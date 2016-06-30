/*
 * Project Wok
 *
 * Copyright IBM Corp, 2016
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

// Sets defalt Datatable options for Wok

wok.initCompleteDataTableCallback = function(e) {
    var tableId = $('#'+e.sTableId+'_wrapper');
    $('.dataTables_filter input',tableId).attr("placeholder", "Filter");
    $(".dataTables_filter label",tableId).contents().filter(function() {
    return this.nodeType === 3;
    }).wrap('<div class="sr-only" />');
    $(".dataTables_length label",tableId).contents().filter(function() {
    return this.nodeType === 3;
    }).wrap('<div class="sr-only" />');
    $(".dataTables_length select",tableId).selectpicker();
    $(".dataTables tfoot",tableId).remove();
};

$.extend( true, $.fn.dataTable.defaults, {
    "sPaginationType": "full_numbers",
    "dom": '<"row"<"col-sm-12 filter"<"pull-right"l><"pull-right"f>>><"row"<"col-sm-12"t>><"row"<"col-sm-6 pages"p><"col-sm-6 info"i>>',
    "initComplete": function(settings, json) {
        wok.initCompleteDataTableCallback(settings);
    }
});