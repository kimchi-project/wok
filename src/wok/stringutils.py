#
# Project Wok
#
# Copyright IBM Corp, 2016
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA
import copy
import locale


def ascii_dict(base, overlay=None):
    result = copy.deepcopy(base)
    result.update(overlay or {})

    for key, value in result.items():
        result[key] = encode_value(value)

    return result


def utf8_dict(base, overlay=None):
    result = copy.deepcopy(base)
    result.update(overlay or {})

    for key, value in result.items():
        result[key] = decode_value(value)

    return result


def encode_value(val):
    """
        Convert the value to string.
        If its unicode, use encode otherwise str.
    """
    if isinstance(val, str):
        return val
    return str(val)


def decode_value(val):
    """
        Converts value to unicode,
        if its not an instance of unicode.
        For doing so convert the val to string,
        if its not instance of basestring.
    """
    if isinstance(val, bytes):
        val = val.decode('utf-8')
    return val


def format_measurement(number, settings):
    """
    Refer to "Units of information" (
    http://en.wikipedia.org/wiki/Units_of_information
    ) for more information about measurement units.

   @param number The number to be normalized.
   @param settings
        base Measurement base, accepts 2 or 10. defaults to 2.
        unit The unit of the measurement, e.g., B, Bytes/s, bps, etc.
        fixed The number of digits after the decimal point.
        locale The locale for formating the number if not passed
        format is done as per current locale.
   @returns [object]
       v The number part of the measurement.
       s The suffix part of the measurement including multiple and unit.
          e.g., kB/s means 1000B/s, KiB/s for 1024B/s.
    """
    unitBaseMapping = {
        2: [
            {'us': 'Ki', 'v': 1024},
            {'us': 'Mi', 'v': 1048576},
            {'us': 'Gi', 'v': 1073741824},
            {'us': 'Ti', 'v': 1099511627776},
            {'us': 'Pi', 'v': 1125899906842624},
        ],
        10: [
            {'us': 'k', 'v': 1000},
            {'us': 'M', 'v': 1000000},
            {'us': 'G', 'v': 1000000000},
            {'us': 'T', 'v': 1000000000000},
            {'us': 'P', 'v': 1000000000000000},
        ],
    }

    if not number:
        return number
    settings = settings or {}
    unit = settings['unit'] if 'unit' in settings else 'B'
    base = settings['base'] if 'base' in settings else 2

    new_locale = settings['locale'] if 'locale' in settings else ''

    if base != 2 and base != 10:
        return encode_value(number) + unit

    fixed = settings['fixed']

    unitMapping = unitBaseMapping[base]
    for mapping in reversed(unitMapping):
        suffix = mapping['us']
        startingValue = mapping['v']
        if number < startingValue:
            continue

        formatted = float(number) / startingValue
        formatted = format_number(formatted, fixed, new_locale)
        return formatted + suffix + unit

    formatted_number = format_number(number, fixed, new_locale)
    return formatted_number + unit


def format_number(number, fixed, format_locale):
    """
    Format the number based on format_locale passed.
    """

    # get the current locale
    current_locale = locale.getlocale()
    new_locale = ''
    # set passed locale and set new_locale to same value.
    if format_locale:
        new_locale = locale.setlocale(locale.LC_ALL, format_locale)

    # Based on type of number use the correct formatter
    if isinstance(number, float):
        if fixed:
            formatted = locale.format('%' + '.%df' % fixed, number, True)
        else:
            formatted = locale.format('%f', number, True)
    if isinstance(number, int):
        formatted = locale.format('%d', number, True)
    # After formatting is done as per locale, reset the locale if changed.
    if new_locale and not current_locale[0] and not current_locale[1]:
        locale.setlocale(locale.LC_ALL, 'C')
    elif new_locale:
        locale.setlocale(
            locale.LC_ALL, current_locale[0] + '.' + current_locale[1])

    return formatted
