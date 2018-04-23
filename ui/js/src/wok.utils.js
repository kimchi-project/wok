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

/**
 * To check whether a given DOM node is entirely within the viewport
 * of a browser.
 * @param {DOMObject} el The given DOM node to check.
 *
 * @returns {true|false|undefined}
 *     true if the node is within viewport, or
 *     false if the node is not entirely visible, or
 *     undefined if the given parameter is invalid.
 */
wok.isElementInViewport = function(el) {
    if (!el || !el.getBoundingClientRect) {
        return undefined;
    }

    var rect = el.getBoundingClientRect();

    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
};

/**
 * To change the byte to proper unit.
 * @param number needed to change unit.
 * @param digits after the decimal point.
 * @returns str with unit.
 */
wok.changetoProperUnit = function(numOrg, digits, base) {
    if (numOrg === undefined) {
        return "";
    }
    var suffixes = [ 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y', 'B' ];
    var base = base || 1024;
    var numTemp = numOrg;
    var result = numOrg.toFixed(digits) + 'B';
    for ( var i = 0; i < suffixes.length; i++) {
        var numTemp = numTemp / base;
        if (numTemp < 1)
            break;
        result = numTemp.toFixed(digits) + suffixes[i]
    }
    return result;
};

/**
 * wok.formatMeasurement util.
 *
 * Refer to "Units of information" (
 *   http://en.wikipedia.org/wiki/Units_of_information
 * ) for more information about measurement units.
 *
 * @param number The number to be normalized.
 * @param settings
 *     * base Measurement base, accepts 2 or 10. defaults to 2.
 *     * unit The unit of the measurement, e.g., B, Bytes/s, bps, etc.
 *     * fixed The number of digits after the decimal point.
 *
 * @returns [object]
 *     * v The number part of the measurement.
 *     * s The suffix part of the measurement including multiple and unit.
 *         e.g., kB/s means 1000B/s, KiB/s for 1024B/s.
 */
(function() {
    var unitBaseMapping = {
        2: [{
            us: 'Ki',
            v: 1024
        }, {
            us: 'Mi',
            v: 1048576
        }, {
            us: 'Gi',
            v: 1073741824
        }, {
            us: 'Ti',
            v: 1099511627776
        }, {
            us: 'Pi',
            v: 1125899906842624
        }],
        10: [{
            us: 'k',
            v: 1000
        }, {
            us: 'M',
            v: 1000000
        }, {
            us: 'G',
            v: 1000000000
        }, {
            us: 'T',
            v: 1000000000000
        }, {
            us: 'P',
            v: 1000000000000000
        }]
    };

    var Formatted = function(value, suffix) {
        this['v'] = value;
        this['s'] = suffix;
    };
    Formatted.prototype.toString = function() {
        return this['v'] + this['s'];
    };

    var format = function(number, settings) {
        if(number === (undefined || null) || isNaN(number)) {
            return number;
        }

        var settings = settings || {};
        var unit = settings['unit'] || 'B';
        var base = settings['base'] || 2;
        if(base !== 2 && base !== 10) {
            return new Formatted(number, unit);
        }

        // Introduce converter to format data.
        // Converter's to function will be used for formatting.
        // if not passed then 'to' formatting will not be done.
        // e.g. formatMeasurement( 2,
        //          { .. , converter: wok.localeConverters["number-locale-converter"]})
        var converter = settings['converter'] || null;
        var converter_to_fun = converter?converter['to']:''
        var fixed = settings['fixed'];

        var unitMapping = unitBaseMapping[base];
        var unitmap = { 'Ki': 'WOKFMT2001M', 'Mi': 'WOKFMT2002M', 'Gi': 'WOKFMT2003M',
                        'Ti': 'WOKFMT2004M', 'Pi': 'WOKFMT2005M', 'k': 'WOKFMT2006M',
                        'M': 'WOKFMT2007M', 'G': 'WOKFMT2008M', 'T': 'WOKFMT2009M',
                        'P': 'WOKFMT2010M'}
        for(var i = unitMapping.length - 1; i >= 0; i--) {
            var mapping = unitMapping[i];
            var s_key = mapping['us'];
            var suffix = i18n[unitmap[s_key]];
            var startingValue = mapping['v'];
            if(number < startingValue) {
                continue;
            }

            var formatted = number / startingValue;
            formatted = fixed ? formatted.toFixed(fixed) : formatted;
            formatted = converter_to_fun ? converter_to_fun(Number(formatted)) : formatted;
            return new Formatted(formatted, suffix + unit);
        }

        formatted = fixed ? number.toFixed(fixed) : number;
        /* format the formatted number as per settings's converter, if not present return as it is. */
        formatted_val = converter_to_fun ? converter_to_fun(Number(formatted)) : formatted;
        return new Formatted(formatted_val, unit);
    };

    wok.formatMeasurement = format;
})();

wok.isUnsignedNumeric = function(number) {
    var reg = /^d+(.d+)?$/
    return reg.test(number);
}

wok.isServer = function(server) {
    var domain = "([0-9a-z_!~*'()-]+\.)*([0-9a-z][0-9a-z-]{0,61})?[0-9a-z]\.[a-z]{2,6}";
    var ip = "(\\d{1,3}\.){3}\\d{1,3}";
    regex = new RegExp('^' + domain + '|' + ip + '$');
    if (!regex.test(server)) {
        return false;
    } else {
        return true;
    }
};

wok.escapeStr = function(str) {
    if (str)
        return str.replace(/([ #;?%&,.+*~\\':"!^$[\]()<=>`{|}\/@])/g,'\\$&');

    return str;
};

wok.urlSafeB64Decode = function(str) {
    return atob(str.replace(/-/g, '+').replace(/_/g, '/'), true);
}

wok.urlSafeB64Encode = function(str) {
    return btoa(str, true).replace(/\+/g, '-').replace(/\//g, '_');
}

wok.notificationsLoop = function() {
    wok.getNotifications(
        function(notifications){
            if(notifications && notifications.length > 0) {
                $.each(notifications, function(i, notif) {
                    // Check if notification is being displayed
                    if (($("#alert-container").find("div:contains('" + notif.message + "')").length) == 0) {
                        wok.message.notify(notif, '#alert-container');
                    }
                });
            }
        }, undefined);
}

wok.datetimeLocaleConverter = function datetimeLocaleConverter(datetime_string, locale){
   var dateRegEx = /(\d{4})-(\d{2})-(\d{2})/;
   if(dateRegEx.test(datetime_string.substr(0,10))){
     var dte = new Date(datetime_string.substr(0,10) + 'T' + datetime_string.substr(11));
     var options = { year: 'numeric', month: 'long', day: 'numeric' };
     return dte.toLocaleString(locale, options);
  }else{
    return datetime_string;
  }
}

wok.dateLocaleConverter = function dateLocaleConverter(date_string, locale){
     var dte = new moment(date_string);
     var options = { year: 'numeric', month: 'numeric', day: 'numeric' };
     return dte._d.toLocaleDateString(locale, options);
}

wok.timeLocaleConverter = function timeLocaleConverter(time_string, locale){
     var dte = new Date((new Date(0)).toDateString() + ' ' + time_string);
     return dte.toLocaleTimeString(locale);
}

wok.numberLocaleConverter = function numberConverter(number, locale){
     number = (typeof(number) === 'number') ? number.toLocaleString(wok.lang.get_locale()) : number;
     return number;
}

wok.localeConverters = {
       "date-locale-converter": {
           to: function(date){
              return wok.dateLocaleConverter(date, wok.lang.get_locale());
           }
       },
       "time-locale-converter": {
           to: function(time){
              return wok.timeLocaleConverter(time, wok.lang.get_locale());
           }
       },
       "datetime-locale-converter": {
            to: function(datetime){
                return wok.datetimeLocaleConverter(datetime, wok.lang.get_locale());
            }
       },
       "number-locale-converter":{
           to: function(number){
              if (number == null) {
                 return 'Unknown';
              }
              format_value = wok.numberLocaleConverter(number, wok.lang.get_locale());
              return format_value.toString().replace(/\s/g,' '); //replace non-breaking space with breaking space
           }
      }
}
