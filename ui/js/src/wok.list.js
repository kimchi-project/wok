/*
 * Project Wok
 *
 * Copyright IBM Corp, 2015-2016
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
wok.widget.List = function(opts) {
    "use strict";
    this.opts = $.extend({}, this.opts, opts);
    this.createDOM();
    this.reload();
};

wok.widget.List.prototype = (function() {
    "use strict";

    var htmlStr = [
        '<div id="{id}-section" class="panel panel-default">',
            '<div class="panel-heading">',
            '</div>',
            '<div id="content-{id}" class="panel-body">',
                '<div id="{id}-container">',
                    '<div class="wok-list-message clearfix hidden">',
                        '<div class="alert alert-danger fade in" role="alert">',
                            '<p><strong>{message}</strong> ',
                            '<span class="detailed-text"></span></p>',
                            '<p><button class="btn btn-primary btn-xs retry-button">',
                                '{buttonLabel}',
                            '</button></p>',
                        '</div>',
                    '</div>',
                    '<div id="{id}-action-group" class="wok-list-action-button-container">',
                        '<div class="dropdown mobile-action">',
                            '<button class="btn btn-primary dropdown-toggle" type="button" data-toggle="dropdown" aria-expanded="false">',
                                '<span class="mobile-action-label">{actions}</span>',
                            '</button>',
                            '<ul class="dropdown-menu" role="menu">',
                            '</ul>',
                        '</div>',
                    '</div>',
                    '<div id="{id}" class="row clearfix">',
                        '<div class="wok-list-content">',
                            '<div class="wok-list" id="list">',
                            '</div>',
                        '</div>',
                    '</div>',
                    '<div class="wok-list-mask hidden">',
                        '<div class="wok-list-loader-container">',
                            '<div class="wok-list-loading">',
                                '<div class="wok-list-loading-icon"></div>',
                                '<div class="wok-list-loading-text">',
                                    '{loading}',
                                '</div>',
                            '</div>',
                        '</div>',
                    '</div>',
                '</div>',
            '</div>',
        '</div>'
    ].join('');

    var getValue = function(name, obj) {
        var result;
        if (!Array.isArray(name)) {
            name = name.parseKey();
        }
        if (name.length !== 0) {
            var tmpName = name.shift();
            if (obj[tmpName] !== undefined) {
                result = obj[tmpName];
            }
            if (name.length !== 0) {
                result = getValue(name, obj[tmpName]);
            }
        }
        return (result);
    };

    var fillButtons = function(btnContainer){
        var toolbarButtons = this.opts.toolbarButtons;
        $.each(toolbarButtons, function(i, button) {
                var btnHTML = [
                    '<li class="',
                    (button.critical === true ? 'critical' : ''),
                    ,'">',
                        '<btn data-dismiss="modal"',
                        (button.id ? (' id="' + button.id + '"') : ''),
                        ' class="btn btn-primary"',
                        (button.disabled === true ? ' disabled="disabled"' : ''),
                        '">',
                            button.class ? ('<i class="' + button.class) + '"></i> ' : ' ',
                            button.label,
                        '</btn>',
                    '</li>'
                ].join('');
                var btnNode = $(btnHTML).appendTo(btnContainer);
                button.onClick && btnNode.on('click', button.onClick);
        });
    };

    var fillBody = function(container, fields) {
        var data = this.data;
        var converters = this.opts.converters;
        var tbody = ($('ul', container).length && $('ul', container)) || $('<ul></ul>').appendTo(container);
        tbody.empty();
        if (typeof data !== 'undefined' && data.length > 0) {
            $.each(data, function(i, row) {
                var rowNode = $('<li></li>').appendTo(tbody);
                var columnNodeHTML;
                var columnData = '';
                var state = '';
                var styleClass = '';
                var checkboxName = $('ul', container).parent().parent().parent().attr('id') + '-check' || $(container).parent().parent().parent().attr('id') + '-check';
                $.each(fields, function(fi, field) {
                    var value = getValue(field.name, row);
                    if(field.converter){
                        var converter = field.converter;
                        if(converters[converter]){
                            var to = converters[converter]['to'];
                            value = to(value);
                        }else{
                            console.error('converter ' + converters[converter] + ' not defined');
                        }
                    }
                    if (field.type === 'status' && field.name === 'enabled') {
                        styleClass = (value === true ? '' : ' disabled');
                        state = [
                            '<span class="wok-list-item-status ',
                            value === true ? 'enabled' : 'disabled',
                            '"><i class="fa fa-power-off"></i><span class="sr-only">',
                            value === true ? 'Enabled' : 'Disabled',
                            '</span></span>'
                        ].join('');
                    }
                    columnData += (field.type === 'name') ? ('<span role="status" class="wok-list-loading-icon-inline"></span><span class="wok-list-name '+field.cssClass+'" title="'+field.label+'">'+value.toString()+'</span>') : (field.type !== 'status' ? '<span class="wok-list-description '+field.cssClass+'" title="'+field.label+'">' + value.toString() + '</span>' : '');
                    columnNodeHTML = [
                        '<input class="wok-checkbox" type="checkbox" name="'+checkboxName+'" id="wok-list-',i+1,'-check" />',
                            '<label for="wok-list-',i+1,'-check" class="wok-list-cell', styleClass, '">',
                                state,
                                columnData,
                            '</div>',
                        '</label>'
                    ].join('');
                });
                $(columnNodeHTML).appendTo(rowNode);
            });
        }
    };

    var stylingRow = function(grid, className) {
        $('li',grid.bodyContainer).removeClass(className);
        $.each(grid.selectedIndex, function(){
            var nth = this + 1;
            $('li:nth-child('+nth+')',grid.bodyContainer).addClass(className);
        });
    };

    var setBodyListeners = function() {
        if (this['opts']['rowSelection'] !== 'disabled') {
            $('li:not(.generating) input[type="checkbox"]', this.bodyContainer).on('change', {
                grid: this
            },function(event) {
                var grid = event.data.grid;
                grid.selectedIndex = [];
                $("li > :checkbox:checked", this.bodyContainer).map(function() {
                    return $(this).parent().index();
                }).each(function() {
                    grid.selectedIndex.push(this);
                });
                if ($('.mobile-action-count',grid.buttonActionContainer).length) {
                    $('.mobile-action-count',grid.buttonActionContainer).remove();
                }
                if(grid.selectedIndex.length){
                    $(grid.buttonActionContainer).append('<span class="mobile-action-count"> ( <strong>'+grid.selectedIndex.length+' item(s)</strong> selected )</span>');
                }
                stylingRow.call(grid, grid, 'selected');
                grid['opts']['onRowSelected'] && grid['opts']['onRowSelected']();
            });
        }
    };

    var setData = function(data) {
        this.data = data;
        fillBody.call(this, this.bodyContainer, this.opts.fields);
        setBodyListeners.call(this);
    };

    var getSelected = function() {
        var selectedItems = [];
        for (var i = 0; i < this.selectedIndex.length; i++ ){
            var value = this.selectedIndex[i];
            selectedItems.push(this.data[value]);
        }
        // return this.selectedIndex >= 0 ? this.data[this.selectedIndex] : null;
        return selectedItems;
    };

    var showMessage = function(msg) {
        $('.detailed-text', this.messageNode).text(msg);
        $(this.messageNode).removeClass('hidden');
    };

    var hideMessage = function() {
        $(this.messageNode).addClass('hidden');
    };

    var reload = function() {
        var data = this.opts.data;
        if (!data) {
            return;
        }

        if ($.isArray(data)) {
            return this.setData(data);
        }

        if ($.isFunction(data)) {
            var loadData = data;
            $(this.maskNode).removeClass('hidden');
            loadData($.proxy(function(data) {
                this.setData(data);
                $(this.maskNode).addClass('hidden');
            }, this));
        }
    };

    var createDOM = function() {
        var containerID = this.opts.container;
        var container = $('#' + containerID);
        var gridID = this.opts.id;
        var data = this.opts.data;
        var rowSelection = this.opts.rowSelection || 'single';
        var domNode = $(wok.substitute(htmlStr, {
            id: gridID,
            loading: i18n.WOKGRD6001M,
            message: i18n.WOKGRD6002M,
            buttonLabel: i18n.WOKGRD6003M,
            detailedLabel: i18n.WOKGRD6004M,
            actions: i18n.WOKSETT0012M
        })).appendTo(container);
        this.domNode = domNode;


        var titleContainer = $('.panel-heading', domNode);
        this.titleContainer = titleContainer;

        var title = this.opts.title;
        var titleNode = null;

        if (title) {
            titleNode = $('<h3 class="panel-title">' + title + '</h3>').appendTo(titleContainer);
        }

        var bodyContainer = $('.wok-list', domNode);
        this.bodyContainer = bodyContainer;

        var selectButtonContainer = $('.wok-list-action-button-container', domNode);
        this.selectButtonContainer = selectButtonContainer;

        var buttonActionGroupContainer = $('.wok-list-action-button-container .dropdown-menu', domNode);
        this.buttonActionGroupContainer = buttonActionGroupContainer;

        var buttonActionContainer = $('.mobile-action .dropdown-toggle.btn', domNode);
        this.buttonActionContainer = buttonActionContainer;

        var gridBody = $('.wok-list-content', domNode);
        this.gridBody = gridBody;

        var maskNode = $('.wok-list-mask', domNode);
        this.maskNode = maskNode;

        var messageNode = $('.wok-list-message', domNode);
        this.messageNode = messageNode;

        fillButtons.call(this,this.buttonActionGroupContainer);

        $('.retry-button', domNode).on('click', {
            grid: this
        }, function(event) {
            event.data.grid.reload();
        });

    };

    return {
        opts: {
            container: null,
            id: null,
            rowSelection: 'single',
            onRowSelected: null,
            title: null,
            toolbarButtons: null,
            frozenFields: null,
            fields: null
        },
        createDOM: createDOM,
        setData: setData,
        getSelected: getSelected,
        reload: reload,
        showMessage: showMessage
    };
})();
