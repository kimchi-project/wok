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

wok.initSettings = function() {
  wok.opts_user_log = {};
  wok.opts_user_log['id'] = 'user-log-content';
  wok.opts_user_log['gridId'] = "user-log-grid";
  wok.opts_user_log['loadingMessage'] = i18n['WOKSETT0007M'];
  wok.initUserLog();
};

wok.initUserLogConfig = function() {
  wok.listUserLogConfig();
}

wok.getUserLogs = function(suc, err) {
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
};

wok.getFilteredUserLogs = function(suc, err, search) {
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
};

wok.downloadLogs = function(suc, err, search) {
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
};

wok.listUserLogConfig = function() {

  var ulGrid = [];
  var gridFields = [];

  gridFields = [{
      "column-id": 'app',
      "converter": 'string',
      "formatter": "settings-user-log-app",
      "title": i18n['WOKSETT0001M']
    }, {
      "column-id": 'user',
      "converter": 'string',
      "title": i18n['WOKSETT0002M']
    }, {
      "column-id": 'ip',
      "converter": 'string',
      "title": i18n['WOKSETT0014M']
    }, {
      "column-id": 'req',
      "converter": 'string',
      "title": i18n['WOKSETT0003M']
    }, {
      "column-id": 'date',
      "converter": 'date-locale-converter',
      "order": 'desc',
      "title": i18n['WOKSETT0004M']
    }, {
      "column-id": 'time',
      "converter": 'time-locale-converter',
      "order": 'desc',
      "title": i18n['WOKSETT0005M']
    }, {
      "column-id": 'zone',
      "converter": 'string',
      "width": "6%",
      "title": i18n['WOKSETT0013M']
    }, {
      "column-id": 'status',
      "converter": 'string',
      "width": "7%",
      "title": i18n['WOKSETT0015M']
    }, {
      "column-id": 'message',
      "converter": 'string',
      "formatter": "settings-user-log-message",
      "sortable": false,
      "width": "30%",
      "title": i18n['WOKSETT0006M']
    }
  ];

  wok.opts_user_log['gridFields'] = JSON.stringify(gridFields);
  wok.opts_user_log['converters'] = wok.localeConverters;

  ulGrid = wok.createBootgrid(wok.opts_user_log);
  wok.hideBootgridLoading(wok.opts_user_log);
  wok.initUserLogConfigGridData();
};

wok.initUserLogConfigGridData = function() {
  wok.clearBootgridData(wok.opts_user_log['gridId']);
  wok.hideBootgridData(wok.opts_user_log);
  wok.showBootgridLoading(wok.opts_user_log);

  var labelStyle = function(status) {
    var result = null;
    if (status != undefined) {
      var firstNumberOfStatus = status.toString().charAt(0);
      result = {
        labelColor: "",
        labelIcon: ""
      };
      switch(firstNumberOfStatus) {
        case "1":
        case "2": result.labelColor = 'label label-info'; result.labelIcon = 'fa fa-check fa-2'; break;
        case "3": result.labelColor = 'label label-warning'; result.labelIcon = 'fa fa-times fa-2'; break;
        case "4":
        case "5": result.labelColor = 'label label-danger'; result.labelIcon = 'fa fa-times fa-2'; break;
      }
    }
    return result;
  }

  wok.getUserLogs(function(result) {
    $.each(result, function(index, log){
      var statusLabel = labelStyle(log.status);
      var userLabel = labelStyle(log.user);
      if (statusLabel != null) {
        log.status = "<span class='" + statusLabel.labelColor + "'><i class='" + statusLabel.labelIcon + "' aria-hidden='true'></i> " + log.status + "</span> ";
      } else {
        log.status = "";
      }
      if (userLabel == null) {
        log.user = "N/A";
      }
    })
    wok.loadBootgridData(wok.opts_user_log['gridId'], result);
    wok.showBootgridData(wok.opts_user_log);
    wok.hideBootgridLoading(wok.opts_user_log);
  }, function(error) {
    wok.message.error(error.responseJSON.reason, '#message-container-area');
    wok.hideBootgridLoading(wok.opts_user_log);
  });
};

wok.initUserLog = function() {
  $(".content-area", "#wokSettings").css("height", "100%");
  wok.initUserLogConfig();
  $('#advanced-search-button').on('click',function(){
    wok.window.open('tabs/settings-search.html');
  });

  $("#download-button").on('click',function(){
    var search = $('#download-button').data('search');
    if(search){
      search +='&';
    };
    wok.downloadLogs(function(result) {
        window.open(result.uri, '_blank');
      }, function(error) {
        wok.message.error(error.responseJSON.reason, '#message-container-area');
      },search);
  });

  $("#refresh-button").on('click', function(){
    $("#download-button").data('search', '');
    $("#user-log-grid").bootgrid("search");
    wok.initUserLogConfigGridData();
  });

};

wok.initUserLogWindow = function() {
  var currentLocale = wok.lang.get_locale();
  currentLocale = currentLocale.substring(0, currentLocale.indexOf('-'));
  $("#request-type").selectpicker();
  $.datepicker.setDefaults($.datepicker.regional[currentLocale]);
  $("#date").datepicker({ dateFormat: 'yy-mm-dd',
    onSelect: function(dateText) {
      $('#button-search').prop('disabled',false);
    },
    beforeShow: function(input, inst) {
       $('#ui-datepicker-div').removeClass(function() {
           return $('input').get(0).id;
       });
       $('#ui-datepicker-div').addClass(this.id);
   }
  });
  var pluginsData = [];
  wok.listPlugins(function(pluginReturn) {
        $.each(pluginReturn, function(i, obj) {
          pluginsData.push({"app": obj});
        });
        pluginsData.unshift({"app": "wok"});
        var pluginsTt = new Bloodhound({
                  datumTokenizer: Bloodhound.tokenizers.obj.whitespace('app'),
                  queryTokenizer: Bloodhound.tokenizers.whitespace,
                  local: pluginsData
              });
        pluginsTt.initialize();

        $('.typeahead').typeahead(
                {
                    autoselect:  false
                }, {
                name: 'application-name',
                displayKey: 'app',
                source: pluginsTt.ttAdapter()
        });

  });

  $('#form-advanced-search').submit(function(event) {
      event.preventDefault();
      var $inputs = $('#form-advanced-search :input').not('button');
      var values = {};
      $inputs.each(function() {
          if($(this).val()) {
            values[this.name] = $(this).val();
          }
      });
      if(Object.keys(values).length){
        var form = $('#form-advanced-search').serialize();
        wok.getFilteredUserLogs(function(result) {
          $("#"+wok.opts_user_log['gridId']).bootgrid("clear");
          $("#"+wok.opts_user_log['gridId']).bootgrid("append", result.records);
          $("#download-button").data('search',form);
          wok.window.close();
        }, function(err) {
          wok.message.error(err.responseJSON.reason, '#alert-modal-container');
          wok.hideBootgridLoading(wok.opts_user_log);
        }, form);
      }else {
      wok.getUserLogs(function(result) {
        $("#"+wok.opts_user_log['gridId']).bootgrid("clear");
        $("#"+wok.opts_user_log['gridId']).bootgrid("append", result);
      }, function(error) {
        wok.message.error(error.responseJSON.reason, '#message-container-area');
        wok.hideBootgridLoading(wok.opts_user_log);
      });
        wok.window.close();
      }
  });

  $('#button-search').on('click',function(){
       $('#form-advanced-search :input').each(function(){
         if( $(this).val() === '' ){
            $(this).prop('disabled',true);
         }
      });
      $('#form-advanced-search').submit();
  });
};
