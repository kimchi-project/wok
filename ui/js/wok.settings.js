/*
 * Copyright IBM Corp, 2017
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
 */

wok.initSettings = function() {
    wok.initPluginsMgmt();
};

wok.initPluginsMgmt = function() {
    // Make wok.plugins is ready to be used
    if (wok.plugins == undefined) {
        setTimeout(wok.initPluginsMgmt, 2000);
        return;
    }

    var plugins = wok.plugins;
    if (plugins && plugins.length) {
        plugins.sort(function(a, b) {
            if (a.name !== undefined && b.name !== undefined) {
                return a.name.localeCompare( b.name );
            } else {
                return 0
            }
        });
        $("#plugins-mgmt-body").empty();
        $.each(plugins, function(i,value){
            wok.generatePluginEntry(value);
        });
        $('#plugins-mgmt-datagrid').dataGrid({enableSorting: false});
    } else {
        $('#plugins-mgmt-datagrid ul').addClass('hidden');
        $('#plugins-mgmt-datagrid .no-matching-data').removeClass('hidden');
    }

    // Filter configuration
    var pluginsOptions = {
        valueNames: ['plugin-name-filter', 'plugin-description-filter']
    };
    var pluginsFilterList = new List('plugins-mgmt-content-area', pluginsOptions);
    pluginsFilterList.sort('plugin-name-filter', {
        order: "asc"
    });

    pluginsFilterList.search($('#search_input_plugins_mgmt').val());
    pluginsFilterList.on('searchComplete',function(){
        if(pluginsFilterList.matchingItems.length == 0){
            $('#plugins-mgmt-datagrid ul').addClass('hidden');
            $('#plugins-mgmt-datagrid .no-matching-data').removeClass('hidden');
        } else {
            $('#plugins-mgmt-datagrid ul').removeClass('hidden');
            $('#plugins-mgmt-datagrid .no-matching-data').addClass('hidden');
        }
    });

    // Toggle handler
    $('#plugins-mgmt-body').on('change', '.wok-toggleswitch-checkbox', function(event) {
        var pluginNode = $(this).parent().parent();
        if($(this).is(":checked")) {
            togglePlugin(pluginNode, true);
        } else {
            togglePlugin(pluginNode, false);
        }
    });

    var enablePlugin = function(plugin) {
        wok.enablePlugin(plugin, function(result){
            location.reload();
        }, function(){});
    };

    var disablePlugin = function(plugin) {
        wok.disablePlugin(plugin, function(result){
            location.reload();
        }, function(){});
    };

    var togglePlugin = function(pluginNode, enable) {
        var plugin = pluginNode.data('id');
        var depends = $('input[name=plugin-depends]', pluginNode).val();
        var is_dependency_of = $('input[name=plugin-is-dependency-of]', pluginNode).val();

        var confirmMessage = undefined;
        if (depends && enable) {
            var confirmMessage = i18n['WOKPL0001M'].replace('%1', '<strong>' + plugin + '</strong>');
            confirmMessage = confirmMessage.replace('%2', '<strong>' + depends + '</strong>');
        } else if (is_dependency_of && !enable) {
            var confirmMessage = i18n['WOKPL0002M'].replace('%1', '<strong>' + plugin + '</strong>');
            confirmMessage = confirmMessage.replace('%2', '<strong>' + is_dependency_of + '</strong>');
        }

        if (confirmMessage) {
            var settings = {
                title: i18n['WOKAPI6005M'],
                content: confirmMessage,
                confirm: i18n['WOKAPI6004M'],
                cancel: i18n['WOKAPI6003M']
            };
            wok.confirm(settings, function() {
                $("body").css("cursor", "wait");
                if (enable)
                    enablePlugin(plugin);
                else if (!enable)
                    disablePlugin(plugin);
            }, function() {
                if (enable) {
                    $('.wok-toggleswitch-checkbox', pluginNode).removeAttr('checked');
                }
                else if (!enable) {
                    $('.wok-toggleswitch-checkbox', pluginNode).replaceWith('<input type="checkbox" name="plugin-status[]" id="' + plugin + '" value="' + plugin + '" checked class="wok-toggleswitch-checkbox">');
                }
            });
        } else {
            if (enable)
                enablePlugin(plugin);
            else if (!enable)
                disablePlugin(plugin);
        }
    };
};

wok.generatePluginEntry = function(value){
    //var description = value.description;
    var description = "Plugin description " + value.name;
    var checked = (value.enabled) ? 'checked' : '';

    var id = 'plugin-' + value.name;
    var disabled = (value.enabled) ? '' : 'disabled';
    var pluginstatus  = (value.enabled) ? 'On' : 'Off';

    var pluginEntry = $.parseHTML(wok.substitute($("#pluginItem").html(), {
        id: id,
        name: value.name,
        disabled: disabled,
        checked: checked,
        pluginstatus: pluginstatus,
        depends: value.depends.join(", "),
        is_dependency_of: value.is_dependency_of.join(", "),
        logo: value.image ? value.image : '../images/pl.png',
        description: description
    }));

        $('#plugins-mgmt-body').append(pluginEntry);
};
