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
#
import glob
import grp
import inspect
import os
import pwd
import re
import sqlite3
import subprocess
import sys
import traceback
import xml.etree.ElementTree as ET
from datetime import datetime
from datetime import timedelta
from multiprocessing import Process
from multiprocessing import Queue
from optparse import Values
from threading import Timer

import cherrypy
import psutil
from cherrypy.lib.reprconf import Parser
from wok import config
from wok.config import paths
from wok.config import PluginConfig
from wok.config import PluginPaths
from wok.exception import InvalidParameter
from wok.exception import TimeoutExpired
from wok.stringutils import decode_value

wok_log = cherrypy.log.error_log

SI_PREFIXES = ['k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
# The IEC prefixes are the equivalent SI prefixes + 'i'
# but, exceptionally, 'k' becomes 'Ki' instead of 'ki'.
IEC_PREFIXES = ['Ki' if p == 'k' else p + 'i' for p in SI_PREFIXES]
PREFIXES_BY_BASE = {1000: SI_PREFIXES, 1024: IEC_PREFIXES}

SUFFIXES_WITH_MULT = {'b': 1, 'B': 8}
DEFAULT_SUFFIX = 'B'


def is_digit(value):
    if isinstance(value, int):
        return True
    elif isinstance(value, str):
        value = value.strip()
        return value.isdigit()
    else:
        return False


def get_plugin_config_file(name):
    plugin_conf = PluginPaths(name).conf_file
    if not os.path.exists(plugin_conf):
        cherrypy.log.error_log.error(
            f"Plugin configuration file {plugin_conf} doesn't exist."
        )
        return None
    return plugin_conf


def load_plugin_conf(name):
    try:
        plugin_conf = get_plugin_config_file(name)
        if not plugin_conf:
            return None

        return Parser().dict_from_file(plugin_conf)
    except ValueError as e:
        cherrypy.log.error_log.error(
            f'Failed to load plugin conf from {plugin_conf}: {e}'
        )


def get_plugins(enabled_only=False):
    plugin_dir = paths.plugins_dir

    try:
        dir_contents = os.listdir(plugin_dir)
    except OSError:
        return

    test_mode = config.config.get('server', 'test').lower() == 'true'

    for name in dir_contents:
        if os.path.isdir(os.path.join(plugin_dir, name)):
            if name == 'sample' and not test_mode:
                continue

            plugin_config = load_plugin_conf(name)
            if not plugin_config:
                continue
            try:
                if plugin_config['wok']['enable'] is None:
                    continue

                plugin_enabled = plugin_config['wok']['enable']
                if enabled_only and not plugin_enabled:
                    continue

                yield (name, plugin_config)
            except (TypeError, KeyError):
                continue


def get_enabled_plugins():
    return get_plugins(enabled_only=True)


def get_plugin_app_mounted_in_cherrypy(name):
    plugin_uri = '/plugins/' + name
    return cherrypy.tree.apps.get(plugin_uri, None)


def get_plugin_dependencies(name):
    app = get_plugin_app_mounted_in_cherrypy(name)
    if app is None or not hasattr(app.root, 'depends'):
        return []
    return app.root.depends


def get_all_plugins_dependent_on(name):
    if not cherrypy.tree.apps:
        return []

    dependencies = []
    for plugin, app in cherrypy.tree.apps.items():
        if hasattr(app.root, 'depends') and name in app.root.depends:
            dependencies.append(plugin.replace('/plugins/', ''))

    return dependencies


def get_all_affected_plugins_by_plugin(name):
    dependencies = get_all_plugins_dependent_on(name)
    if len(dependencies) == 0:
        return []

    all_affected_plugins = dependencies
    for dep in dependencies:
        all_affected_plugins += get_all_affected_plugins_by_plugin(dep)

    return all_affected_plugins


def disable_plugin(name):
    plugin_deps = get_all_affected_plugins_by_plugin(name)

    for dep in set(plugin_deps):
        update_plugin_config_file(dep, False)
        update_cherrypy_mounted_tree(dep, False)

    update_plugin_config_file(name, False)
    update_cherrypy_mounted_tree(name, False)


def enable_plugin(name):
    update_plugin_config_file(name, True)
    update_cherrypy_mounted_tree(name, True)

    plugin_deps = get_plugin_dependencies(name)

    for dep in set(plugin_deps):
        enable_plugin(dep)


def set_plugin_state(name, state):
    if state is False:
        disable_plugin(name)
    else:
        enable_plugin(name)


def update_plugin_config_file(name, state):
    plugin_conf = get_plugin_config_file(name)
    if not plugin_conf:
        return

    with open(plugin_conf, 'r') as f:
        config_contents = f.readlines()

    wok_section_found = False

    pattern = re.compile('^\\s*enable\\s*=\\s*')

    for i in range(0, len(config_contents)):
        if config_contents[i] == '[wok]\n':
            wok_section_found = True
            continue

        if pattern.match(config_contents[i]) and wok_section_found:
            config_contents[i] = f'enable = {str(state)}\n'
            break

    with open(plugin_conf, 'w') as f:
        f.writelines(config_contents)


def load_plugin(plugin_name, plugin_config):
    try:
        class_name = f'{plugin_name[0].upper() + plugin_name[1:]}'
        plugin_class = f'wok.plugins.{plugin_name}.{class_name}'
        del plugin_config['wok']
        plugin_config.update(PluginConfig(plugin_name))
    except KeyError:
        return

    try:
        options = get_plugin_config_options()
        plugin_app = import_class(plugin_class)(options)
    except (ImportError, Exception) as e:
        cherrypy.log.error_log.error(
            f'Failed to import plugin {plugin_class}, error: {str(e)}'
        )
        return

    # dynamically extend plugin config with custom data, if provided
    get_custom_conf = getattr(plugin_app, 'get_custom_conf', None)
    if get_custom_conf is not None:
        plugin_config.update(get_custom_conf())

    # dynamically add tools.wokauth.on = True to extra plugin APIs
    try:
        sub_nodes = import_class(
            f'wok.plugins.{plugin_name}.control.sub_nodes')

        urlSubNodes = {}
        for ident, node in sub_nodes.items():
            if node.url_auth:
                ident = f'/{ident}'
                urlSubNodes[ident] = {'tools.wokauth.on': True}

            plugin_config.update(urlSubNodes)

    except ImportError as e:
        msg = f'Failed to import subnodes for plugin {plugin_class}'
        msg += f'Error: {str(e)}'
        cherrypy.log.error_log.error(msg)

    cherrypy.tree.mount(
        plugin_app, config.get_base_plugin_uri(plugin_name), plugin_config
    )


def is_plugin_mounted_in_cherrypy(plugin_uri):
    return cherrypy.tree.apps.get(plugin_uri) is not None


def update_cherrypy_mounted_tree(plugin, state):
    plugin_uri = '/plugin/' + plugin

    if state is False and is_plugin_mounted_in_cherrypy(plugin_uri):
        del cherrypy.tree.apps[plugin_uri]

    if state is True and not is_plugin_mounted_in_cherrypy(plugin_uri):
        plugin_config = load_plugin_conf(plugin)
        load_plugin(plugin, plugin_config)


def get_plugin_config_options():
    options = Values()

    options.websockets_port = config.config.getint('server', 'websockets_port')
    options.cherrypy_port = config.config.getint('server', 'cherrypy_port')
    options.proxy_port = config.config.getint('server', 'proxy_port')
    options.session_timeout = config.config.getint('server', 'session_timeout')

    options.test = config.config.get('server', 'test')
    if options.test == 'None':
        options.test = None

    options.environment = config.config.get('server', 'environment')
    options.server_root = config.config.get('server', 'server_root')
    options.max_body_size = config.config.get('server', 'max_body_size')

    options.log_dir = config.config.get('logging', 'log_dir')
    options.log_level = config.config.get('logging', 'log_level')

    return options


def get_all_tabs():
    files = [os.path.join(paths.ui_dir, 'config/tab-ext.xml')]

    for plugin, _ in get_enabled_plugins():
        files.append(os.path.join(PluginPaths(
            plugin).ui_dir, 'config/tab-ext.xml'))

    tabs = []
    for f in files:
        try:
            root = ET.parse(f)
        except (IOError):
            wok_log.debug(f'Unable to load {f}')
            continue
        tabs.extend([t.text.lower() for t in root.getiterator('title')])

    return tabs


def import_class(class_path):
    module_name, class_name = class_path.rsplit('.', 1)
    try:
        mod = import_module(module_name, class_name)
        return getattr(mod, class_name)
    except (ImportError, AttributeError) as e:
        raise ImportError(
            f'Class {class_path} can not be imported, error: {str(e)}')


def import_module(module_name, class_name=''):
    return __import__(module_name, globals(), locals(), [class_name])


def _set_timer(proc, timeout, timeout_flag):
    # subprocess.kill() can leave descendants running
    # and halting the execution. Using psutil to
    # get all descendants from the subprocess and
    # kill them recursively.
    def kill_proc(proc, timeout_flag):
        try:
            parent = psutil.Process(proc.pid)
            for child in parent.get_children(recursive=True):
                child.kill()
            # kill the process after no children is left
            proc.kill()
        except OSError:
            pass
        else:
            timeout_flag[0] = True

    timer = Timer(timeout, kill_proc, [proc, timeout_flag])
    timer.setDaemon(True)
    timer.start()

    return timer


def _get_cmd_output(proc, out_cb):
    output = []
    while True:
        line = ''
        try:
            line = proc.stdout.readline()
            line = line.decode('utf_8')
        except Exception:
            type, e, tb = sys.exc_info()
            wok_log.error(e)
            msg = f'The output of the command could not be decoded as utf-8.'
            msg += f'\nIgnored line: {repr(line)}'
            wok_log.error(msg)
            pass

        output.append(line)
        if not line:
            break
        out_cb(''.join(output))

    return output


def run_command(cmd, timeout=None, silent=False, out_cb=None, env_vars=None):
    """
    cmd is a sequence of command arguments.
    timeout is a float number in seconds.
    timeout default value is None, means command run without timeout.
    silent is bool, it will log errors using debug handler not error.
    silent default value is False.
    out_cb is a callback that receives the whole command output every time a
    new line is thrown by command. Default value is None, meaning that whole
    output will be returned at the end of execution.

    Returns a tuple (out, error, returncode) where:
    out is the output thrown by command
    error is an error message if applicable
    returncode is an integer equal to the result of command execution
    """
    proc = None
    timer = None
    timeout_flag = [False]

    if env_vars is None:
        env_vars = os.environ.copy()
        env_vars['LC_ALL'] = 'en_US.UTF-8'
    elif env_vars.get('LC_ALL') is None:
        env_vars['LC_ALL'] = 'en_US.UTF-8'

    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env_vars
        )
        if timeout is not None:
            timer = _set_timer(proc, timeout, timeout_flag)

        wok_log.debug(f"Run command: {' '.join(cmd)}")
        if out_cb is not None:
            output = _get_cmd_output(proc, out_cb)
            out = ''.join(output)
            error = proc.stderr.read()
            returncode = proc.poll()
        else:
            out, error = proc.communicate()
            returncode = proc.returncode

        if out:
            wok_log.debug(f'out:\n{out}')

        if returncode != 0:
            msg = (
                f'rc: {returncode} error: {decode_value(error)} returned '
                f"from cmd: {decode_value(' '.join(cmd))}"
            )

            if silent:
                wok_log.debug(msg)

            else:
                wok_log.error(msg)
                if out_cb is not None:
                    out_cb(msg)
        elif error:
            wok_log.debug(
                f'error: {decode_value(error)} returned from cmd: '
                f"{decode_value(' '.join(cmd))}"
            )

        if timeout_flag[0]:
            msg = (
                f'subprocess is killed by signal.SIGKILL for '
                f'timeout {timeout} seconds'
            )
            wok_log.error(msg)

            msg_args = {'cmd': ' '.join(cmd), 'seconds': str(timeout)}
            raise TimeoutExpired('WOKUTILS0002E', msg_args)

        return out.decode('utf-8'), error, returncode
    except TimeoutExpired:
        raise
    except OSError as e:
        msg = f"Impossible to execute {' '.join(cmd)}"
        wok_log.debug(msg)

        return None, f'{msg} {e}', -1
    except Exception as e:
        msg = f"Failed to run command: {b' '.join(cmd)}."
        msg = msg if proc is None else msg + f'\n  error code: {e}.'
        wok_log.error(msg)

        if proc:
            return out.decode('utf-8'), error, proc.returncode
        else:
            return None, msg, -1
    finally:
        if timer and not timeout_flag[0]:
            timer.cancel()


def parse_cmd_output(output, output_items):
    res = []
    for line in output.split('\n'):
        if line:
            res.append(dict(zip(output_items, line.split())))
    return res


def patch_find_nfs_target(nfs_server):
    cmd = ['showmount', '--no-headers', '--exports', nfs_server]
    try:
        out = run_command(cmd, 10)[0]
    except TimeoutExpired:
        msg = f'server {nfs_server} query timeout.'
        msg += ' may not have any path exported'
        wok_log.warning(msg)
        return list()

    targets = parse_cmd_output(out, output_items=['target'])
    for target in targets:
        target['type'] = 'nfs'
        target['host_name'] = nfs_server
    return targets


def list_path_modules(path):
    modules = set()
    for f in os.listdir(path):
        base, ext = os.path.splitext(f)
        if ext in ('.py', '.pyc', '.pyo'):
            modules.add(base)
    return sorted(modules)


def get_model_instances(module_name):
    instances = []
    module = import_module(module_name)
    members = inspect.getmembers(module, inspect.isclass)
    for cls_name, instance in members:
        if inspect.getmodule(instance) == module and \
                cls_name.endswith('Model'):
            instances.append(instance)
    return instances


def get_all_model_instances(root_model_name, root_model_file, kwargs):
    """Function that returns all model instances from all modules
    found on the same dir as root_model_name module.

    The intended use of this function is to be called from a root
    model class that subclasses BaseModel to get all model instances
    contained in its dir. This module array would then be used in
    the super init call of BaseModel.

    The root model itself is ignored in the return array.

    Args:
        root_model_name (str): the python name of the root module. For
            example, in WoK case it would be 'wok.model.model'. This
            value can be retrieved by calling '__name__' inside the root
            model file.

        root_model_file (str): the absolute file name of the root model.
            This can be retrived by calling '__file__' in the root model
            file.

        kwargs (dict): keyword arguments to be used to initiate the
            models found. For example, {'objstore': ...}

    Returns:
        array: an array with all module instances found, excluding the
            root module itself.

    """
    models = []

    root_model = os.path.basename(root_model_file)
    ignore_mod = os.path.splitext(root_model)[0]

    package_namespace = root_model_name.rsplit('.', 1)[0]

    for mod_name in list_path_modules(os.path.dirname(root_model_file)):
        if mod_name.startswith('_') or mod_name == ignore_mod:
            continue

        instances = get_model_instances(package_namespace + '.' + mod_name)
        for instance in instances:
            try:
                models.append(instance(**kwargs))
            except TypeError:
                models.append(instance())

    return models


def run_setfacl_set_attr(path, attr='r', user=''):
    set_user = ['setfacl', '--modify', f'user:{user}:{attr}', path]
    out, error, ret = run_command(set_user)
    return ret == 0


def probe_file_permission_as_user(file, user):
    def probe_permission(q, file, user):
        uid = pwd.getpwnam(user).pw_uid
        gid = pwd.getpwnam(user).pw_gid
        gids = [g.gr_gid for g in grp.getgrall() if user in g.gr_mem]
        os.setgid(gid)
        os.setgroups(gids)
        os.setuid(uid)
        try:
            with open(file):
                q.put((True, None))
        except Exception as e:
            wok_log.debug(traceback.format_exc())
            q.put((False, e))

    queue = Queue()
    p = Process(target=probe_permission, args=(queue, file, user))
    p.start()
    p.join()
    return queue.get()


def remove_old_files(globexpr, hours):
    """
    Delete files matching globexpr that are older than specified hours.
    """
    minTime = datetime.now() - timedelta(hours=hours)

    try:
        for f in glob.glob(globexpr):
            timestamp = os.path.getmtime(f)
            fileTime = datetime.fromtimestamp(timestamp)

            if fileTime < minTime:
                os.remove(f)
    except (IOError, OSError) as e:
        wok_log.error(str(e))


def get_unique_file_name(all_names, name):
    """Find the next available, unique name for a file.

    If a file named "<name>" isn't found in "<all_names>", use that same
    "<name>".  There's no need to generate a new name in that case.

    If any file named "<name> (<number>)" is found in "all_names", use the
    maximum "number" + 1; else, use 1.

    Arguments:
    all_names -- All existing file names. This list will be used to make sure
        the new name won't conflict with existing names.
    name -- The name of the original file.

    Return:
    A string in the format "<name> (<number>)", or "<name>".
    """
    if name not in all_names:
        return name

    re_group_num = 'num'

    re_expr = f'{name} \\((?P<{re_group_num}>\\d+)\\)'

    max_num = 0
    re_compiled = re.compile(re_expr)

    for n in all_names:
        match = re_compiled.match(n)
        if match is not None:
            max_num = max(max_num, int(match.group(re_group_num)))

    return f'{name} ({max_num + 1})'


def servermethod(f):
    def wrapper(*args, **kwargs):
        server_state = str(cherrypy.engine.state)
        if server_state not in ['states.STARTED', 'states.STARTING']:
            return False
        return f(*args, **kwargs)

    return wrapper


def _validate_convert_data(value, from_unit, to_unit):
    if not from_unit:
        raise InvalidParameter('WOKUTILS0005E', {'unit': from_unit})
    if not to_unit:
        raise InvalidParameter('WOKUTILS0005E', {'unit': to_unit})

    # set the default suffix
    if from_unit[-1] not in SUFFIXES_WITH_MULT:
        from_unit += DEFAULT_SUFFIX
    if to_unit[-1] not in SUFFIXES_WITH_MULT:
        to_unit += DEFAULT_SUFFIX

    # split prefix and suffix for better parsing
    from_p = from_unit[:-1]
    from_s = from_unit[-1]
    to_p = to_unit[:-1]
    to_s = to_unit[-1]

    # validate parameters
    try:
        value = float(value)
    except TypeError:
        raise InvalidParameter('WOKUTILS0004E', {'value': value})
    if from_p != '' and from_p not in (SI_PREFIXES + IEC_PREFIXES):
        raise InvalidParameter('WOKUTILS0005E', {'unit': from_unit})
    if from_s not in SUFFIXES_WITH_MULT:
        raise InvalidParameter('WOKUTILS0005E', {'unit': from_unit})
    if to_p != '' and to_p not in (SI_PREFIXES + IEC_PREFIXES):
        raise InvalidParameter('WOKUTILS0005E', {'unit': to_unit})
    if to_s not in SUFFIXES_WITH_MULT:
        raise InvalidParameter('WOKUTILS0005E', {'unit': to_unit})

    return value, from_unit, to_unit


def convert_data_size(value, from_unit, to_unit='B'):
    """Convert a data value from one unit to another unit
    (e.g. 'MiB' -> 'GiB').

    The data units supported by this function are made up of one prefix and one
    suffix. The valid prefixes are those defined in the SI (i.e. metric system)
    and those defined by the IEC, and the valid suffixes indicate if the base
    unit is bit or byte.
    Take a look at the tables below for the possible values:

    Prefixes:

    ==================================     ===================================
    PREFIX (SI) | DESCRIPTION | VALUE      PREFIX (IEC) | DESCRIPTION | VALUE
    ==================================     ===================================
    k           | kilo        | 1000       Ki           | kibi        | 1024
    ----------------------------------     -----------------------------------
    M           | mega        | 1000^2     Mi           | mebi        | 1024^2
    ----------------------------------     -----------------------------------
    G           | giga        | 1000^3     Gi           | gibi        | 1024^3
    ----------------------------------     -----------------------------------
    T           | tera        | 1000^4     Ti           | tebi        | 1024^4
    ----------------------------------     -----------------------------------
    P           | peta        | 1000^5     Pi           | pebi        | 1024^5
    ----------------------------------     -----------------------------------
    E           | exa         | 1000^6     Ei           | exbi        | 1024^6
    ----------------------------------     -----------------------------------
    Z           | zetta       | 1000^7     Zi           | zebi        | 1024^7
    ----------------------------------     -----------------------------------
    Y           | yotta       | 1000^8     Yi           | yobi        | 1024^8
    ==================================     ===================================

    Suffixes:

    =======================
    SUFFIX | DESCRIPTION
    =======================
    b      | bit
    -----------------------
    B      | byte (default)
    =======================

    See http://en.wikipedia.org/wiki/Binary_prefix for more details on
    those units.

    If a wrong unit is provided, an error will be raised.

    Examples:
        convert_data_size(5, 'MiB', 'KiB') -> 5120.0
        convert_data_size(5, 'MiB', 'M')   -> 5.24288
        convert_data_size(5, 'MiB', 'GiB') -> 0.0048828125
        convert_data_size(5, 'MiB', 'Tb')  -> 4.194304e-05
        convert_data_size(5, 'MiB')        -> 5242880.0
        convert_data_size(5, 'mib')        -> #ERROR# (invalid from_unit)

    Parameters:
    value -- the value to be converted, in the unit specified by 'from_unit'.
             this parameter can be of any type which can be cast to float
             (e.g. int, float, str).
    from_unit -- the unit of 'value', as described above.
    to_unit -- the unit of the return value, as described above.

    Return:
    A float number representing 'value' (in 'from_unit') converted
    to 'to_unit'.
    """

    value, from_unit, to_unit = _validate_convert_data(
        value, from_unit, to_unit)
    # if the units are the same, return the input value
    if from_unit == to_unit:
        return value

    # split prefix and suffix for better parsing
    from_p = from_unit[:-1]
    from_s = from_unit[-1]
    to_p = to_unit[:-1]
    to_s = to_unit[-1]

    # convert 'value' to the most basic unit (bits)...
    bits = value

    for suffix, mult in SUFFIXES_WITH_MULT.items():
        if from_s == suffix:
            bits *= mult
            break

    if from_p != '':
        for base, prefixes in PREFIXES_BY_BASE.items():
            for i, p in enumerate(prefixes):
                if from_p == p:
                    bits *= base ** (i + 1)
                    break

    # ...then convert the value in bits to the destination unit
    ret = bits

    for suffix, mult in SUFFIXES_WITH_MULT.items():
        if to_s == suffix:
            ret /= float(mult)
            break

    if to_p != '':
        for base, prefixes in PREFIXES_BY_BASE.items():
            for i, p in enumerate(prefixes):
                if to_p == p:
                    ret /= float(base) ** (i + 1)
                    break

    return ret


def get_objectstore_fields(objstore=None):
    """
        Return a list with all fields from the objectstore.
    """
    if objstore is None:
        wok_log.error('No objectstore set up.')
        return None
    conn = sqlite3.connect(objstore, timeout=10)
    cursor = conn.cursor()
    schema_fields = []
    sql = "PRAGMA table_info('objects')"
    cursor.execute(sql)
    for row in cursor.fetchall():
        schema_fields.append(row[1])
    return schema_fields


def upgrade_objectstore_schema(objstore=None, field=None):
    """
        Add a new column (of type TEXT) in the objectstore schema.
    """
    if (field or objstore) is None:
        wok_log.error('Cannot upgrade objectstore schema.')
        return False

    if field in get_objectstore_fields(objstore):
        # field already exists in objectstore schema. Nothing to do.
        return False
    try:
        conn = sqlite3.connect(objstore, timeout=10)
        cursor = conn.cursor()
        sql = f'ALTER TABLE objects ADD COLUMN {field} TEXT'
        cursor.execute(sql)
        wok_log.info(f'Objectstore schema sucessfully upgraded: {objstore}')
        conn.close()
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            conn.close()
        wok_log.error(f'Cannot upgrade objectstore schema: {e.args[0]}')
        return False
    return True
