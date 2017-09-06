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

wok.message = function(msg, level, node, closeable, onclick, alertId) {
    "use strict";
    var close = closeable || true;
    var container = node || $('#alert-fields');
    if($("#" + alertId).length === 0) {
        if ($(container).length < 1) {
            container = $('<div id="alert-fields"/>').appendTo($('#alert-container'));
        }
        var message = '<div '+( alertId ? 'id="'+alertId+'"' : '')+' role="alert" class="alert ' + (level || '') + ' '+( close ? 'alert-dismissible' : '')+' fade in" style="display: none;">';
        if(!node || close) {
            message += '<button type="button" class="close" data-dismiss="alert" aria-label="Close" onclick="' + (onclick || '') + '"><span aria-hidden="true"><i class="fa fa-times-circle"></i></span></button>';
        }
        message += msg;
        message += '</div>';
        var $message = $(message);
        $(container).show();
        $(container).append($message);
        $message.alert();
        $message.fadeIn(100);

        if(!close){
            var timeout = setTimeout(function() {
                $message.delay(4000).fadeOut(100, function() {
                    $message.alert('close');
                    $(this).remove();
                    if ($(container).children().length < 1) {
                        $(container).hide();
                    }
                });
            }, 10000);
        }
    }
};

wok.message.warn = function(msg, node, closeable, alertId) {
    "use strict";
    wok.message(msg, 'alert-warning', node, closeable, null, alertId);
};
wok.message.error = function(msg, node, closeable, alertId) {
    "use strict";
    wok.message(msg, 'alert-danger', node, closeable, null, alertId);
};
wok.message.error.code = function(code, node, closeable, alertId) {
    "use strict";
    var msg = code + ": " + i18n[code];
    wok.message(msg, 'alert-danger', node, closeable, null, alertId);
};
wok.message.success = function(msg, node, closeable, alertId) {
    "use strict";
    wok.message(msg, 'alert-success', node, closeable, null, alertId);
};
wok.message.notify = function(notification, node) {
    "use strict";
    wok.message(notification.message, 'alert-warning', node, true, "wok.removeNotification('" + notification.code + "')");
};
