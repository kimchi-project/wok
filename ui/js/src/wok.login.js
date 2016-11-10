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
wok.login_main = function() {
    "use strict";

    // verify if language is available
    var selectedLanguage = wok.lang.get();
    if ($('#userLang option[value="'+selectedLanguage+'"]').length == 1)  {
        $('#userLang').val(selectedLanguage);
        $('#userLang option[value="'+selectedLanguage+'"]').attr("selected", "selected");
        $('.filter-option:first').parent().attr('title',$('#userLang option[value="'+selectedLanguage+'"]').text());
        $('.filter-option:first').text($('#userLang option[value="'+selectedLanguage+'"]').text());
    }

    // verify if locale is available
    var selectedLocale = wok.lang.get_locale();
    if ($('#userLocale option[value="'+selectedLocale+'"]').length == 1) {
        $('#userLocale').val(selectedLocale);
        $('#userLocale option[value="'+selectedLocale+'"]').attr("selected", "selected");
        $('.filter-option:last').parent().attr('title',$('#userLocale option[value="'+selectedLocale+'"]').text());
        $('.filter-option:last').text($('#userLocale option[value="'+selectedLocale+'"]').text());
    }

    $('#userLang').on('change', function() {
        wok.lang.set($(this).val());
        location.reload();
    });

    $('#userLocale').on('change', function() {
        wok.lang.set_locale($(this).val());
    });

    var query = window.location.search;
    var error = /.*error=(.*?)(&|$)/g.exec(query);
    if (error && error[1] === "sessionTimeout") {
        $("#messSession").show();
    }

    var userNameBox = $('#username');
    var passwordBox = $('#password');
    var loginButton = $('#btn-login');

    var login = function(event) {
        $("#login").hide();
        $("#logging").show();

        var userName = userNameBox.val();
        userName && wok.user.setUserName(userName);
        var settings = {
            username: userName,
            password: passwordBox.val()
        };

        wok.login(settings, function(data) {
            var query = window.location.search;
            var next  = /.*next=(.*?)(&|$)/g.exec(query);
            if (next) {
                var next_url = decodeURIComponent(next[1]);
            }
            else {
                var lastPage = wok.cookie.get('lastPage');
                var next_url = lastPage ? lastPage.replace(/\"/g,'') : "/";
            }
            wok.cookie.set('roles',JSON.stringify(data.roles));
            window.location.replace(window.location.pathname.replace(/\/+login.html/, '') + next_url);
        }, function(jqXHR, textStatus, errorThrown) {
            if (jqXHR.responseText == "") {
                $("#messUserPass").hide();
                $("#missServer").show();
            } else {
                $("#missServer").hide();
                $("#messUserPass").show();
            }
            $("#messSession").hide();
            $("#logging").hide();
            $("#login").show();
        });

        return false;
    };

    wok.logos('#wok-logos',true);
    $('#btn-login').bind('click', login);
};
