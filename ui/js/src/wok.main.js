/*
 * Project Wok
 *
 * Copyright IBM Corp, 2015-2016
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

wok.NOTIFICATION_INTERVAL = 2000
wok.tabMode = {};

wok.config = undefined;
wok.getConfig(function(result) {
    wok.config = result;
}, function() {
    wok.config = {};
});

wok.main = function() {
    wok.isLoggingOut = false;
    wok.popable();

    var genTabs = function(tabs) {
        var functionalTabs = [];
        var tabsHtml = [];
        $(tabs).each(function(i, tab) {
            tab_i18n = i18n[tab] ? i18n[tab] : tab;
            var functionality = tab['functionality'];
            var title = tab['title'];
            var path = tab['path'];
            var mode = tab['mode'];
            if (mode != 'none') {
                var helpPath = wok.checkHelpFile(path);
                var disableHelp = (helpPath.length == 0 ? "disableHelp" : helpPath);
                tabsHtml.push(
                    '<li class="', functionality.toLowerCase() + 'Tab', '">',
                        '<a class="item ', disableHelp, '" href="', path, '">',
                            title,
                        '</a>',
                        '<input name="funcTab" class="sr-only" value="' + functionality.toLowerCase() + '" type="hidden"/>',
                        '<input name="helpPath" class="sr-only" value="' + helpPath + '" type="hidden"/>',
                        '<input name="colorTab1" class="sr-only" value="' + tab['colorTab1'] + '" type="hidden"/>',
                        '<input name="colorTab2" class="sr-only" value="' + tab['colorTab2'] + '" type="hidden"/>',
                    '</li>'
                );

                if (functionalTabs.indexOf(functionality) == -1) {
                    functionalTabs.push(functionality)
                }
            }
        });

        $('#functionalTabPanel ul').append(genFuncTabs(functionalTabs));
        $('#tabPanel ul').append(tabsHtml.join(''));
        return;
    };

    var genFuncTabs  = function(tabs){
        var functionalTabHtml = [];
        $(tabs).each(function(i, tab_i18n) {
            functionalTabHtml.push(
                '<li>',
                    '<a class="item',' ',tab_i18n.toLowerCase(),'Tab','" href="#">',
                        tab_i18n,
                    '</a>',
                '</li>'
            );
        });
        return functionalTabHtml.join('');
    };

    var parseTabs = function(xmlData) {
        var tabs = [];
        var funcNode = $(xmlData).find('functionality');
        var functionality = funcNode.text();
        var colorTab1 = funcNode.attr('colorTab1');
        var colorTab2 = funcNode.attr('colorTab2');
        wok.pluginsColor[plugin] = colorTab2;
        $(xmlData).find('tab').each(function() {
            var tab = $(this);
            var titleKey = tab.find('title').text();
            var title = i18n[titleKey] ? i18n[titleKey] : titleKey;
            var path = tab.find('path').text();
            var roles = wok.cookie.get('roles');
            var order = tab.find('order').text();

            if (roles) {
                var role = JSON.parse(roles)[titleKey.toLowerCase()];
                var mode = tab.find('[role="' + role + '"]').attr('mode');
                wok.tabMode[titleKey.toLowerCase()] = mode;
                tabs.push({
                    functionality: functionality,
                    title: title,
                    path: path,
                    mode: mode,
                    order: order,
                    colorTab1: colorTab1,
                    colorTab2: colorTab2
                });
            } else {
                document.location.href = 'login.html';
            }
        });

        return tabs;
    };

    var retrieveTabs = function(url) {
        var tabs = [];
        $.ajax({
            url : url,
            async : false,
            success : function(xmlData) {
                tabs = parseTabs(xmlData);
            },
            statusCode : {
                404: function() {
                    return tabs;
                }
            }
        });
        return tabs;
    };

    var wokConfigUrl = 'ui/config/tab-ext.xml';
    var pluginConfigUrl = 'plugins/{plugin}/ui/config/tab-ext.xml';
    var pluginI18nUrl = 'plugins/{plugin}/i18n.json';
    var DEFAULT_HASH;
    var buildTabs = function(callback) {
        var tabs = retrieveTabs(wokConfigUrl);
        wok.listPlugins(function(plugins) {
            $(plugins).each(function(i, p) {
                var url = wok.substitute(pluginConfigUrl, {
                    plugin: p
                });
                var i18nUrl = wok.substitute(pluginI18nUrl, {
                    plugin: p
                });
                wok.getI18n(function(i18nObj){ $.extend(i18n, i18nObj)},
                            function(i18nObj){ //i18n is not define by plugin
                            }, i18nUrl, true);
                var pluginTabs = retrieveTabs(url);
                if(pluginTabs.length > 0){
                    tabs.push.apply(tabs, pluginTabs);
                }
            });

            //sort second level tab based on their ordering number
            var orderedTabs = tabs.slice(0);
            orderedTabs.sort(function(a, b) {
                return a.order - b.order;
            });
            //redirect to empty page when no plugin installed
            if(tabs.length===0){
                DEFAULT_HASH = 'wok-empty';
            } else {
                var defaultTab = orderedTabs[0]
                var defaultTabPath = defaultTab && defaultTab['path']

                // Remove file extension from 'defaultTabPath'
                DEFAULT_HASH = defaultTabPath &&
                    defaultTabPath.substring(0, defaultTabPath.lastIndexOf('.'))
                }

                genTabs(orderedTabs);
                wok.getHostname();
                wok.logos('ul#plugins',true);
                wok.logos('ul#wok-about',false);

                callback && callback();
            }, function(data) {
               wok.message.error(data.responseJSON.reason);
            }, true);
    };

    var onLanguageChanged = function(lang) {
        wok.lang.set(lang);
        location.reload();
    };

    /**
     * Do the following setup:
     *   1) Clear any timing events.
     *   2) If the given URL is invalid (i.e., no corresponding href value in
     *      page tab list.), then clear location.href and inform the user;
     *
     *      Or else:
     *      Move the page tab indicator to the right position;
     *      Load the page content via Ajax.
     */
    var onWokRedirect = function(url) {
        /*
         * Find the corresponding tab node and animate the arrow indicator to
         * point to the tab. If nothing found, inform user the URL is invalid
         * and clear location.hash to jump to home page.
         */
        var tab = $('#tabPanel a[href="' + url + '"]');
        if (tab.length === 0 && url != 'wok-empty.html') {
            location.hash = '#';
            return;
        }
        //Remove the tab arrow indicator for no plugin
        if (url == 'wok-empty.html') {
            $('#main').html('No plugins installed currently.You can download the available plugins <a href="https://github.com/kimchi-project/kimchi">Kimchi</a> and <a href="https://github.com/kimchi-project/ginger">Ginger</a> from Github').addClass('noPluginMessage');
        } else {
            var plugin = $(tab).parent().find("input[name='funcTab']").val();
            var colorTab1 = $(tab).parent().find("input[name='colorTab1']").val();
            var colorTab2 = $(tab).parent().find("input[name='colorTab2']").val();
            var toolbar = $('#toolbar').closest('.navbar-default.toolbar');
            $('#toolbar ul.tools').html('');

            $('#tabPanel').css('background-color', colorTab1);
            $('#tabPanel ul li').removeClass('active');
            $('#tabPanel ul li a').removeAttr('style');
            $.each($('#tabPanel li'), function(i, t) {
                if ($(t).hasClass(plugin + 'Tab')) {
                    $(t).css('display', 'block');
                } else {
                    $(t).css('display', 'none');
                }
            });

            $(tab).parent().addClass('active');
            $(tab).css('background-color', colorTab2).focus();
            $(toolbar).css('background-color', colorTab2);

            $('#functionalTabPanel ul li').removeClass('active');
            $('#functionalTabPanel ul li').removeAttr('style');
            $('#functionalTabPanel ul .' + plugin + 'Tab').parent().addClass('active').focus();
            $('#functionalTabPanel ul .' + plugin + 'Tab').parent().css('background-color', colorTab1);

            // Disable Help button according to selected tab
            if ($(tab).hasClass("disableHelp")) {
                $('#btn-help').css('cursor', "not-allowed");
                $('#btn-help').off("click");
            }
            else {
                $('#btn-help').css('cursor', "pointer");
                $('#btn-help').on("click", wok.openHelp);
            }
            // Load page content.
            loadPage(url);
        }
    };

    /**
     * Use Ajax to dynamically load a page without a page refreshing. Handle
     * arrow cursor animation, DOM node focus, and page content rendering.
     */
    var loadPage = function(url) {
        // Get the page content through Ajax and render it.
        url && $('#main').load(url, function(responseText, textStatus, jqXHR) {
            if (jqXHR['status'] === 401 || jqXHR['status'] === 303) {
                var isSessionTimeout = jqXHR['responseText'].indexOf("sessionTimeout")!=-1;
                document.location.href = isSessionTimeout ? 'login.html?error=sessionTimeout' : 'login.html';
                return;
            }
        });
    };

    /*
     * Update page content.
     * 1) If user types in the main page URL without hash, then we apply the
     *    default hash. e.g., http://kimchi.company.com:8000;
     * 2) If user types a URL with hash, then we publish an "redirect" event
     *    to load the page, e.g., http://kimchi.company.com:8000/#templates.
     */
    var updatePage = function() {
        // Parse hash string.
        var hashString = (location.hash && location.hash.substr(1));

        /*
         * If hash string is empty, then apply the default one;
         * or else, publish an "redirect" event to load the page.
         */
        if (!hashString) {
            location.hash = DEFAULT_HASH;
        }
        else {
            wok.topic('redirect').publish(hashString + '.html');
        }
    };

    /**
     * Register listeners including:
     * 1) wok redirect event
     * 2) hashchange event
     * 3) Tab list click event
     * 4) Log-out button click event
     * 5) About button click event
     * 6) Help button click event
     * 7) Start notifications loop
     */
    var initListeners = function() {
        wok.topic('languageChanged').subscribe(onLanguageChanged);
        wok.topic('redirect').subscribe(onWokRedirect);

        /*
         * If hash value is changed, then we know the user is intended to load
         * another page.
         */
        window.onhashchange = updatePage;

        /*
         * Register click listener of tabs. Replace the default reloading page
         * behavior of <a> with Ajax loading.
         */
        $('#tabPanel ul').on('click', 'a.item', function(event) {
            var href = $(this).attr('href');
            // Remove file extension from 'href'
            location.hash = href.substring(0,href.lastIndexOf('.'))
            /*
             * We use the HTML file name for hash, like: guests for guests.html
             * and templates for templates.html.
             *     Retrieve hash value from the given URL and update location's
             * hash part. It has 2 effects: one is to publish Wok "redirect"
             * event to trigger listener, the other is to put an entry into the
             * browser's address history to make pages be bookmark-able.
             */
            // Prevent <a> causing browser redirecting to other page.
            event.preventDefault();
        });

        /*
         * Register click listener of second level tabs. Replace the default reloading page
         * behavior of <a> with Ajax loading.
         */
         $('#functionalTabPanel ul li').on('click', 'a.item', function(event) {
            var plugin = $(this).text().toLowerCase();
            var previousPlugin = $('#functionalTabPanel ul li.active a').text().toLowerCase();

            $('#tabPanel').switchClass(previousPlugin + 'Tab', plugin + 'Tab');
            $('#tabPanel ul li').removeClass('active');
            $.each($('#tabPanel li'), function(i, t) {
                if ($(t).hasClass(plugin + 'Tab')) {
                    $(t).css('display', 'block');
                } else {
                    $(t).css('display', 'none');
                }
            });

            $('#functionalTabPanel ul li').removeClass('active');
            $(this).parent().addClass('active').focus();

            var firstTab = $('#tabPanel ul.navbar-nav li.' + plugin + 'Tab').first();
            $(firstTab).addClass('active');

            var href = $('a.item', firstTab).attr('href');
            location.hash = href.substring(0,href.lastIndexOf('.'));
            event.preventDefault();
        });

        // Perform logging out via Ajax request.
        $('#btn-logout').on('click', function() {
            wok.logout(function() {
                wok.isLoggingOut = true;
                document.location.href = "login.html";
            }, function(err) {
                wok.message.error(err.responseJSON.reason);
            });
        });

        // Set handler for about button
        $('#btn-about').on('click', function(event) {
            event.preventDefault();
        });

        $("#aboutModal").append($("#about-tmpl").html());

        // Set handler for help button
        $('#btn-help').on('click', wok.openHelp);
    };

    var initUI = function() {
        var errorMsg = "";
        $(document).bind('ajaxError', function(event, jqXHR, ajaxSettings, errorThrown) {
            if (!ajaxSettings['wok']) {
                return;
            }

            if (jqXHR['status'] === 401) {
                var isSessionTimeout = jqXHR['responseText'].indexOf("sessionTimeout")!=-1;
                wok.user.showUser(false);
                wok.previousAjax = ajaxSettings;
                $(".empty-when-logged-off").empty();
                $(".remove-when-logged-off").remove();
                document.location.href= isSessionTimeout ? 'login.html?error=sessionTimeout' : 'login.html';
                return;
            }
            else if((jqXHR['status'] == 0) && ("error"==jqXHR.statusText) && !wok.isLoggingOut && errorMsg == "") {
               errorMsg = i18n['WOKAPI6007E'].replace("%1", jqXHR.state());
               wok.message.error(errorMsg);
            }
            if(ajaxSettings['originalError']) {
                ajaxSettings['originalError'](jqXHR, jqXHR.statusText, errorThrown);
            }
        });

        wok.user.showUser(true);
        initListeners();
        updatePage();

        // Overriding Bootstrap Modal windows to allow a stack of modal windows and backdrops
        $(document).on({
            'show.bs.modal': function () {
                var zIndex = 1040 + (10 * $('.modal:visible').length);
                $(this).css('z-index', zIndex);
                setTimeout(function() {
                    $('.modal-backdrop').not('.modal-stack').css('z-index', zIndex - 1).addClass('modal-stack');
                }, 0);
            },
            'hidden.bs.modal': function() {
                if ($('.modal:visible').length > 0) {
                    // restore the modal-open class to the body element, so that scrolling works
                    // properly after de-stacking a modal.
                    setTimeout(function() {
                        $(document.body).addClass('modal-open');
                    }, 0);
                }
            }
        }, '.modal');


    };

    // Load i18n translation strings first and then render the page.
    wok.getI18n(
        function(i18nStrings){ //success
            i18n = i18nStrings;
            buildTabs(initUI);
        },
        function(data){ //error
            wok.message.error(data.responseJSON.reason);
        }
    );

    setTimeout(wok.notificationsLoop, wok.NOTIFICATION_INTERVAL);
};


wok.checkHelpFile = function(path) {
    var lang = wok.lang.get();
    var url = path.replace("tabs", "help/" + lang);
    // Checking if help page exist.
    $.ajax({
        url: url,
        async: false,
        error: function() { url = ""; },
        success: function() { }
    });
    return url;
};

wok.getHostname = function(e) {
    host = window.location.hostname;
    $('span.host-location').text(host);
    return host;
}

wok.openHelp = function(e) {
    var tab = $('#tabPanel ul li.active');
    var url = $(tab).find("input[name='helpPath']").val();
    window.open(url, "Wok Help");
    e.preventDefault();
};
