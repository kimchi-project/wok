/*
 * Project Wok
 *
 * Copyright IBM Corp, 2015-2017
 *
 * Code derived from Project Kimchi
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
var wok = {

    widget: {},

    /**
     * A wrapper of jQuery.ajax function to allow custom bindings.
     *
     * @param settings an extended object to jQuery Ajax settings object
     *   with some extra properties (see below)
     *
     *   resend: if the XHR has failed due to 401, the XHR can be resent
     *     after user being authenticated successfully by setting resend
     *     to true: settings = {resend: true}. It's useful for switching
     *     pages (Guests, Templates, etc.).
     *       e.g., the user wants to list guests by clicking Guests tab,
     *     but he is told not authorized and a login window will pop up.
     *     After login, the Ajax request for /vms will be resent without
     *     user clicking the tab again.
     *       Default to false.
     */
    requestJSON : function(settings) {
        settings['originalError'] = settings['error'];
        settings['error'] = null;
        settings['wok'] = true;
        settings['complete'] = function(req) {
            wok.session.remainingSessionTime = req.getResponseHeader('Session-Expires-On');
            wok.session.remainingSessionTime = (parseInt(wok.session.remainingSessionTime, 10) * 1000);
            if (!wok.session.flagInTimer) {
                wok.session.refreshExpiringCounter();
                wok.session.expiringCounter();
            } else if(wok.session.remainingSessionTime > wok.session.remaingTimeToShowAlert) {
                wok.session.hideExpiringAlert();
                wok.session.refreshExpiringCounter();
                wok.session.flagInTimer = false;
            }
        };
        return $.ajax(settings);
    },

    /**
     * Get the i18 strings.
     */
    getI18n: function(suc, err, url, sync) {
        wok.requestJSON({
            url : url ? url : 'i18n.json',
            type : 'GET',
            resend: true,
            dataType : 'json',
            async : !sync,
            success : suc,
            error: err
        });
    },

    getPeers: function(suc, err) {
        wok.requestJSON({
            url: 'peers',
            type: 'GET',
            contentType: 'application/json',
            dataType: 'json',
            resend: true,
            success: suc,
            error: err ? err : function(data) {
                wok.message.error(data.responseJSON.reason);
            }
        });
    },

    getNotifications: function (suc, err) {
        wok.requestJSON({
            url: 'notifications',
            type : 'GET',
            headers: {'Wok-Robot': 'wok-robot'},
            dataType : 'json',
            success : suc,
            error: err
        });
    },

    removeNotification: function (id) {
        wok.requestJSON({
            url: 'notifications/' + id,
            type : 'DELETE',
            dataType : 'json',
        });
    },

    login : function(settings, suc, err) {
        $.ajax({
            url : "login",
            type : "POST",
            contentType : "application/json",
            data : JSON.stringify(settings),
            dataType : "json"
        }).done(suc).fail(err);
    },

    logout : function(suc, err) {
        wok.requestJSON({
            url : 'logout',
            type : 'POST',
            contentType : "application/json",
            dataType : "json"
        }).done(suc).fail(err);
    },

    listPlugins : function(suc, err, sync) {
        wok.requestJSON({
            url : 'config/plugins',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            resend: true,
            async : !sync,
            success : suc,
            error : err
        });
    },

    enablePlugin : function(plugin, suc, err) {
        wok.requestJSON({
            url : 'config/plugins/' + encodeURIComponent(plugin) + "/enable",
            type : 'POST',
            contentType : 'application/json',
            dataType : 'json',
            resend: true,
            success : suc,
            error : err
        });
    },

    disablePlugin : function(plugin, suc, err) {
        wok.requestJSON({
            url : 'config/plugins/' + encodeURIComponent(plugin) + "/disable",
            type : 'POST',
            contentType : 'application/json',
            dataType : 'json',
            resend: true,
            success : suc,
            error : err
        });
    },

    getConfig: function(suc, err, sync) {
        wok.requestJSON({
            url : 'config',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            resend: true,
            async : !sync,
            success : suc,
            error : err
        });
    },

    getTasks: function(suc, err) {
        wok.requestJSON({
            url : 'tasks',
            type : 'GET',
            contentType : "application/json",
            dataType : 'json',
            success : suc,
            error : err
        });
    },

    getUserLogs : function(suc, err) {
        wok.requestJSON({
            url : 'logs',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            resend : true,
            success : suc,
            error : err || function(data) {
                wok.message.error(data.responseJSON.reason);
            }
        });
    },

    getFilteredUserLogs : function(suc, err, search) {
        wok.requestJSON({
            url : 'logs?' + search,
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err || function(data) {
                wok.message.error(data.responseJSON.reason);
            }
        });
    },

    downloadLogs : function(suc, err, search) {
        wok.requestJSON({
            url : 'logs?'+search+'download=True',
            type : 'GET',
            contentType : 'application/json',
            dataType : 'json',
            success : suc,
            error : err || function(data) {
                wok.message.error(data.responseJSON.reason);
            }
        });
    }
};
