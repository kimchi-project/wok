/*
 * Project Wok
 *
 * Copyright IBM Corp, 2016
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

wok.logos = function(element, powered) {
    powered = (typeof powered === 'undefined') ? false : true;
    var genLogos  = function(obj){
        var objHtml = [];
        var plugins = [];
        for (var i in obj) {
            plugins.push(obj[i])
        }
        plugins.sort(function(a, b) {
            return a.name.localeCompare( b.name );
        });
        $(plugins).each(function(i, plugin) {
            var name = plugin.name[0].toUpperCase() + plugin.name.slice(1);
            if(plugin.image && plugin.version) {
                objHtml.push(
                    '<li>',
                        '<img src="',plugin.image,'" longdesc="',name,' logotype" alt="',name,' plugin - ',plugin.version,'" title="',name,' plugin - ',plugin.version,'" />',
                        '<span class="plugin-title">',name,'</span>',
                        '<span class="plugin-version">',plugin.version,'</span>',
                    '</li>'
                );
            }else if(plugin.image) {
                objHtml.push(
                    '<li>',
                        '<img src="',plugin.image,'" longdesc="',name,' logotype" alt="',name,' plugin" title="',name,' plugin" />',
                        '<span class="plugin-title">',name,'</span>',
                    '</li>'
                );
            }
        });
        return objHtml.join('');
    };

    var retrieveVersion = function(url) {
        var version = "";
        $.ajax({
            dataType: "json",
            url : url+'/config',
            async : false,
            success : function(data) {
                version = data.version;
            },
        });
        return version;
    };

    var checkImage = function (testurl) {
     var http = $.ajax({
        type:"HEAD",
        url: testurl,
        async: false
      })
      return http.status;
    }

    var pluginUrl = 'plugins/{plugin}';
    var buildLogos = function() {
        var logos = [];
        var  obj = {};
        wok.listPlugins(function(plugins) {
            if(plugins && plugins.length > 0) {
                $(plugins).each(function(i, p) {
                    var url = wok.substitute(pluginUrl, {
                        plugin: p
                    });
                    obj[i] = {
                        name : p
                    }
                    var pluginVersions;
                    pluginVersions = retrieveVersion(url);
                    if(pluginVersions && pluginVersions.length > 0){
                        obj[i].version = pluginVersions;
                    }
                    var imagepath = url+'/images/'+p;
                    if(checkImage(imagepath+'.svg') == 200) {
                        obj[i].image = imagepath+'.svg';
                    }
                    else if(checkImage(imagepath+'.png') == 200) {
                        obj[i].image = imagepath+'.png';
                    }
                });
                var generatedLogos = genLogos(obj);
                if(generatedLogos.length > 0) {
                    $(element).append(generatedLogos);
                    if(powered) {
                        $(element).parentsUntil('.container').find('.powered').removeClass('hidden');
                    }else {
                        $(element).parentsUntil('.container').find('.powered').remove();
                    }
                }
            }
        });
    };
    buildLogos();

 };
