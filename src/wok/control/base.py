# -*- coding: utf-8 -*-
#
# Project Wok
#
# Copyright IBM Corp, 2015-2017
#
# Code derived from Project Kimchi
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA
import re
import urllib.parse

import cherrypy
import wok.template
from wok.asynctask import save_request_log_id
from wok.auth import USER_GROUPS
from wok.auth import USER_NAME
from wok.auth import USER_ROLE
from wok.auth import wokauth
from wok.control.utils import get_class_name
from wok.control.utils import internal_redirect
from wok.control.utils import model_fn
from wok.control.utils import parse_request
from wok.control.utils import validate_method
from wok.control.utils import validate_params
from wok.exception import InvalidOperation
from wok.exception import UnauthorizedError
from wok.exception import WokException
from wok.reqlogger import log_request
from wok.stringutils import encode_value
from wok.stringutils import utf8_dict
from wok.utils import wok_log

# Default request log messages
COLLECTION_DEFAULT_LOG = 'WOKCOL0001L'
RESOURCE_DEFAULT_LOG = 'WOKRES0001L'

LOG_DISABLED_METHODS = ['GET']


class Resource(object):
    """
    A Resource represents a single entity in the API (such as a Virtual
    Machine)

    To create new Resource types, subclass this and change the following things
    in the child class:

    - If the Resource requires more than one identifier set self.model_args as
      appropriate.  This should only be necessary if this Resource is logically
      nested.  For example: A Storage Volume belongs to a Storage Pool so the
      Storage Volume would set model args to (pool_ident, volume_ident).

    - Implement the base operations of 'lookup' and 'delete' in the model(s).

    - Set the 'data' property to a JSON-serializable representation of the
      Resource.
    """

    def __init__(self, model, ident=None):
        self.uri_fmt = ''
        self.info = {}
        self.model = model
        self.ident = ident.decode(
            'utf-8') if isinstance(ident, bytes) else ident
        self.model_args = (self.ident,)
        self.admin_methods = []
        self.log_map = {}
        self.log_args = {'ident': self.ident if self.ident else ''}

    def _redirect(self, action_result, code=303):
        uri_params = []
        if isinstance(action_result, list):
            for arg in action_result:
                if arg is None:
                    arg = ''
                uri_params.append(urllib.parse.quote(arg, safe=''))
        elif action_result is not None and action_result != self.ident:
            uri_params = list(self.model_args[:-1])
            uri_params += [urllib.parse.quote(action_result, safe='')]

        if uri_params:
            base_uri = cherrypy.request.app.script_name + self.uri_fmt
            raise cherrypy.HTTPRedirect(base_uri % tuple(uri_params), code)

    def generate_action_handler(
        self, action_name, action_args=None, destructive=False, protected=None
    ):
        def _render_element(self, ident):
            self._redirect(ident)
            uri_params = []
            for arg in self.model_args:
                if arg is None:
                    arg = ''
                uri_params.append(urllib.parse.quote(arg, safe=''))
            raise internal_redirect(self.uri_fmt % tuple(uri_params))

        return self._generate_action_handler_base(
            action_name,
            _render_element,
            destructive=destructive,
            action_args=action_args,
            protected=protected,
        )

    def generate_action_handler_task(self, action_name, action_args=None):
        def _render_task(self, task):
            cherrypy.response.status = 202
            return wok.template.render('Task', task)

        return self._generate_action_handler_base(
            action_name, _render_task, action_args=action_args
        )

    def _generate_action_handler_base(
        self,
        action_name,
        render_fn,
        destructive=False,
        action_args=None,
        protected=None,
    ):
        def wrapper(*args, **kwargs):
            # status must be always set in order to request be logged.
            # use 500 as fallback for "exception not handled" cases.
            if protected is not None and protected:
                wokauth()

            details = None
            status = 500

            method = 'POST'
            validate_method(method, self.admin_methods)
            try:
                request = parse_request()
                validate_params(request, self, action_name)
                self.lookup()
                if not self.is_authorized():
                    raise UnauthorizedError('WOKAPI0009E')

                model_args = list(self.model_args)
                if action_args is not None:
                    model_args.extend(
                        request[key] if key in request.keys() else None
                        for key in action_args
                    )

                action_fn = getattr(self.model, model_fn(self, action_name))
                action_result = action_fn(*model_args)
                status = 200

                if destructive is False or (
                    'persistent' in self.info.keys(
                    ) and self.info['persistent'] is True
                ):
                    result = render_fn(self, action_result)
                    status = cherrypy.response.status

                    return result
            except WokException as e:
                details = e
                status = e.getHttpStatusCode()
                raise cherrypy.HTTPError(status, str(e))
            finally:
                # log request
                code = self.getRequestMessage(method, action_name)
                reqParams = utf8_dict(self.log_args, request)
                log_id = log_request(
                    code,
                    reqParams,
                    details,
                    method,
                    status,
                    class_name=get_class_name(self),
                    action_name=action_name,
                )
                if status == 202:
                    save_request_log_id(log_id, action_result['id'])

        wrapper.__name__ = action_name
        wrapper.exposed = True
        return wrapper

    def lookup(self):
        try:
            lookup = getattr(self.model, model_fn(self, 'lookup'))
            self.info = lookup(*self.model_args)
        except AttributeError:
            self.info = {}

    def delete(self):
        try:
            fn = getattr(self.model, model_fn(self, 'delete'))
            fn(*self.model_args)
            cherrypy.response.status = 204
        except AttributeError:
            e = InvalidOperation(
                'WOKAPI0002E', {'resource': get_class_name(self)})
            raise cherrypy.HTTPError(405, str(e))

    @cherrypy.expose
    def index(self, *args, **kargs):
        # status must be always set in order to request be logged.
        # use 500 as fallback for "exception not handled" cases.
        details = None
        status = 500

        method = validate_method(('GET', 'DELETE', 'PUT'), self.admin_methods)

        try:
            self.lookup()
            if not self.is_authorized():
                raise UnauthorizedError('WOKAPI0009E')

            result = {
                'GET': self.get,
                'DELETE': self.delete,
                'PUT': self.update
            }[method](*args, **kargs)

            status = cherrypy.response.status
        except WokException as e:
            details = e
            status = e.getHttpStatusCode()
            raise cherrypy.HTTPError(status, str(e))
        except cherrypy.HTTPError as e:
            status = e.status
            raise
        finally:
            # log request
            if method not in LOG_DISABLED_METHODS and status != 202:
                code = self.getRequestMessage(method)
                log_request(
                    code,
                    self.log_args,
                    details,
                    method,
                    status,
                    class_name=get_class_name(self),
                )

        return result

    def is_authorized(self):
        user_name = cherrypy.session.get(USER_NAME, '')
        user_groups = cherrypy.session.get(USER_GROUPS, [])
        user_role = cherrypy.session.get(USER_ROLE, None)

        users = self.data.get('users', None)
        groups = self.data.get('groups', None)

        if (users is None and groups is None) or user_role == 'admin':
            return True

        return user_name in users or len(set(user_groups) & set(groups)) > 0

    def update(self, *args, **kargs):
        params = parse_request()

        try:
            update = getattr(self.model, model_fn(self, 'update'))
        except AttributeError:
            e = InvalidOperation(
                'WOKAPI0003E', {'resource': get_class_name(self)})
            raise cherrypy.HTTPError(405, str(e))

        validate_params(params, self, 'update')

        args = list(self.model_args) + [params]
        ident = update(*args)
        self._redirect(ident)
        cherrypy.response.status = 200
        self.lookup()
        return self.get()

    def get(self):
        return wok.template.render(get_class_name(self), self.data)

    def getRequestMessage(self, method, action='default'):
        """
        Provide customized user activity log message in inherited classes
        through log_map attribute.
        """
        return self.log_map.get(method, {}).get(action, RESOURCE_DEFAULT_LOG)

    @property
    def data(self):
        """
        Override this in inherited classes to provide the Resource
        representation as a python dictionary.
        """
        return {}


class AsyncResource(Resource):
    """
    AsyncResource is a specialized Resource to handle async task.
    """

    def __init__(self, model, ident=None):
        super(AsyncResource, self).__init__(model, ident)

    def lookup(self):
        try:
            lookup = getattr(self.model, model_fn(self, 'lookup'))
            self.info = lookup(*self.model_args)
        except AttributeError:
            self.info = {}

        cherrypy.response.status = 202
        return wok.template.render('Task', self.info)

    def delete(self):
        try:
            fn = getattr(self.model, model_fn(self, 'delete'))
            task = fn(*self.model_args)
        except AttributeError:
            e = InvalidOperation(
                'WOKAPI0002E', {'resource': get_class_name(self)})
            raise cherrypy.HTTPError(405, str(e))

        cherrypy.response.status = 202

        # log request
        method = 'DELETE'
        code = self.getRequestMessage(method)
        reqParams = utf8_dict(self.log_args)
        log_id = log_request(
            code,
            reqParams,
            None,
            method,
            cherrypy.response.status,
            class_name=get_class_name(self),
        )
        save_request_log_id(log_id, task['id'])

        return wok.template.render('Task', task)


class Collection(object):
    """
    A Collection is a container for Resource objects.  To create a new
    Collection type, subclass this and make the following changes to the child
    class:

    - Set self.resource to the type of Resource that this Collection contains

    - Set self.resource_args.  This can remain an empty list if the Resources
      can be initialized with only one identifier.  Otherwise, include
      additional values as needed (eg. to identify a parent resource).

    - Set self.model_args.  Similar to above, this is needed only if the model
      needs additional information to identify this Collection.

    - Implement the base operations of 'create' and 'get_list' in the model.
    """

    def __init__(self, model):
        self.model = model
        self.resource = Resource
        self.resource_args = []
        self.model_args = []
        self.admin_methods = []
        self.log_map = {}
        self.log_args = {}

    def create(self, params, *args):
        try:
            create = getattr(self.model, model_fn(self, 'create'))
        except AttributeError:
            e = InvalidOperation(
                'WOKAPI0005E', {'resource': get_class_name(self)})
            raise cherrypy.HTTPError(405, str(e))

        validate_params(params, self, 'create')
        args = self.model_args + [params]
        name = create(*args)
        cherrypy.response.status = 201
        args = self.resource_args + [name]
        res = self.resource(self.model, *args)
        res.lookup()
        return res.get()

    def _get_resources(self, flag_filter):
        try:
            get_list = getattr(self.model, model_fn(self, 'get_list'))
            idents = get_list(*self.model_args, **flag_filter)
            res_list = []
            for ident in idents:
                # internal text, get_list changes ident to unicode for sorted
                args = self.resource_args + [ident]
                res = self.resource(self.model, *args)
                try:
                    res.lookup()
                except Exception as e:
                    # In case of errors when fetching a resource info, pass and
                    # log the error, so, other resources are returned
                    # Encoding error message as ident is also encoded value.
                    # This has to be done to avoid unicode error,
                    # as combination of encoded and unicode value results into
                    # unicode error.
                    wok_log.error(
                        f"Problem in lookup of resource '{ident}'. "
                        f'Detail: {encode_value(str(e))}'
                    )
                    continue
                res_list.append(res)
            return res_list
        except AttributeError:
            return []

    def _cp_dispatch(self, vpath):
        if vpath:
            ident = vpath.pop(0)
            ident = urllib.parse.unquote(ident)
            # incoming text, from URL, is not unicode, need encode
            args = self.resource_args + [ident]
            return self.resource(self.model, *args)

    def filter_data(self, resources, fields_filter):
        data = []
        for res in resources:
            if not res.is_authorized():
                continue

            if all(
                key in res.data and
                (
                    res.data[key] == val or
                    re.match(str(val), res.data[key]) or
                    (isinstance(val, list) and res.data[key] in val)
                )
                for key, val in fields_filter.items()
            ):
                data.append(res.data)
        return data

    def get(self, filter_params):
        def _split_filter(params):
            flag_filter = dict()
            fields_filter = dict(params)
            for key, val in params.items():
                if key.startswith('_'):
                    flag_filter[key] = fields_filter.pop(key)
            return flag_filter, fields_filter

        flag_filter, fields_filter = _split_filter(filter_params)
        resources = self._get_resources(flag_filter)
        data = self.filter_data(resources, fields_filter)
        return wok.template.render(get_class_name(self), data)

    def getRequestMessage(self, method):
        """
        Provide customized user activity log message in inherited classes
        through log_map attribute.
        """
        log = self.log_map.get(method, {})
        return log.get('default', COLLECTION_DEFAULT_LOG)

    @cherrypy.expose
    def index(self, *args, **kwargs):
        # status must be always set in order to request be logged.
        # use 500 as fallback for "exception not handled" cases.
        details = None
        status = 500

        params = {}
        method = validate_method(('GET', 'POST'), self.admin_methods)

        try:
            if method == 'GET':
                params = cherrypy.request.params
                validate_params(params, self, 'get_list')
                return self.get(params)
            elif method == 'POST':
                params = parse_request()
                result = self.create(params, *args)
                status = cherrypy.response.status
                return result
        except WokException as e:
            details = e
            status = e.getHttpStatusCode()
            raise cherrypy.HTTPError(status, str(e))
        except cherrypy.HTTPError as e:
            status = e.status
            raise
        finally:
            if method not in LOG_DISABLED_METHODS and status != 202:
                # log request
                code = self.getRequestMessage(method)
                reqParams = utf8_dict(self.log_args, params)
                log_request(
                    code,
                    reqParams,
                    details,
                    method,
                    status,
                    class_name=get_class_name(self),
                )


class AsyncCollection(Collection):
    """
    A Collection to create it's resource by asynchronous task
    """

    def __init__(self, model):
        super(AsyncCollection, self).__init__(model)

    def create(self, params, *args):
        try:
            create = getattr(self.model, model_fn(self, 'create'))
        except AttributeError:
            e = InvalidOperation(
                'WOKAPI0005E', {'resource': get_class_name(self)})
            raise cherrypy.HTTPError(405, str(e))

        validate_params(params, self, 'create')
        args = self.model_args + [params]
        task = create(*args)
        cherrypy.response.status = 202

        # log request
        method = 'POST'
        code = self.getRequestMessage(method)
        reqParams = utf8_dict(self.log_args, params)
        log_id = log_request(
            code,
            reqParams,
            None,
            method,
            cherrypy.response.status,
            class_name=get_class_name(self),
        )
        save_request_log_id(log_id, task['id'])

        return wok.template.render('Task', task)


class SimpleCollection(Collection):
    """
    A Collection without Resource definition
    """

    def __init__(self, model):
        super(SimpleCollection, self).__init__(model)

    def get(self, filter_params):
        res_list = []
        try:
            get_list = getattr(self.model, model_fn(self, 'get_list'))
            res_list = get_list(*self.model_args)
        except AttributeError:
            pass
        return wok.template.render(get_class_name(self), res_list)
