/*
 * Copyright IBM Corp, 2016
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

wok.createBootgrid = function(opts) {
  var containerId = opts['id'];
  var gridId = opts['gridId'];
  noResults = opts['noResults'];
  var fields = JSON.parse(opts['gridFields']);
  var selection = ('selection' in opts) ? opts['selection'] : true;
  var navigation = ('navigation' in opts) ? opts['navigation'] : 3;
  var converters = ('converters' in opts) ? opts['converters'] : '';

  var gridMessage = ('loadingMessage' in opts && opts['loadingMessage'].trim() && opts['loadingMessage'].length > 0) ? opts['loadingMessage'] : i18n['WOKSETT0011M'];
  var gridloadingHtml = ['<div id="' + gridId + '-loading" class="wok-list-mask">',
    '<div class="wok-list-loader-container">',
    '<div class="wok-list-loading">',
    '<div class="wok-list-loading-icon"></div>',
    '<div class="wok-list-loading-text">' + gridMessage + '</div>',
    '</div>',
    '</div>',
    '</div>'
  ].join('');

  $(gridloadingHtml).appendTo('#' + containerId);

  var gridHtml = [
    '<table id="', gridId, '" class="table table-striped" >',
    '<thead>',
    '<tr>',
    '</tr>',
    '</thead>'
  ].join('');
  $(gridHtml).appendTo('#' + containerId);
  var gridHeader = $('tr', gridHtml);

  for (var i = 0; i < fields.length; i++) {
    var columnHtml = [
      '<th data-type="', fields[i]["type"], '" data-column-id="', fields[i]["column-id"], '"', (fields[i].identifier) ? 'data-identifier="true"' : '', ("header-class" in fields[i]) ? 'data-header-css-class="gridHeader ' + fields[i]["header-class"] + '"' : 'gridHeader', ("data-class" in fields[i]) ? ' data-align="' + fields[i]["data-class"] + '"' + ' headerAlign="center"' : ' data-align="left" headerAlign="center"', ("formatter" in fields[i]) ? 'data-formatter=' + fields[i]["formatter"] : '', (fields[i].width) ? (' data-width="' + fields[i].width + '"') : '', ("converter" in fields[i]) ? ' data-converter=' + fields[i]["converter"] : '',
      '>', ("title" in fields[i]) ? fields[i]["title"] : fields[i]["column-id"],
      '</th>'
    ].join('');
    $(columnHtml).appendTo($('tr', '#' + gridId));
  }

  var grid = $('#' + gridId).bootgrid({
    selection: selection,
    multiSelect: false,
    keepSelection: false,
    rowCount: 15,
    sorting: true,
    multiSort: true,
    columnSelection: false,
    navigation: navigation,
    rowSelect: false,
    formatters: {
      "settings-user-log-app": function(column, row) {
        return '<span class="label label-primary" style="background-color:' + wok.pluginsColor[row.app] + '">' + row.app + '</span> ';
      },
      "settings-user-log-message": function(column, row) {
        return '<span class="trim" data-toggle="tooltip"  data-placement="auto bottom" title="'+row.message+'">' +row.message+ '</span> ';
      },
    },
    converters: converters,
    css: {
      iconDown: "fa fa-sort-desc",
      iconUp: "fa fa-sort-asc",
      center: "text-center"
    },
    labels: {
      search: i18n['WOKSETT0008M'],
      noResults: (opts['noResults']) ? opts['noResults'] : i18n['WOKSETT0010M'],
      infos: i18n['WOKSETT0009M']
    }
  }).on("loaded.rs.jquery.bootgrid", function(e) {
        $('.input-group .glyphicon-search').remove();
        $('.search > div').removeClass('input-group');
        $('[data-toggle="tooltip"]').tooltip();
        if ($('#' + gridId).bootgrid('getTotalRowCount') > 0) {
          // This need to be in if block to avoid showing no-record-found
          wok.showBootgridData(opts);
        }
      }).on("load.rs.jquery.bootgrid", function(e) {
    $('.input-group .glyphicon-search').remove();
        $('.search > div').removeClass('input-group');
    $('[data-toggle="tooltip"]').tooltip();
  })
  wok.hideBootgridLoading(opts);
  return grid;
}

wok.loadBootgridData = function(gridId, data) {
  wok.clearBootgridData(gridId);
  wok.appendBootgridData(gridId, data);
};

wok.clearBootgridData = function(gridId) {
  $('#' + gridId).bootgrid("clear");
};

wok.appendBootgridData = function(gridId, data) {
  $('#' + gridId).bootgrid("append", data);
};

wok.reloadGridData = function(opts) {
  return $('#' + opts['gridId']).bootgrid("reload");
}

wok.showBootgridLoading = function(opts) {
  var gridMessage = ('loadingMessage' in opts && opts['loadingMessage'].trim() && opts['loadingMessage'].length > 0) ? opts['loadingMessage'] : 'Loading...';
  $("#" + opts['gridId'] + "-loading .wok-list-loading-text").text(gridMessage);
  $("#" + opts['gridId'] + "-loading").show();
  $("#" + opts['gridId'] + "-loading").css("zIndex", 1);
};

wok.hideBootgridLoading = function(opts) {
  var gridMessage = ('loadingMessage' in opts && opts['loadingMessage'].trim() && opts['loadingMessage'].length > 0) ? opts['loadingMessage'] : 'Loading...';
  $("#" + opts['gridId'] + "-loading .wok-list-loading-text").text(gridMessage);
  $("#" + opts['gridId'] + "-loading").hide();
  $("#" + opts['gridId'] + "-loading").css("zIndex", 1);
};

wok.showBootgridData = function(opts) {
  $("#" + opts['gridId'] + " tbody").show();
};

wok.hideBootgridData = function(opts) {
  $("#" + opts['gridId'] + " tbody").hide();
};
