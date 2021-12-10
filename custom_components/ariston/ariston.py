"""Suppoort for Ariston."""
import copy
import json
import logging
import math
import os
import re
import threading
import time
from typing import Union
import requests
from requests.models import StreamConsumedError


class AristonHandler:
    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Ariston NET Remotethermo API

    'username' - mandatory username;

    'password' - mandatory password;

    'sensors' - list of wanted sensors to be monitored.
    API automatically filters out requests based on this list to reduce amount of unique requests towards the server
    and thus reduce a period to update the data.
     from the allowed list of sensors:
        - 'account_ch_gas' - gas use for CH.
        - 'account_ch_electricity' - electricity use for CH.
        - 'account_dhw_gas' - gas use for DHW.
        - 'account_dhw_electricity' - electricity use for DHW.
        - 'ch_antifreeze_temperature' - atifreeze temperature for CH.
        - 'ch_mode' - CH mode.
        - 'ch_set_temperature' - CH temperature set as a target.
        - 'ch_comfort_temperature' - CH comfort temperature.
        - 'ch_economy_temperature' - CH economy temperature.
        - 'ch_detected_temperature' - CH detected room temperature.
        - 'ch_program' - CH program information.
        - 'ch_pilot' - CH pilot status.
        - 'ch_auto_function' - CH auto function.
        - 'ch_flame' - CH flame.
        - 'ch_water_temperature' - CH water temperature.
        - 'cooling_last_24h' - energy use for pump cooling in a day.
        - 'cooling_last_7d' - energy use for pump cooling in a week.
        - 'cooling_last_30d' - energy use for pump cooling in a month.
        - 'cooling_last_365d' - energy use for pump cooling in a year.
        - 'cooling_last_24h_list' - energy use for pump cooling in a day with periods.
        - 'cooling_last_7d_list' - energy use for pump cooling in a week with periods.
        - 'cooling_last_30d_list' - energy use for pump cooling in a month with periods.
        - 'cooling_last_365d_list' - energy use for pump cooling in a year with periods.
        - 'errors' - list of active errors.
        - 'errors_count' - number of active errors
        - 'dhw_comfort_function' - DHW comfort function.
        - 'dhw_mode' - DHW mode.
        - 'dhw_program' - DHW program information.
        - 'dhw_set_temperature' - DHW temperature set as a target.
        - 'dhw_storage_temperature' - DHW storeage probe temperature.
        - 'dhw_comfort_temperature' - DHW comfort temperature.
        - 'dhw_economy_temperature' - DHW economy temperature.
        - 'dhw_thermal_cleanse_function' - DHW thermal cleanse function.
        - 'dhw_thermal_cleanse_cycle' - DHW thermal cleanse cycle.
        - 'dhw_flame' - approximated DHW flame status.
        - 'heating_last_24h' - energy use for CH in a day.
        - 'heating_last_7d' - energy use for CH in a week.
        - 'heating_last_30d' - energy use for CH in a month.
        - 'heating_last_365d' - energy use for CH in a year.
        - 'heating_last_24h_list' - energy use for CH in a day with periods.
        - 'heating_last_7d_list' - energy use for CH in a week with periods.
        - 'heating_last_30d_list' - energy use for CH in a month with periods.
        - 'heating_last_365d_list' - energy use for CH in a year with periods.
        - 'mode' - general mode.
        - 'outside_temperature' - outside temperature.
        - 'signal_strength' - signal strength.
        - 'water_last_24h' - energy use for DHW in a day.
        - 'water_last_7d' - energy use for DHW in a week.
        - 'water_last_30d' - energy use for DHW in a month.
        - 'water_last_365d' - energy use for DHW in a year.
        - 'water_last_24h_list' - energy use for DHW in a day with periods.
        - 'water_last_7d_list' - energy use for DHW in a week with periods.
        - 'water_last_30d_list' - energy use for DHW in a month with periods.
        - 'water_last_365d_list' - energy use for DHW in a year with periods.
        - 'units' - indicates if metric or imperial units to be used.
        - 'gas_type' - type of gas.
        - 'gas_cost' - gas cost.
        - 'electricity_cost' - electricity cost.
        - 'flame' - CH or DHW flame detcted.
        - 'heat_pump' - heating pump.
        - 'holiday_mode' - holiday mode.
        - 'internet_time' - internet time.
        - 'internet_weather' - internet weather.
        - API specific 'update' - API update is available.
        - API specific 'online_version' - API version online.

    'retries' - number of retries to set the data;

    'polling' - defines multiplication factor for waiting periods to get or set the data;

    'store_file' - indicates if HTTP and internal data to be stored as files for troubleshooting purposes;

    'store_folder' - folder to store HTTP and internal data to. If empty string is used, then current working directory
    is used with a folder 'http_logs' within it.

    'units' - 'metric' or 'imperial' or 'auto'.
    Value 'auto' creates additional request towards the server and as a result increases period to update other sensors.

    'ch_and_dhw' - indicates if CH and DHW heating can work at the same time (usually valve allows to use one);

    'dhw_unknown_as_on' - indicates if to assume 'dhw_flame' as being True if cannot be identified.

    'logging_level' - defines level of logging - allowed values [CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET=(default)]

    'zones' - specifies number of monitored zones. By default is 1. For senors, which depend on zones,
              new sensor values shall be set (ending with _zone_2 and _zone_3), otherwise they shall remain unset.

    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    _VERSION = "1.0.48"

    _LOGGER = logging.getLogger(__name__)
    _LEVEL_CRITICAL = "CRITICAL"
    _LEVEL_ERROR = "ERROR"
    _LEVEL_WARNING = "WARNING"
    _LEVEL_INFO = "INFO"
    _LEVEL_DEBUG = "DEBUG"
    _LEVEL_NOTSET = "NOTSET"

    _LOGGING_LEVELS = [
        _LEVEL_CRITICAL,
        _LEVEL_ERROR,
        _LEVEL_WARNING,
        _LEVEL_INFO,
        _LEVEL_DEBUG,
        _LEVEL_NOTSET
    ]

    _TEMPLATE_ZONE_VAR_NAME = '{}_ZONE_{}'
    _TEMPLATE_ZONE_VAR_VALUE = '{}_zone_{}'
    _SETS_MODIFIED_WITH_ZONES = dict()

    def duplicate_set_per_zone(var_name, locals_dict, zone_params, zone_start, zone_stop, zone_template):
        for param in zone_params:
            check_key = locals_dict[param]
            if check_key in locals_dict[var_name]:
                if var_name not in locals_dict['_SETS_MODIFIED_WITH_ZONES']:
                    locals_dict['_SETS_MODIFIED_WITH_ZONES'][var_name] = list()
                locals_dict['_SETS_MODIFIED_WITH_ZONES'][var_name].append(check_key)
                for zone in range(zone_start, zone_stop + 1):
                    locals_dict[var_name].add(zone_template.lower().format(check_key, zone))


    _ZONE_1 = '_zone_1'
    _ZONE_2 = '_zone_2'
    _ZONE_3 = '_zone_3'

    _ZONE_ORDER = [_ZONE_1, _ZONE_2, _ZONE_3]

    _ADD_ZONES_START = 2
    _ADD_ZONES_STOP = 3

    _PARAM_ACCOUNT_CH_GAS = "account_ch_gas"
    _PARAM_ACCOUNT_CH_ELECTRICITY = "account_ch_electricity"
    _PARAM_ACCOUNT_DHW_GAS = "account_dhw_gas"
    _PARAM_ACCOUNT_DHW_ELECTRICITY = "account_dhw_electricity"
    _PARAM_CH_ANTIFREEZE_TEMPERATURE = "ch_antifreeze_temperature"
    _PARAM_CH_MODE = "ch_mode"
    _PARAM_CH_SET_TEMPERATURE = "ch_set_temperature"
    _PARAM_CH_COMFORT_TEMPERATURE = "ch_comfort_temperature"
    _PARAM_CH_ECONOMY_TEMPERATURE = "ch_economy_temperature"
    _PARAM_CH_DETECTED_TEMPERATURE = "ch_detected_temperature"
    _PARAM_CH_PROGRAM = "ch_program"
    _PARAM_CH_WATER_TEMPERATURE = "ch_water_temperature"
    _PARAM_COOLING_LAST_24H = "cooling_last_24h"
    _PARAM_COOLING_LAST_7D = "cooling_last_7d"
    _PARAM_COOLING_LAST_30D = "cooling_last_30d"
    _PARAM_COOLING_LAST_365D = "cooling_last_365d"
    _PARAM_COOLING_LAST_24H_LIST = "cooling_last_24h_list"
    _PARAM_COOLING_LAST_7D_LIST = "cooling_last_7d_list"
    _PARAM_COOLING_LAST_30D_LIST = "cooling_last_30d_list"
    _PARAM_COOLING_LAST_365D_LIST = "cooling_last_365d_list"
    _PARAM_COOLING_TODAY = "cooling_today"
    _PARAM_ERRORS = "errors"
    _PARAM_ERRORS_COUNT = "errors_count"
    _PARAM_DHW_COMFORT_FUNCTION = "dhw_comfort_function"
    _PARAM_DHW_MODE = "dhw_mode"
    _PARAM_DHW_PROGRAM = "dhw_program"
    _PARAM_DHW_SET_TEMPERATURE = "dhw_set_temperature"
    _PARAM_DHW_STORAGE_TEMPERATURE = "dhw_storage_temperature"
    _PARAM_DHW_COMFORT_TEMPERATURE = "dhw_comfort_temperature"
    _PARAM_DHW_ECONOMY_TEMPERATURE = "dhw_economy_temperature"
    _PARAM_HEATING_LAST_24H = "heating_last_24h"
    _PARAM_HEATING_LAST_7D = "heating_last_7d"
    _PARAM_HEATING_LAST_30D = "heating_last_30d"
    _PARAM_HEATING_LAST_365D = "heating_last_365d"
    _PARAM_HEATING_LAST_24H_LIST = "heating_last_24h_list"
    _PARAM_HEATING_LAST_7D_LIST = "heating_last_7d_list"
    _PARAM_HEATING_LAST_30D_LIST = "heating_last_30d_list"
    _PARAM_HEATING_LAST_365D_LIST = "heating_last_365d_list"
    _PARAM_HEATING_TODAY = "heating_today"
    _PARAM_MODE = "mode"
    _PARAM_OUTSIDE_TEMPERATURE = "outside_temperature"
    _PARAM_SIGNAL_STRENGTH = "signal_strength"
    _PARAM_WATER_LAST_24H = "water_last_24h"
    _PARAM_WATER_LAST_7D = "water_last_7d"
    _PARAM_WATER_LAST_30D = "water_last_30d"
    _PARAM_WATER_LAST_365D = "water_last_365d"
    _PARAM_WATER_LAST_24H_LIST = "water_last_24h_list"
    _PARAM_WATER_LAST_7D_LIST = "water_last_7d_list"
    _PARAM_WATER_LAST_30D_LIST = "water_last_30d_list"
    _PARAM_WATER_LAST_365D_LIST = "water_last_365d_list"
    _PARAM_WATER_TODAY = "water_today"
    _PARAM_UNITS = "units"
    _PARAM_THERMAL_CLEANSE_CYCLE = "dhw_thermal_cleanse_cycle"
    _PARAM_GAS_TYPE = "gas_type"
    _PARAM_GAS_COST = "gas_cost"
    _PARAM_ELECTRICITY_COST = "electricity_cost"
    _PARAM_CH_AUTO_FUNCTION = "ch_auto_function"
    _PARAM_CH_FLAME = "ch_flame"
    _PARAM_DHW_FLAME = "dhw_flame"
    _PARAM_FLAME = "flame"
    _PARAM_HEAT_PUMP = "heat_pump"
    _PARAM_HOLIDAY_MODE = "holiday_mode"
    _PARAM_INTERNET_TIME = "internet_time"
    _PARAM_INTERNET_WEATHER = "internet_weather"
    _PARAM_THERMAL_CLEANSE_FUNCTION = "dhw_thermal_cleanse_function"
    _PARAM_CH_PILOT = "ch_pilot"
    _PARAM_UPDATE = "update"
    _PARAM_ONLINE_VERSION = "online_version"

    _ZONE_PARAMETERS ={
        "_PARAM_CH_MODE",
        "_PARAM_CH_SET_TEMPERATURE",
        "_PARAM_CH_COMFORT_TEMPERATURE",
        "_PARAM_CH_ECONOMY_TEMPERATURE",
        "_PARAM_CH_DETECTED_TEMPERATURE",
        "_PARAM_CH_ANTIFREEZE_TEMPERATURE",
        "_PARAM_CH_FLAME",
        "_PARAM_CH_PROGRAM"
    }
    # Create variables for zones
    for param in _ZONE_PARAMETERS:
        check_key = locals()[param]
        for zone in range(_ADD_ZONES_START, _ADD_ZONES_STOP + 1):
            locals()[_TEMPLATE_ZONE_VAR_NAME.format(param, zone)] = _TEMPLATE_ZONE_VAR_VALUE.format(locals()[param], zone)

    # Units of measurement
    _UNIT_METRIC = "metric"
    _UNIT_IMPERIAL = "imperial"
    _UNIT_AUTO = "auto"

    _VALUE = "value"
    _UNITS = "units"

    # parameter values
    _VAL_WINTER = "winter"
    _VAL_SUMMER = "summer"
    _VAL_OFF = "off"
    _VAL_HEATING_ONLY = "heating_only"
    _VAL_COOLING = "cooling"
    _VAL_MANUAL = "manual"
    _VAL_PROGRAM = "program"
    _VAL_UNKNOWN = "unknown"
    _VAL_OFFLINE = "offline"
    _VAL_UNSUPPORTED = "unsupported"
    _VAL_AVAILABLE = "available"
    _VAL_DISABLED = "disabled"
    _VAL_TIME_BASED = "time_based"
    _VAL_ALWAYS_ACTIVE = "always_active"
    _VAL_METRIC = "metric"
    _VAL_IMPERIAL = "imperial"
    _VAL_AUTO = "auto"
    _VAL_DEFAULT = "default"

    _FILE_FOLDER = "http_logs"
    _ARISTON_URL = "https://www.ariston-net.remotethermo.com"
    _GITHUB_LATEST_RELEASE = \
        'https://pypi.python.org/pypi/aristonremotethermo/json'

    _DEFAULT_HVAC = _VAL_SUMMER
    _DEFAULT_POWER_ON = _VAL_SUMMER
    _DEFAULT_NAME = "Ariston"
    _DEFAULT_MAX_RETRIES = 1
    _DEFAULT_TIME = "00:00"
    _DEFAULT_MODES = [0, 1, 5]
    _DEFAULT_CH_MODES = [2, 3]
    _MAX_ERRORS = 10
    _MAX_ERRORS_TIMER_EXTEND = 7
    _MAX_ZERO_TOLERANCE = 10
    _MAX_ZERO_TOLERANCE_TODAY_PARAMS = 5
    _HTTP_DELAY_MULTIPLY = 3
    _HTTP_TIMER_SET_LOCK = 25
    _HTTP_TIMER_SET_WAIT = 30
    _HTTP_TIMEOUT_LOGIN = 5.0
    _HTTP_TIMEOUT_GET_LONG = 18.0
    _HTTP_TIMEOUT_GET_MEDIUM = 10.0
    _HTTP_TIMEOUT_GET_SHORT = 6.0
    _HTTP_PARAM_DELAY = 30.0

    _TODAY_SENSORS = {_PARAM_COOLING_TODAY, _PARAM_HEATING_TODAY, _PARAM_WATER_TODAY}

    # Conversions between parameters
    _MODE_TO_VALUE = {_VAL_WINTER: 1, _VAL_SUMMER: 0, _VAL_OFF: 5, _VAL_HEATING_ONLY: 2, _VAL_COOLING: 3}
    _VALUE_TO_MODE = {value: key for (key, value) in _MODE_TO_VALUE.items()}

    _CH_MODE_TO_VALUE = {_VAL_MANUAL: 2, _VAL_PROGRAM: 3, _VAL_UNKNOWN: 0}
    _VALUE_TO_CH_MODE = {value: key for (key, value) in _CH_MODE_TO_VALUE.items()}

    _DHW_MODE_TO_VALUE = {_VAL_MANUAL: 2, _VAL_PROGRAM: 1, _VAL_DEFAULT: 0}
    _VALUE_TO_DHW_MODE = {value: key for (key, value) in _DHW_MODE_TO_VALUE.items()}

    _DHW_COMFORT_FUNCT_TO_VALUE = {_VAL_DISABLED: 0, _VAL_TIME_BASED: 1, _VAL_ALWAYS_ACTIVE: 2}
    _DHW_COMFORT_VALUE_TO_FUNCT = {value: key for (key, value) in _DHW_COMFORT_FUNCT_TO_VALUE.items()}

    _UNIT_TO_VALUE = {_VAL_METRIC: 0, _VAL_IMPERIAL: 1}
    _VALUE_TO_UNIT = {value: key for (key, value) in _UNIT_TO_VALUE.items()}

    _PARAM_STRING_TO_VALUE = {"true": 1, "false": 0}

    _UNKNOWN_TEMP = 0.0
    _UNKNOWN_UNITS = 3276
    _UNKNOWN_TEMPERATURES = [0, 3276]
    _INVALID_STORAGE_TEMP = 0
    _DAYS_OF_WEEK = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

    # Ariston parameter codes in the menu
    _ARISTON_DHW_COMFORT_TEMP = "U6_9_0"
    _ARISTON_DHW_COMFORT_FUNCTION = "U6_9_2"
    _ARISTON_DHW_TIME_PROG_COMFORT = "U6_9_1_0_0"
    _ARISTON_DHW_TIME_PROG_ECONOMY = "U6_9_1_0_1"
    _ARISTON_SIGNAL_STRENGHT = "U6_16_5"
    _ARISTON_INTERNET_TIME = "U6_16_6"
    _ARISTON_INTERNET_WEATHER = "U6_16_7"
    _ARISTON_CH_COMFORT_TEMP = "U6_3_1_0_0"
    _ARISTON_CH_COMFORT_TEMP_ZONE_2 = "U6_3_1_1_0"
    _ARISTON_CH_COMFORT_TEMP_ZONE_3 = "U6_3_1_2_0"
    _ARISTON_CH_ECONOMY_TEMP = "U6_3_1_0_1"
    _ARISTON_CH_ECONOMY_TEMP_ZONE_2 = "U6_3_1_1_1"
    _ARISTON_CH_ECONOMY_TEMP_ZONE_3 = "U6_3_1_2_1"
    _ARISTON_CH_AUTO_FUNCTION = "U6_3_3"
    _ARISTON_CH_WATER_TEMPERATURE = "U6_3_0_0"
    _ARISTON_THERMAL_CLEANSE_FUNCTION = "U6_9_5_0"
    _ARISTON_THERMAL_CLEANSE_CYCLE = "U6_9_5_1"
    _ARISTON_S_W_FUNCTION_ACTIVATION = "U6_3_5_0_0"
    _ARISTON_S_W_FUNCTION_ACTIVATION_ZONE_2 = "U6_3_5_1_0"
    _ARISTON_S_W_FUNCTION_ACTIVATION_ZONE_3 = "U6_3_5_2_0"
    _ARISTON_S_W_TEMPERATURE_THRESHOLD = "U6_3_5_0_1"
    _ARISTON_S_W_TEMPERATURE_THRESHOLD_ZONE_2 = "U6_3_5_1_1"
    _ARISTON_S_W_TEMPERATURE_THRESHOLD_ZONE_3 = "U6_3_5_2_1"
    _ARISTON_S_W_DELAY_TIME = "U6_3_5_0_2"
    _ARISTON_S_W_DELAY_TIME_ZONE_2 = "U6_3_5_1_2"
    _ARISTON_S_W_DELAY_TIME_ZONE_3 = "U6_3_5_2_2"
    _ARISTON_PROGRAM_MANUAL_ZONE_1 = "U0_0"
    _ARISTON_PROGRAM_MANUAL_ZONE_2 = "U0_1"
    _ARISTON_PROGRAM_MANUAL_ZONE_3 = "U0_2"
    _ARISTON_PROGRAM_MANUAL_ZONE_4 = "U0_3"
    _ARISTON_PROGRAM_MANUAL_ZONE_5 = "U0_4"
    _ARISTON_PROGRAM_MANUAL_ZONE_6 = "U0_5"
    _ARISTON_PROGRAM_MANUAL_DHW = "U0_6"
    _ARISTON_PV_OFFSET_DHW = "U6_15_2"
    _ARISTON_QUITET_MODE_HHP = "U6_15_0_1"
    _ARISTON_HYBRID_MODE = "U6_12_1"
    _ARISTON_ENERGY_MANAGER_LOGIC = "U6_12_0"
    _ARISTON_BUFFER_ACTIVATION = "U6_10_0"
    _ARISTON_BUFFER_COMFORT_SETPOINT = "U6_10_1"
    _ARISTON_BUFFER_SETPOINT_HEATING = "U6_10_2"
    _ARISTON_BUFFER_SETPOINT_MODE = "U6_10_5"
    _ARISTON_DHW_TANK_CHARGE_MODE = "U6_9_3"
    _ARISTON_CH_FIXED_TEMP = "U6_3_0_1"
    _ARISTON_CH_FIXED_TEMP_ZONE_2 = "U6_3_0_3"
    _ARISTON_CH_FIXED_TEMP_ZONE_3 = "U6_3_0_5"

    _REQUEST_GET_MAIN = "_get_main"
    _REQUEST_GET_CH = "_get_ch"
    _REQUEST_GET_DHW = "_get_dhw"
    _REQUEST_GET_ERROR = "_get_error"
    _REQUEST_GET_GAS = "_get_gas"
    _REQUEST_GET_OTHER = "_get_param"
    _REQUEST_GET_UNITS = "_get_units"
    _REQUEST_GET_CURRENCY = "_get_currency"
    _REQUEST_GET_VERSION = "_get_version"
    _REQUEST_SET_MAIN = "_set_main"
    _REQUEST_SET_OTHER = "_set_param"
    _REQUEST_SET_UNITS = "_set_units"


    _PARAM_TO_ARISTON = {
        _PARAM_INTERNET_TIME: _ARISTON_INTERNET_TIME,
        _PARAM_INTERNET_WEATHER: _ARISTON_INTERNET_WEATHER,
        _PARAM_THERMAL_CLEANSE_FUNCTION: _ARISTON_THERMAL_CLEANSE_FUNCTION,
        _PARAM_CH_AUTO_FUNCTION: _ARISTON_CH_AUTO_FUNCTION,
        _PARAM_DHW_COMFORT_FUNCTION: _ARISTON_DHW_COMFORT_FUNCTION,
        _PARAM_CH_COMFORT_TEMPERATURE: _ARISTON_CH_COMFORT_TEMP,
        _PARAM_CH_ECONOMY_TEMPERATURE: _ARISTON_CH_ECONOMY_TEMP,
        _PARAM_SIGNAL_STRENGTH: _ARISTON_SIGNAL_STRENGHT,
        _PARAM_THERMAL_CLEANSE_CYCLE: _ARISTON_THERMAL_CLEANSE_CYCLE,
        _PARAM_CH_WATER_TEMPERATURE: _ARISTON_CH_WATER_TEMPERATURE,
        _PARAM_DHW_COMFORT_TEMPERATURE: _ARISTON_DHW_TIME_PROG_COMFORT,
        _PARAM_DHW_ECONOMY_TEMPERATURE: _ARISTON_DHW_TIME_PROG_ECONOMY,
    }
    # Create mappings for zones
    var_name = '_PARAM_TO_ARISTON'
    for param in _ZONE_PARAMETERS:
        check_key = locals()[param]
        if check_key in locals()[var_name]:
            value_var_name = ""
            for key in set(locals().keys()):
                if key.startswith('_ARISTON_') and locals()[key] == locals()[var_name][check_key]:
                    value_var_name = key
            for zone in range(_ADD_ZONES_START, _ADD_ZONES_STOP + 1):
                locals()[var_name][_TEMPLATE_ZONE_VAR_VALUE.format(check_key, zone)] = locals()[_TEMPLATE_ZONE_VAR_NAME.format(value_var_name, zone)]

    _ARISTON_TO_PARAM = {value: key for (key, value) in _PARAM_TO_ARISTON.items()}

    _MENU_TO_SENSOR = {value.replace('U','').replace('_','.'): key for (key, value) in _PARAM_TO_ARISTON.items()}

    # Mapping of parameter to request
    _GET_REQUEST_CH_PROGRAM = {
        _PARAM_CH_PROGRAM
    }
    duplicate_set_per_zone('_GET_REQUEST_CH_PROGRAM', locals(), _ZONE_PARAMETERS, _ADD_ZONES_START, _ADD_ZONES_STOP, _TEMPLATE_ZONE_VAR_VALUE)
    _GET_REQUEST_CURRENCY = {
        _PARAM_GAS_TYPE,
        _PARAM_GAS_COST,
        _PARAM_ELECTRICITY_COST
    }
    duplicate_set_per_zone('_GET_REQUEST_CURRENCY', locals(), _ZONE_PARAMETERS, _ADD_ZONES_START, _ADD_ZONES_STOP, _TEMPLATE_ZONE_VAR_VALUE)
    _GET_REQUEST_DHW_PROGRAM = {
        _PARAM_DHW_PROGRAM
    }
    duplicate_set_per_zone('_GET_REQUEST_DHW_PROGRAM', locals(), _ZONE_PARAMETERS, _ADD_ZONES_START, _ADD_ZONES_STOP, _TEMPLATE_ZONE_VAR_VALUE)
    _GET_REQUEST_ERRORS = {
        _PARAM_ERRORS,
        _PARAM_ERRORS_COUNT
    }
    duplicate_set_per_zone('_GET_REQUEST_ERRORS', locals(), _ZONE_PARAMETERS, _ADD_ZONES_START, _ADD_ZONES_STOP, _TEMPLATE_ZONE_VAR_VALUE)
    _GET_REQUEST_GAS = {
        _PARAM_ACCOUNT_CH_GAS,
        _PARAM_ACCOUNT_CH_ELECTRICITY,
        _PARAM_ACCOUNT_DHW_GAS,
        _PARAM_ACCOUNT_DHW_ELECTRICITY,
        _PARAM_HEATING_LAST_24H,
        _PARAM_HEATING_LAST_7D,
        _PARAM_HEATING_LAST_30D,
        _PARAM_HEATING_LAST_365D,
        _PARAM_HEATING_LAST_24H_LIST,
        _PARAM_HEATING_LAST_7D_LIST,
        _PARAM_HEATING_LAST_30D_LIST,
        _PARAM_HEATING_LAST_365D_LIST,
        _PARAM_HEATING_TODAY,
        _PARAM_WATER_LAST_24H,
        _PARAM_WATER_LAST_7D,
        _PARAM_WATER_LAST_30D,
        _PARAM_WATER_LAST_365D,
        _PARAM_WATER_LAST_24H_LIST,
        _PARAM_WATER_LAST_7D_LIST,
        _PARAM_WATER_LAST_30D_LIST,
        _PARAM_WATER_LAST_365D_LIST,
        _PARAM_WATER_TODAY,
        _PARAM_COOLING_LAST_24H,
        _PARAM_COOLING_LAST_7D,
        _PARAM_COOLING_LAST_30D,
        _PARAM_COOLING_LAST_365D,
        _PARAM_COOLING_LAST_24H_LIST,
        _PARAM_COOLING_LAST_7D_LIST,
        _PARAM_COOLING_LAST_30D_LIST,
        _PARAM_COOLING_LAST_365D_LIST,
        _PARAM_COOLING_TODAY
    }
    duplicate_set_per_zone('_GET_REQUEST_GAS', locals(), _ZONE_PARAMETERS, _ADD_ZONES_START, _ADD_ZONES_STOP, _TEMPLATE_ZONE_VAR_VALUE)
    _GET_REQUEST_MAIN = {
        _PARAM_CH_DETECTED_TEMPERATURE,
        _PARAM_CH_ANTIFREEZE_TEMPERATURE,
        _PARAM_CH_MODE,
        _PARAM_CH_SET_TEMPERATURE,
        _PARAM_DHW_SET_TEMPERATURE,
        _PARAM_MODE,
        _PARAM_DHW_COMFORT_TEMPERATURE,
        _PARAM_DHW_ECONOMY_TEMPERATURE,
        _PARAM_DHW_STORAGE_TEMPERATURE,
        _PARAM_OUTSIDE_TEMPERATURE,
        _PARAM_DHW_MODE,
        _PARAM_HOLIDAY_MODE,
        _PARAM_HEAT_PUMP,
        _PARAM_CH_PILOT,
        _PARAM_CH_FLAME,
        _PARAM_DHW_FLAME,
        _PARAM_FLAME
    }
    duplicate_set_per_zone('_GET_REQUEST_MAIN', locals(), _ZONE_PARAMETERS, _ADD_ZONES_START, _ADD_ZONES_STOP, _TEMPLATE_ZONE_VAR_VALUE)
    _GET_REQUEST_PARAM = {
        _PARAM_INTERNET_TIME,
        _PARAM_INTERNET_WEATHER,
        _PARAM_THERMAL_CLEANSE_FUNCTION,
        _PARAM_CH_AUTO_FUNCTION,
        _PARAM_DHW_COMFORT_FUNCTION,
        _PARAM_CH_COMFORT_TEMPERATURE,
        _PARAM_CH_ECONOMY_TEMPERATURE,
        _PARAM_SIGNAL_STRENGTH,
        _PARAM_THERMAL_CLEANSE_CYCLE,
        _PARAM_CH_WATER_TEMPERATURE
    }
    duplicate_set_per_zone('_GET_REQUEST_PARAM', locals(), _ZONE_PARAMETERS, _ADD_ZONES_START, _ADD_ZONES_STOP, _TEMPLATE_ZONE_VAR_VALUE)
    _GET_REQUEST_UNITS = {
        _PARAM_UNITS
    }
    duplicate_set_per_zone('_GET_REQUEST_UNITS', locals(), _ZONE_PARAMETERS, _ADD_ZONES_START, _ADD_ZONES_STOP, _TEMPLATE_ZONE_VAR_VALUE)
    _GET_REQUEST_VERSION = {
        _PARAM_UPDATE,
        _PARAM_ONLINE_VERSION
    }
    duplicate_set_per_zone('_GET_REQUEST_VERSION', locals(), _ZONE_PARAMETERS, _ADD_ZONES_START, _ADD_ZONES_STOP, _TEMPLATE_ZONE_VAR_VALUE)

    # Supported sensors list
    _SENSOR_LIST = {*_GET_REQUEST_CH_PROGRAM,
                    *_GET_REQUEST_DHW_PROGRAM,
                    *_GET_REQUEST_CURRENCY,
                    *_GET_REQUEST_ERRORS,
                    *_GET_REQUEST_GAS,
                    *_GET_REQUEST_MAIN,
                    *_GET_REQUEST_PARAM,
                    *_GET_REQUEST_UNITS,
                    *_GET_REQUEST_VERSION}


    _MAP_ZONE_TO_ORIGINAL_PARAM = dict()
    _SUB_ORIGINAL = 'original'
    _SUB_ZONE = 'zone'
    # Create mapping of variables for zones
    for sensor in _SENSOR_LIST:
        _MAP_ZONE_TO_ORIGINAL_PARAM[sensor] = {
            _SUB_ORIGINAL: sensor,
            _SUB_ZONE: _ZONE_1
        }
    var_name = '_MAP_ZONE_TO_ORIGINAL_PARAM'
    for param in _ZONE_PARAMETERS:
        check_key = locals()[param]
        for zone in range(_ADD_ZONES_START, _ADD_ZONES_STOP + 1):
            locals()[var_name][_TEMPLATE_ZONE_VAR_VALUE.format(check_key, zone)] = {
                _SUB_ORIGINAL: check_key,
                _SUB_ZONE: _TEMPLATE_ZONE_VAR_VALUE.format("", zone)
            }
    _MAP_PARAM_NAME_TO_ZONE_PARAM_NAME = dict()
    _MAP_PARAM_NAME_TO_ZONE_NUMBER = dict()
    for sensor in _SENSOR_LIST:
        if _MAP_ZONE_TO_ORIGINAL_PARAM[sensor][_SUB_ORIGINAL] == sensor:
            _MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[sensor] = dict()
            in_zone = False
            for param in _ZONE_PARAMETERS:
                check_key = locals()[param]
                if sensor == check_key:
                    in_zone = True
            for zone in _ZONE_ORDER:
                if zone == _ZONE_1 or not in_zone:
                    _MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[sensor][zone] = sensor
                    _MAP_PARAM_NAME_TO_ZONE_NUMBER[sensor] = _ZONE_1
                else:
                    _MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[sensor][zone] = sensor + zone
                    _MAP_PARAM_NAME_TO_ZONE_NUMBER[sensor + zone] = zone
    

    _SET_REQUEST_MAIN = {
        _PARAM_CH_DETECTED_TEMPERATURE,
        _PARAM_CH_ANTIFREEZE_TEMPERATURE,
        _PARAM_CH_MODE,
        _PARAM_CH_SET_TEMPERATURE,
        _PARAM_DHW_SET_TEMPERATURE,
        _PARAM_MODE,
        _PARAM_DHW_STORAGE_TEMPERATURE,
        _PARAM_OUTSIDE_TEMPERATURE,
        _PARAM_DHW_MODE,
        _PARAM_HOLIDAY_MODE,
        _PARAM_HEAT_PUMP,
        _PARAM_CH_PILOT,
        _PARAM_CH_FLAME,
        _PARAM_FLAME
    }
    duplicate_set_per_zone('_SET_REQUEST_MAIN', locals(), _ZONE_PARAMETERS, _ADD_ZONES_START, _ADD_ZONES_STOP, _TEMPLATE_ZONE_VAR_VALUE)
    _SET_REQUEST_PARAM = {
        _PARAM_INTERNET_TIME,
        _PARAM_INTERNET_WEATHER,
        _PARAM_THERMAL_CLEANSE_FUNCTION,
        _PARAM_CH_AUTO_FUNCTION,
        _PARAM_DHW_COMFORT_FUNCTION,
        _PARAM_DHW_COMFORT_TEMPERATURE,
        _PARAM_DHW_ECONOMY_TEMPERATURE,
        _PARAM_CH_COMFORT_TEMPERATURE,
        _PARAM_CH_ECONOMY_TEMPERATURE,
        _PARAM_SIGNAL_STRENGTH,
        _PARAM_THERMAL_CLEANSE_CYCLE,
        _PARAM_CH_WATER_TEMPERATURE
    }
    duplicate_set_per_zone('_SET_REQUEST_PARAM', locals(), _ZONE_PARAMETERS, _ADD_ZONES_START, _ADD_ZONES_STOP, _TEMPLATE_ZONE_VAR_VALUE)
    _SET_REQUEST_UNITS = {
        _PARAM_UNITS
    }
    duplicate_set_per_zone('_SET_REQUEST_UNITS', locals(), _ZONE_PARAMETERS, _ADD_ZONES_START, _ADD_ZONES_STOP, _TEMPLATE_ZONE_VAR_VALUE)
    _SENSOR_SET_LIST = {
        _PARAM_MODE,
        _PARAM_CH_MODE,
        _PARAM_CH_SET_TEMPERATURE,
        _PARAM_CH_COMFORT_TEMPERATURE,
        _PARAM_CH_ECONOMY_TEMPERATURE,
        _PARAM_CH_AUTO_FUNCTION,
        _PARAM_DHW_SET_TEMPERATURE,
        _PARAM_DHW_COMFORT_TEMPERATURE,
        _PARAM_DHW_ECONOMY_TEMPERATURE,
        _PARAM_DHW_MODE,
        _PARAM_DHW_COMFORT_FUNCTION,
        _PARAM_INTERNET_TIME,
        _PARAM_INTERNET_WEATHER,
        _PARAM_UNITS,
        _PARAM_THERMAL_CLEANSE_CYCLE,
        _PARAM_THERMAL_CLEANSE_FUNCTION,
        _PARAM_CH_WATER_TEMPERATURE
    }
    duplicate_set_per_zone('_SENSOR_SET_LIST', locals(), _ZONE_PARAMETERS, _ADD_ZONES_START, _ADD_ZONES_STOP, _TEMPLATE_ZONE_VAR_VALUE)

    _CLASS_LOCALS = locals()

    def _get_request_for_parameter(self, data):
        if data in self._GET_REQUEST_CH_PROGRAM:
            return self._REQUEST_GET_CH
        elif data in self._GET_REQUEST_CURRENCY:
            return self._REQUEST_GET_CURRENCY
        elif data in self._GET_REQUEST_DHW_PROGRAM:
            return self._REQUEST_GET_DHW
        elif data in self._GET_REQUEST_ERRORS:
            return self._REQUEST_GET_ERROR
        elif data in self._GET_REQUEST_GAS:
            return self._REQUEST_GET_GAS
        elif data in self._GET_REQUEST_PARAM:
            return self._REQUEST_GET_OTHER
        elif data in self._GET_REQUEST_UNITS:
            return self._REQUEST_GET_UNITS
        elif data in self._GET_REQUEST_VERSION:
            return self._REQUEST_GET_VERSION
        return self._REQUEST_GET_MAIN

    def _set_request_for_parameter(self, data):
        if data in self._SET_REQUEST_PARAM:
            return self._REQUEST_SET_OTHER
        elif data in self._SET_REQUEST_UNITS:
            return self._REQUEST_SET_UNITS
        return self._REQUEST_SET_MAIN

    def _update_units(self):
        if self._ariston_sensors[self._PARAM_UNITS][self._VALUE] == self._VAL_IMPERIAL:
            self._ariston_sensors[self._PARAM_CH_ANTIFREEZE_TEMPERATURE][self._UNITS] = "°F"
            self._ariston_sensors[self._PARAM_CH_DETECTED_TEMPERATURE][self._UNITS] = "°F"
            self._ariston_sensors[self._PARAM_CH_SET_TEMPERATURE][self._UNITS] = "°F"
            self._ariston_sensors[self._PARAM_CH_COMFORT_TEMPERATURE][self._UNITS] = "°F"
            self._ariston_sensors[self._PARAM_CH_ECONOMY_TEMPERATURE][self._UNITS] = "°F"
            self._ariston_sensors[self._PARAM_CH_WATER_TEMPERATURE][self._UNITS] = "°F"
            self._ariston_sensors[self._PARAM_DHW_SET_TEMPERATURE][self._UNITS] = "°F"
            self._ariston_sensors[self._PARAM_DHW_STORAGE_TEMPERATURE][self._UNITS] = "°F"
            self._ariston_sensors[self._PARAM_DHW_COMFORT_TEMPERATURE][self._UNITS] = "°F"
            self._ariston_sensors[self._PARAM_DHW_ECONOMY_TEMPERATURE][self._UNITS] = "°F"
            self._ariston_sensors[self._PARAM_OUTSIDE_TEMPERATURE][self._UNITS] = "°F"
            self._ariston_sensors[self._PARAM_ACCOUNT_CH_GAS][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_ACCOUNT_DHW_GAS][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_ACCOUNT_CH_ELECTRICITY][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_ACCOUNT_DHW_ELECTRICITY][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_HEATING_LAST_24H][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_HEATING_LAST_7D][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_HEATING_LAST_30D][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_HEATING_LAST_365D][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_HEATING_TODAY][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_WATER_LAST_24H][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_WATER_LAST_7D][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_WATER_LAST_30D][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_WATER_LAST_365D][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_WATER_TODAY][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_SIGNAL_STRENGTH][self._UNITS] = '%'
            self._ariston_sensors[self._PARAM_THERMAL_CLEANSE_CYCLE][self._UNITS] = 'h'
            self._ariston_sensors[self._PARAM_COOLING_LAST_24H][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_COOLING_LAST_7D][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_COOLING_LAST_30D][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_COOLING_LAST_365D][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_COOLING_TODAY][self._UNITS] = 'kBtuh'
        elif self._ariston_sensors[self._PARAM_UNITS][self._VALUE] == self._VAL_METRIC:
            self._ariston_sensors[self._PARAM_CH_ANTIFREEZE_TEMPERATURE][self._UNITS] = "°C"
            self._ariston_sensors[self._PARAM_CH_DETECTED_TEMPERATURE][self._UNITS] = "°C"
            self._ariston_sensors[self._PARAM_CH_SET_TEMPERATURE][self._UNITS] = "°C"
            self._ariston_sensors[self._PARAM_CH_COMFORT_TEMPERATURE][self._UNITS] = "°C"
            self._ariston_sensors[self._PARAM_CH_ECONOMY_TEMPERATURE][self._UNITS] = "°C"
            self._ariston_sensors[self._PARAM_CH_WATER_TEMPERATURE][self._UNITS] = "°C"
            self._ariston_sensors[self._PARAM_DHW_SET_TEMPERATURE][self._UNITS] = "°C"
            self._ariston_sensors[self._PARAM_DHW_STORAGE_TEMPERATURE][self._UNITS] = "°C"
            self._ariston_sensors[self._PARAM_DHW_COMFORT_TEMPERATURE][self._UNITS] = "°C"
            self._ariston_sensors[self._PARAM_DHW_ECONOMY_TEMPERATURE][self._UNITS] = "°C"
            self._ariston_sensors[self._PARAM_OUTSIDE_TEMPERATURE][self._UNITS] = "°C"
            self._ariston_sensors[self._PARAM_ACCOUNT_CH_GAS][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_ACCOUNT_DHW_GAS][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_ACCOUNT_CH_ELECTRICITY][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_ACCOUNT_DHW_ELECTRICITY][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_HEATING_LAST_24H][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_HEATING_LAST_7D][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_HEATING_LAST_30D][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_HEATING_LAST_365D][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_HEATING_TODAY][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_WATER_LAST_24H][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_WATER_LAST_7D][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_WATER_LAST_30D][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_WATER_LAST_365D][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_WATER_TODAY][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_SIGNAL_STRENGTH][self._UNITS] = '%'
            self._ariston_sensors[self._PARAM_THERMAL_CLEANSE_CYCLE][self._UNITS] = 'h'
            self._ariston_sensors[self._PARAM_COOLING_LAST_24H][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_COOLING_LAST_7D][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_COOLING_LAST_30D][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_COOLING_LAST_365D][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_COOLING_TODAY][self._UNITS] = 'kWh'
        for key in self._ariston_sensors.keys():
            for param_name in self._ZONE_PARAMETERS:
                param_key = self._CLASS_LOCALS[param_name]
                if key == param_key:
                    for zone in range(self._ADD_ZONES_START, self._ADD_ZONES_STOP + 1):
                        self._ariston_sensors[self._TEMPLATE_ZONE_VAR_VALUE.format(key, zone)][self._UNITS] = self._ariston_sensors[key][self._UNITS]
                    break

    def __init__(self,
                 username: str,
                 password: str,
                 sensors: list = None,
                 retries: int = 5,
                 polling: Union[float, int] = 1.,
                 store_file: bool = False,
                 store_folder: str = "",
                 units: str = _UNIT_METRIC,
                 ch_and_dhw: bool = False,
                 dhw_unknown_as_on: bool = True,
                 logging_level: str = _LEVEL_NOTSET,
                 gw: str = "",
                 zones: int = 1,
                 ) -> None:
        """
        Initialize API.
        """
        if sensors is None:
            sensors = list()

        if units not in {
            self._UNIT_METRIC,
            self._UNIT_IMPERIAL,
            self._UNIT_AUTO
        }:
            raise Exception("Invalid unit")

        if not isinstance(retries, int) or retries < 0:
            raise Exception("Invalid retries")

        if not isinstance(polling, float) and not isinstance(polling, int) or polling < 1:
            raise Exception("Invalid poling")

        if not isinstance(store_file, int):
            raise Exception("Invalid store files")

        if not isinstance(ch_and_dhw, bool):
            raise Exception("Invalid ch_and_dhw")

        if not isinstance(dhw_unknown_as_on, bool):
            raise Exception("Invalid dhw_unknown_as_on")

        if not isinstance(sensors, list):
            raise Exception("Invalid sensors type")

        if logging_level not in self._LOGGING_LEVELS:
            raise Exception("Invalid logging_level")

        if sensors:
            for sensor in sensors:
                if sensor not in self._SENSOR_LIST:
                    sensors.remove(sensor)

        if store_folder != "":
            self._store_folder = store_folder
        else:
            self._store_folder = os.path.join(os.getcwd(), self._FILE_FOLDER)
        if store_file:
            if not os.path.isdir(self._store_folder):
                os.makedirs(self._store_folder)

        """
        Logging settings
        """
        self._logging_level = logging.getLevelName(logging_level)
        self._LOGGER.setLevel(self._logging_level)
        self._console_handler = logging.StreamHandler()
        self._console_handler.setLevel(self._logging_level)
        self._formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self._console_handler.setFormatter(self._formatter)
        self._LOGGER.addHandler(self._console_handler)

        self._available = False
        self._ch_available = False
        self._ch_available_zone_2 = False
        self._ch_available_zone_3 = False
        self._dhw_available = False
        self._changing_data = False

        self._default_gw = gw
        if self._default_gw:
            self._gw_name = self._default_gw + '_'
        else:
            self._gw_name = ""

        # clear read sensor values
        self._ariston_sensors = dict()
        self._subscribed_sensors_old = dict()
        for sensor in self._SENSOR_LIST:
            self._ariston_sensors[sensor] = dict()
            self._ariston_sensors[sensor][self._VALUE] = None
            self._ariston_sensors[sensor][self._UNITS] = None
            self._subscribed_sensors_old[sensor] = copy.deepcopy(self._ariston_sensors[sensor])
        
        if units in {self._UNIT_METRIC, self._UNIT_IMPERIAL}:
            self._ariston_sensors[self._PARAM_UNITS][self._VALUE] = units
            self._update_units()

        for sensor in self._SENSOR_LIST:
            self._subscribed_sensors_old[sensor] = copy.deepcopy(self._ariston_sensors[sensor])

        # clear configuration data
        self._ariston_data = {}
        self._ariston_gas_data = {}
        self._ariston_error_data = {}
        self._ariston_dhw_data = {}
        self._ariston_currency = {}
        self._ariston_other_data = {}
        self._ariston_units = {}
        self._zone_data_main = {
            self._ZONE_1: dict(),
            self._ZONE_2: dict(),
            self._ZONE_3: dict()
        }
        self._zone_data_ch = {
            self._ZONE_1: dict(),
            self._ZONE_2: dict(),
            self._ZONE_3: dict()
        }
        # initiate all other data
        self._timer_periodic_read = threading.Timer(1, self._queue_get_data)
        self._timer_queue_delay = threading.Timer(1, self._control_availability_state, [self._REQUEST_GET_MAIN])
        self._timer_periodic_set = threading.Timer(1, self._preparing_setting_http_data)
        self._timer_set_delay = threading.Timer(1, self._preparing_setting_http_data)
        self._data_lock = threading.Lock()
        self._dhw_history = [self._UNKNOWN_TEMP, self._UNKNOWN_TEMP, self._UNKNOWN_TEMP, self._UNKNOWN_TEMP]
        self._dhw_trend_up = False
        self._errors = 0
        self._get_request_number_low_prio = 0
        self._get_request_number_high_prio = 0
        self._get_time_start = {
            self._REQUEST_GET_MAIN: 0.,
            self._REQUEST_GET_CH: 0.,
            self._REQUEST_GET_DHW: 0.,
            self._REQUEST_GET_ERROR: 0.,
            self._REQUEST_GET_GAS: 0.,
            self._REQUEST_GET_OTHER: 0.,
            self._REQUEST_GET_UNITS: 0.,
            self._REQUEST_GET_CURRENCY: 0.,
            self._REQUEST_GET_VERSION: 0.
        }
        self._get_time_end = {
            self._REQUEST_GET_MAIN: 0.,
            self._REQUEST_GET_CH: 0.,
            self._REQUEST_GET_DHW: 0.,
            self._REQUEST_GET_ERROR: 0.,
            self._REQUEST_GET_GAS: 0.,
            self._REQUEST_GET_OTHER: 0.,
            self._REQUEST_GET_UNITS: 0.,
            self._REQUEST_GET_CURRENCY: 0.,
            self._REQUEST_GET_VERSION: 0.
        }
        self._get_zero_temperature = {
            self._PARAM_CH_SET_TEMPERATURE: self._UNKNOWN_TEMP,
            self._PARAM_CH_COMFORT_TEMPERATURE: self._UNKNOWN_TEMP,
            self._PARAM_CH_ECONOMY_TEMPERATURE: self._UNKNOWN_TEMP,
            self._PARAM_CH_DETECTED_TEMPERATURE: self._UNKNOWN_TEMP,
            self._PARAM_DHW_SET_TEMPERATURE: self._UNKNOWN_TEMP,
            self._PARAM_DHW_COMFORT_TEMPERATURE: self._UNKNOWN_TEMP,
            self._PARAM_DHW_ECONOMY_TEMPERATURE: self._UNKNOWN_TEMP,
            self._PARAM_DHW_STORAGE_TEMPERATURE: self._UNKNOWN_TEMP
        }
        self._lock = threading.Lock()
        self._login = False
        self._password = password
        self._plant_id = ""
        self._plant_id_lock = threading.Lock()
        self._session = requests.Session()
        self._ch_and_dhw = ch_and_dhw
        self._dhw_unknown_as_on = dhw_unknown_as_on
        self._set_param = {}
        self._set_param_group = {
            self._REQUEST_GET_MAIN: False,
            self._REQUEST_GET_OTHER: False,
            self._REQUEST_GET_UNITS: False
        }
        self._today_count_ignore = dict()
        for today_param in self._TODAY_SENSORS:
            self._today_count_ignore[today_param] = 0
        self._set_retry = {
            self._REQUEST_SET_MAIN: 0,
            self._REQUEST_SET_OTHER: 0,
            self._REQUEST_SET_UNITS: 0
        }
        self._set_max_retries = retries
        self._set_new_data_pending = False
        self._set_scheduled = False
        self._set_time_start = {
            self._REQUEST_SET_MAIN: 0,
            self._REQUEST_SET_OTHER: 0,
            self._REQUEST_SET_UNITS: 0
        }
        self._set_time_end = {
            self._REQUEST_SET_MAIN: 0,
            self._REQUEST_SET_OTHER: 0,
            self._REQUEST_SET_UNITS: 0
        }
        self._store_file = store_file
        self._subscribed = list()
        self._subscribed_args = list()
        self._subscribed_kwargs = list()
        self._subscribed_thread = list()

        self._subscribed2 = list()
        self._subscribed2_args = list()
        self._subscribed2_kwargs = list()
        self._subscribed2_thread = list()

        self._token_lock = threading.Lock()
        self._token = None
        self._units = units
        self._url = self._ARISTON_URL
        self._user = username
        self._verify = True
        self._version = ""
        self._zones = zones
        # check which requests should be used
        # note that main and other are mandatory for climate and water_heater operations
        self._valid_requests = {
            self._REQUEST_GET_MAIN: True,
            self._REQUEST_GET_CH: False,
            self._REQUEST_GET_DHW: False,
            self._REQUEST_GET_ERROR: False,
            self._REQUEST_GET_GAS: False,
            self._REQUEST_GET_OTHER: True,
            self._REQUEST_GET_UNITS: False,
            self._REQUEST_GET_CURRENCY: False,
            self._REQUEST_GET_VERSION: False
        }
        if sensors:
            for item in sensors:
                self._valid_requests[self._get_request_for_parameter(item)] = True

        sensors_to_use = list()
        exclude_set = {
            self._PARAM_DHW_COMFORT_TEMPERATURE, 
            self._PARAM_DHW_ECONOMY_TEMPERATURE
        }
        for sensor_to_add in sorted(self._GET_REQUEST_PARAM):
            if sensor_to_add in sensors and sensor_to_add not in exclude_set:
                sensors_to_use.append(self._PARAM_TO_ARISTON[sensor_to_add])
                # duplicate zone parameters
                if self._zones > 1:
                    for param in self._ZONE_PARAMETERS:
                        check_key = self._CLASS_LOCALS[param]
                        if check_key == sensor_to_add:
                            for zone in range(self._ADD_ZONES_START, self._ADD_ZONES_STOP + 1):
                                sensors_to_use.append(self._PARAM_TO_ARISTON[self._TEMPLATE_ZONE_VAR_VALUE.format(check_key, zone)])
                            break
        self._param_sensors = sensors_to_use

        if self._units == self._UNIT_AUTO:
            self._valid_requests[self._REQUEST_GET_UNITS] = True
        # prepare lists of requests
        # prepare list of higher priority
        self._request_list_high_prio = []
        if self._valid_requests[self._REQUEST_GET_MAIN]:
            self._request_list_high_prio.append(self._REQUEST_GET_MAIN)
        if self._valid_requests[self._REQUEST_GET_UNITS]:
            self._request_list_high_prio.append(self._REQUEST_GET_UNITS)
        if self._valid_requests[self._REQUEST_GET_OTHER]:
            self._request_list_high_prio.append(self._REQUEST_GET_OTHER)
        if self._valid_requests[self._REQUEST_GET_ERROR]:
            self._request_list_high_prio.append(self._REQUEST_GET_ERROR)
        # prepare list of lower priority
        self._request_list_low_prio = []
        if self._valid_requests[self._REQUEST_GET_CH]:
            self._request_list_low_prio.append(self._REQUEST_GET_CH)
        if self._valid_requests[self._REQUEST_GET_DHW]:
            self._request_list_low_prio.append(self._REQUEST_GET_DHW)
        if self._valid_requests[self._REQUEST_GET_GAS]:
            self._request_list_low_prio.append(self._REQUEST_GET_GAS)
        if self._valid_requests[self._REQUEST_GET_CURRENCY]:
            self._request_list_low_prio.append(self._REQUEST_GET_CURRENCY)
        if self._valid_requests[self._REQUEST_GET_VERSION]:
            self._request_list_low_prio.append(self._REQUEST_GET_VERSION)

        # initiate timer between requests within one loop
        self._timer_between_param_delay = self._HTTP_PARAM_DELAY * polling

        # initiate timers for http requests to reading or setting of data
        self._timeout_long = self._HTTP_TIMEOUT_GET_LONG * polling
        self._timeout_medium = self._HTTP_TIMEOUT_GET_MEDIUM * polling
        self._timeout_short = self._HTTP_TIMEOUT_GET_SHORT * polling

        # initiate timer between set request attempts
        self._timer_between_set = self._timer_between_param_delay + self._HTTP_TIMER_SET_WAIT

        self._current_temp_economy_ch = {
            self._ZONE_1: None,
            self._ZONE_2: None,
            self._ZONE_3: None
        }
        self._current_temp_economy_dhw = None

        self._started = False

        self._LOGGER.info("API initiated")

        if self._store_file:
            if not os.path.isdir(self._store_folder):
                os.makedirs(self._store_folder)
            store_file = self._gw_name + 'data_ariston_valid_requests.json'
            store_file_path = os.path.join(self._store_folder, store_file)
            with open(store_file_path, 'w') as ariston_fetched:
                json.dump(self._valid_requests, ariston_fetched)
            store_file = self._gw_name + 'data_ariston_high_prio.json'
            store_file_path = os.path.join(self._store_folder, store_file)
            with open(store_file_path, 'w') as ariston_fetched:
                json.dump(self._request_list_high_prio, ariston_fetched)
            store_file = self._gw_name + 'data_ariston_low_prio.json'
            store_file_path = os.path.join(self._store_folder, store_file)
            with open(store_file_path, 'w') as ariston_fetched:
                json.dump(self._request_list_low_prio, ariston_fetched)

    def _send_params_get_main(self):
        result = ['?zoneNum={0}&umsys=si']
        if self._zones > 1:
            for zone in range(self._ADD_ZONES_START, self._zones + 1):
                result.append(f'?zoneNum={zone}&umsys=si')
        return result

    def _send_params_get_program(self):
        result = list()
        for zone in range(1, self._zones + 1):
                result.append(f'?progId=ChZn{zone}&umsys=si')
        return result

    def _send_params_set(self, zone_name):
        zone = self._ZONE_ORDER.index(zone_name) + 1
        return f'?zoneNum={zone}&umsys=si'

    def subscribe_sensors(self, func, *args, **kwargs):
        """
        Subscribe to change of sensors value in:
            - sensor_values

        Function will be called when sensors' values are being changed.
        Actual changed values are being returned as a dictionary in a first argument.
        """
        self._subscribed.append(func)
        self._subscribed_args.append(args)
        self._subscribed_kwargs.append(kwargs)

    def subscribe_statuses(self, func, *args, **kwargs):
        """
        Subscribe to change of API statuses such as:
            - available
            - ch_available
            - dhw_available
            - setting_data

        Function will be called when statuses are being changed.
        Changed property names shall be returned as a dictionary in a first argument.
        """
        self._subscribed2.append(func)
        self._subscribed2_args.append(args)
        self._subscribed2_kwargs.append(kwargs)

    def _subscribers_sensors_inform(self):
        """
        Inform subscribers about changed sensors
        first argument is a dictionary of changed sensors
        """

        changed_data = dict()

        for sensor in self._SENSOR_LIST:
            if sensor in self._ariston_sensors:
                if self._ariston_sensors[sensor][self._VALUE] != self._subscribed_sensors_old[sensor][self._VALUE] or \
                    self._ariston_sensors[sensor][self._UNITS] != self._subscribed_sensors_old[sensor][self._UNITS]:
                    
                    if isinstance(self._ariston_sensors[sensor][self._VALUE], dict) and isinstance(self._subscribed_sensors_old[sensor][self._VALUE], dict):
                        if self._ariston_sensors[sensor][self._VALUE] == {} or self._subscribed_sensors_old[sensor][self._VALUE] == {}:
                            inform = True
                        elif len(self._ariston_sensors[sensor][self._VALUE]) != len(self._subscribed_sensors_old[sensor][self._VALUE]):
                            inform = True
                        else:
                            inform = False
                            for key, value in self._ariston_sensors[sensor][self._VALUE].items():
                                if self._subscribed_sensors_old[sensor][self._VALUE][key] != value:
                                    inform = True
                    else:
                        inform = True

                    if inform:
                        self._subscribed_sensors_old[sensor] = copy.deepcopy(self._ariston_sensors[sensor])
                        changed_data[sensor] = self._ariston_sensors[sensor]

        if changed_data:
            for iteration in range(len(self._subscribed)):
                self._subscribed_thread = threading.Timer(
                    0, self._subscribed[iteration], args=(changed_data, *self._subscribed_args[iteration]), kwargs=self._subscribed_kwargs[iteration])
                self._subscribed_thread.start()

    def _subscribers_statuses_inform(self, changed_data):
        """Inform subscribers about changed API statuses"""
        for iteration in range(len(self._subscribed2)):
            self._subscribed2_thread = threading.Timer(
                0, self._subscribed2[iteration], args=(changed_data, *self._subscribed2_args[iteration]), kwargs=self._subscribed2_kwargs[iteration])
            self._subscribed2_thread.start()
            

    def _change_to_24h_format(self, time_str_12h=""):
        """Convert to 24H format if in 12H format"""
        if not isinstance(time_str_12h, str):
            time_str_12h = self._DEFAULT_TIME
        try:
            if len(time_str_12h) > 5:
                time_and_indic = time_str_12h.split(' ')
                if time_and_indic[1] == "AM":
                    if time_and_indic[0] == "12:00":
                        time_str_24h = "00:00"
                    else:
                        time_str_24h = time_and_indic[0]
                elif time_and_indic[1] == "PM":
                    if time_and_indic[0] == "12:00":
                        time_str_24h = "12:00"
                    else:
                        time_hour_minute = time_and_indic[0].split(":")
                        time_str_24h = str(int(time_hour_minute[0]) + 12) + ":" + time_hour_minute[1]
                else:
                    time_str_24h = self._DEFAULT_TIME
            else:
                time_str_24h = time_str_12h
        except IndexError:
            time_str_24h = self._DEFAULT_TIME
        return time_str_24h

    @staticmethod
    def _json_validator(data):
        try:
            if isinstance(data, dict):
                if data == {}:
                    return False
                else:
                    return True
            if isinstance(data, list):
                if not data:
                    return False
                else:
                    for item in data:
                        if not isinstance(item, dict):
                            return False
                    return True
            else:
                return False
        except KeyError:
            return False

    def _set_statuses(self):
        """Set availablility states"""
        old_available = self._available
        old_ch_available = self._ch_available
        old_ch_available_zone_2 = self._ch_available_zone_2
        old_ch_available_zone_3 = self._ch_available_zone_3
        old_dhw_available = self._dhw_available
        old_changing = self._changing_data

        changed_data = dict()

        self._available = self._errors <= self._MAX_ERRORS and self._login and self._plant_id != "" and self._ariston_data != {}

        if self._ariston_sensors[self._PARAM_UNITS][self._VALUE] not in {self._VAL_METRIC, self._VAL_IMPERIAL}:
            self._ch_available = False
        elif self._ariston_other_data == {}:
            self._ch_available = False
        else:
            self._ch_available = self._available and self._zone_data_main[self._ZONE_1] and self._zone_data_main[self._ZONE_1]["mode"]["allowedOptions"] != []

        if self._ariston_sensors[self._PARAM_UNITS][self._VALUE] not in {self._VAL_METRIC, self._VAL_IMPERIAL}:
            self._ch_available_zone_2 = False
        elif self._ariston_other_data == {}:
            self._ch_available_zone_2 = False
        else:
            self._ch_available_zone_2 = self._available and self._zone_data_main[self._ZONE_2] and self._zone_data_main[self._ZONE_2]["mode"]["allowedOptions"] != []

        if self._ariston_sensors[self._PARAM_UNITS][self._VALUE] not in {self._VAL_METRIC, self._VAL_IMPERIAL}:
            self._ch_available_zone_3 = False
        elif self._ariston_other_data == {}:
            self._ch_available_zone_3 = False
        else:
            self._ch_available_zone_3 = self._available and self._zone_data_main[self._ZONE_3] and self._zone_data_main[self._ZONE_3]["mode"]["allowedOptions"] != []

        if self._ariston_sensors[self._PARAM_UNITS][self._VALUE] not in {self._VAL_METRIC, self._VAL_IMPERIAL}:
            self._dhw_available = False
        elif self._ariston_other_data == {}:
            self._dhw_available = False
        else:
            self._dhw_available = self._available

        self._changing_data = self._set_param != {}

        if old_available != self._available:
            changed_data['available'] = self._available

        if old_ch_available != self._ch_available:
            changed_data['ch_available'] = self._ch_available

        if old_ch_available_zone_2 != self._ch_available_zone_2:
            changed_data['ch_available_zone_2'] = self._ch_available_zone_2

        if old_ch_available_zone_3 != self._ch_available_zone_3:
            changed_data['ch_available_zone_3'] = self._ch_available_zone_3

        if old_dhw_available != self._dhw_available:
            changed_data['dhw_available'] = self._dhw_available

        if old_changing != self._changing_data:
            changed_data['setting_data'] = self._changing_data

        if changed_data:
            self._subscribers_statuses_inform(changed_data)

    @classmethod
    def api_data(cls):
        """
        Get API data as a tuple:
          - API version
          - supported sensors by API (actual list of supported sensors by the model cannot be identified and must be chosen manually)
          - supported parameters to be changed by API (actual list of supported parameters by the model cannot be identified and must be chosen manually)
        """
        return cls._VERSION, cls._SENSOR_LIST, cls._SENSOR_SET_LIST

    @property
    def plant_id(self) -> str:
        """Return the unique plant_id."""
        return self._plant_id

    @property
    def available(self) -> bool:
        """Return if Aristons's API is responding."""
        return self._available

    @property
    def ch_available(self) -> bool:
        """Return if Aristons's API is responding and if there is data available for the CH."""
        return self._ch_available

    @property
    def ch_available_zone_2(self) -> bool:
        """Return if Aristons's API is responding and if there is data available for the CH."""
        return self._ch_available_zone_2

    @property
    def ch_available_zone_3(self) -> bool:
        """Return if Aristons's API is responding and if there is data available for the CH."""
        return self._ch_available_zone_3

    @property
    def dhw_available(self) -> bool:
        """Return if Aristons's API is responding and if there is data available for the DHW."""
        return self._dhw_available

    @property
    def version(self) -> str:
        """Return version of the API in use."""
        return self._VERSION

    @property
    def sensor_values(self) -> dict:
        """
        Return dictionary of sensors and their values.

        'value' key is used to fetch value of the specific sensor/parameter.
        Some sensors/parameters might return dictionaries.

        'units' key is used to fetch units of measurement for specific sensor/parameter.

        """
        return self._ariston_sensors

    @property
    def setting_data(self) -> bool:
        """Return if setting of data is in progress."""
        return self._changing_data

    @property
    def supported_sensors_get(self) -> set:
        """
        Return set of all supported sensors/parameters in API.
        Note that it is sensors supported by API, not the server, so some might never have valid values.
        """
        return self._SENSOR_LIST

    @property
    def supported_sensors_set(self) -> set:
        """
        Return set of all parameters that potentially can be set by API.
        Note that it is parameters supported by API, not the server, so some might be impossible to be set.
        use property 'supported_sensors_set_values' to find allowed values to be set.
        """
        return self._SENSOR_SET_LIST

    @property
    def supported_sensors_set_values(self) -> dict:
        """
        Return dictionary of sensors/parameters to be set and allowed values.
        Allowed values can be returned as:
            - set of allowed options;
            - dictionary with following keys:
                - 'min' is used to indicate minimum value in the range;
                - 'max' is used to indicate maximum value in the range;
                - 'step' is used to indicate step;

        data from this property is used for 'set_http_data' method.
        """
        sensors_dictionary = {}
        for parameter in self._SENSOR_SET_LIST:
            zone_number = self._MAP_PARAM_NAME_TO_ZONE_NUMBER[parameter]
            if self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_MODE:
                param_values = set()
                if self._ariston_data != {}:
                    for value in self._ariston_data["allowedModes"]:
                        if value in self._VALUE_TO_MODE:
                            param_values.add(self._VALUE_TO_MODE[value])
                sensors_dictionary[parameter] = param_values
            elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_CH_MODE:
                param_values = set()
                if self._ariston_data != {} and self._zone_data_main[zone_number]:
                    for value in self._zone_data_main[zone_number]["mode"]["allowedOptions"]:
                        if value in self._VALUE_TO_CH_MODE:
                            param_values.add(self._VALUE_TO_CH_MODE[value])
                sensors_dictionary[parameter] = param_values
            elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_CH_SET_TEMPERATURE:
                param_values = dict()
                if self._ariston_data != {} and self._zone_data_main[zone_number]:
                    param_values["min"] = self._zone_data_main[zone_number]["comfortTemp"]["min"]
                    param_values["max"] = self._zone_data_main[zone_number]["comfortTemp"]["max"]
                    param_values["step"] = 0.5
                sensors_dictionary[parameter] = param_values
            elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_CH_COMFORT_TEMPERATURE:
                param_values = dict()
                if self._ariston_data != {} and self._zone_data_main[zone_number]:
                    param_values["min"] = self._zone_data_main[zone_number]["comfortTemp"]["min"]
                    param_values["max"] = self._zone_data_main[zone_number]["comfortTemp"]["max"]
                    param_values["step"] = 0.5
                sensors_dictionary[parameter] = param_values
            elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_CH_ECONOMY_TEMPERATURE:
                param_values = dict()
                if self._ariston_data != {} and self._zone_data_main[zone_number]:
                    param_values["min"] = self._zone_data_main[zone_number]["comfortTemp"]["min"]
                    param_values["max"] = self._zone_data_main[zone_number]["comfortTemp"]["max"]
                    param_values["step"] = 0.5
                sensors_dictionary[parameter] = param_values
            elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_CH_AUTO_FUNCTION:
                sensors_dictionary[parameter] = [*self._PARAM_STRING_TO_VALUE]
            elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_DHW_SET_TEMPERATURE:
                param_values = dict()
                if self._ariston_data != {}:
                    param_values["min"] = self._ariston_data["dhwTemp"]["min"]
                    param_values["max"] = self._ariston_data["dhwTemp"]["max"]
                    param_values["step"] = 1
                sensors_dictionary[parameter] = param_values
            elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_DHW_COMFORT_TEMPERATURE:
                param_values = dict()
                if self._ariston_data != {}:
                    param_values["min"] = max(self._ariston_data["dhwTemp"]["min"],
                                              self._ariston_data["dhwTimeProgComfortTemp"]["min"])
                    param_values["max"] = max(self._ariston_data["dhwTemp"]["max"],
                                              self._ariston_data["dhwTimeProgComfortTemp"]["max"])
                    param_values["step"] = 1
                sensors_dictionary[parameter] = param_values
            elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_DHW_ECONOMY_TEMPERATURE:
                param_values = dict()
                if self._ariston_data != {}:
                    param_values["min"] = self._ariston_data["dhwTemp"]["min"]
                    param_values["max"] = self._ariston_data["dhwTemp"]["max"]
                    param_values["step"] = 1
                sensors_dictionary[parameter] = param_values
            elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_DHW_MODE:
                param_values = set()
                if self._ariston_data != {}:
                    if not self._ariston_data["dhwModeNotChangeable"]:
                        param_values = {self._VAL_MANUAL, self._VAL_PROGRAM}
                sensors_dictionary[parameter] = param_values
            elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_DHW_COMFORT_FUNCTION:
                sensors_dictionary[parameter] = [*self._DHW_COMFORT_FUNCT_TO_VALUE]
            elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_INTERNET_TIME:
                sensors_dictionary[parameter] = [*self._PARAM_STRING_TO_VALUE]
            elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_INTERNET_WEATHER:
                sensors_dictionary[parameter] = [*self._PARAM_STRING_TO_VALUE]
            elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_UNITS:
                sensors_dictionary[parameter] = [*self._UNIT_TO_VALUE]
            elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_THERMAL_CLEANSE_CYCLE:
                param_values = dict()
                if self._ariston_other_data != {}:
                    for param_item in self._ariston_other_data:
                        if param_item["id"] == self._ARISTON_THERMAL_CLEANSE_CYCLE:
                            param_values["min"] = param_item["min"]
                            param_values["max"] = param_item["max"]
                            param_values["step"] = 1.
                sensors_dictionary[parameter] = param_values
            elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_CH_WATER_TEMPERATURE:
                param_values = dict()
                if self._ariston_other_data != {}:
                    for param_item in self._ariston_other_data:
                        if param_item["id"] == self._ARISTON_CH_WATER_TEMPERATURE:
                            param_values["min"] = param_item["min"]
                            param_values["max"] = param_item["max"]
                            param_values["step"] = 1.
                sensors_dictionary[parameter] = param_values
            elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_THERMAL_CLEANSE_FUNCTION:
                sensors_dictionary[parameter] = [*self._PARAM_STRING_TO_VALUE]
        return sensors_dictionary

    def _get_plant_id(self, resp):
        plant_id = ""
        if resp.url.startswith(self._url + "/PlantDashboard/Index/") or resp.url.startswith(
                self._url + "/PlantManagement/Index/") or resp.url.startswith(
                self._url + "/PlantPreference/Index/") or resp.url.startswith(
                self._url + "/Error/Active/") or resp.url.startswith(
                self._url + "/PlantGuest/Index/") or resp.url.startswith(
                self._url + "/TimeProg/Index/"):
                plant_id = resp.url.split("/")[5]
        elif resp.url.startswith(self._url + "/PlantData/Index/") or resp.url.startswith(
                self._url + "/UserData/Index/"):
                plant_id_attribute = resp.url.split("/")[5]
                plant_id = plant_id_attribute.split("?")[0]
        elif resp.url.startswith(self._url + "/Menu/User/Index/"):
                plant_id = resp.url.split("/")[6]
        else:
            self._LOGGER.warning('%s Authentication login error', self)
            raise Exception("Login parsing of URL failed")
        if plant_id:
            if self._default_gw:
                # If GW is specified, it can differ from the default
                url = self._url + "/PlantManagement/Index/" + plant_id
                try:
                    resp = self._session.get(
                            url,
                            auth=self._token,
                            timeout=self._HTTP_TIMEOUT_LOGIN,
                            verify=True)
                except requests.exceptions.RequestException:
                    self._LOGGER.warning('%s Checking gateways error', self)
                    raise Exception("Checking gateways error")
                if resp.status_code != 200:
                    self._LOGGER.warning('%s Checking gateways error', self)
                    raise Exception("Checking gateways error")
                gateways = set()
                for item in re.findall(r'"GwId":"[a-zA-Z0-9]+"', resp.text):
                    detected_gw = item.replace('"GwId"', '').replace(':', '').replace('"', '').replace(' ', '')
                    gateways.add(detected_gw)
                gateways_txt = ", ".join(gateways)
                if self._default_gw not in gateways:
                    self._LOGGER.error(f'Gateway "{self._default_gw}" is not in the list of allowed gateways: {gateways_txt}')
                    raise Exception(f'Gateway "{self._default_gw}" is not in the list of allowed gateways: {gateways_txt}')
                else:
                    self._LOGGER.info(f'Allowed gateways: {gateways_txt}')
                plant_id = self._default_gw

        return plant_id

    def _login_session(self):
        """Login to fetch Ariston Plant ID and confirm login"""
        if not self._login and self._started:
            url = self._url + '/Account/Login'
            login_data = {"Email": self._user, "Password": self._password}
            try:
                with self._token_lock:
                    self._token = requests.auth.HTTPDigestAuth(self._user, self._password)
                resp = self._session.post(
                    url,
                    auth=self._token,
                    timeout=self._HTTP_TIMEOUT_LOGIN,
                    json=login_data,
                    verify=True)
            except requests.exceptions.RequestException:
                self._LOGGER.warning('%s Authentication login error', self)
                raise Exception("Login request exception")
            if resp.status_code != 200:
                if self._store_file:
                    if not os.path.isdir(self._store_folder):
                        os.makedirs(self._store_folder)
                    store_file = self._gw_name + "data_ariston_login_" + str(resp.status_code) + "_error.txt"
                    store_file_path = os.path.join(self._store_folder, store_file)
                    with open(store_file_path, "w") as f:
                        f.write(resp.text)
                self._LOGGER.warning('%s Unexpected reply during login: %s', self, resp.status_code)
                raise Exception("Login unexpected reply code")
            plant_id = self._get_plant_id(resp)
            
            if plant_id:
                with self._plant_id_lock:
                    self._plant_id = plant_id
                    self._gw_name = plant_id + '_'
                    self._login = True
                    self._LOGGER.info('%s Plant ID is %s', self, self._plant_id)

        return

    def _set_sensors(self, request_type="", zone_number=_ZONE_1):

        self._LOGGER.info(f"Setting sensors for {request_type} and {zone_number}")

        if request_type in {self._REQUEST_GET_MAIN, self._REQUEST_SET_MAIN}:

            if self.available and self._ariston_data != {}:

                parameter = self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_CH_DETECTED_TEMPERATURE][zone_number]
                try:
                    self._ariston_sensors[parameter][self._VALUE] = \
                        self._zone_data_main[zone_number]["roomTemp"]
                except KeyError:
                    self._ariston_sensors[parameter][self._VALUE] = None

                parameter = self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_CH_ANTIFREEZE_TEMPERATURE][zone_number]
                try:
                    self._ariston_sensors[parameter][self._VALUE] = \
                        self._zone_data_main[zone_number]["antiFreezeTemp"]
                except KeyError:
                    self._ariston_sensors[parameter][self._VALUE] = None

                parameter = self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_CH_MODE][zone_number]
                try:
                    self._ariston_sensors[parameter][self._VALUE] = \
                        self._VALUE_TO_CH_MODE[self._zone_data_main[zone_number]["mode"]["value"]]
                except KeyError:
                    self._ariston_sensors[parameter][self._VALUE] = None

                parameter = self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_CH_SET_TEMPERATURE][zone_number]
                try:
                    self._ariston_sensors[parameter][self._VALUE] = \
                        self._zone_data_main[zone_number]["desiredTemp"]
                except KeyError:
                    self._ariston_sensors[parameter][self._VALUE] = None

                parameter = self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_DHW_SET_TEMPERATURE][zone_number]
                try:
                    self._ariston_sensors[parameter][self._VALUE] = \
                        self._ariston_data["dhwTemp"]["value"]
                except KeyError:
                    self._ariston_sensors[parameter][self._VALUE] = None

                parameter = self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_MODE][zone_number]
                try:
                    self._ariston_sensors[parameter][self._VALUE] = \
                        self._VALUE_TO_MODE[self._ariston_data["mode"]]
                except KeyError:
                    self._ariston_sensors[parameter][self._VALUE] = None

                parameter = self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_DHW_STORAGE_TEMPERATURE][zone_number]
                try:
                    self._ariston_sensors[parameter][self._VALUE] = \
                        self._ariston_data["dhwStorageTemp"]
                except KeyError:
                    self._ariston_sensors[parameter][self._VALUE] = None

                parameter = self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_OUTSIDE_TEMPERATURE][zone_number]
                try:
                    self._ariston_sensors[parameter][self._VALUE] = \
                        self._ariston_data["outsideTemp"]
                except KeyError:
                    self._ariston_sensors[parameter][self._VALUE] = None

                parameter = self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_DHW_COMFORT_TEMPERATURE][zone_number]
                try:
                    if self._ariston_data["dhwTimeProgComfortTemp"]["value"] != 0:
                        self._ariston_sensors[parameter][self._VALUE] = \
                            self._ariston_data["dhwTimeProgComfortTemp"]["value"]
                except KeyError:
                    self._ariston_sensors[parameter][self._VALUE] = None

                parameter = self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_DHW_ECONOMY_TEMPERATURE][zone_number]
                try:
                    if self._ariston_data["dhwTimeProgEconomyTemp"]["value"] != 0:
                        self._ariston_sensors[parameter][self._VALUE] = \
                            self._ariston_data["dhwTimeProgEconomyTemp"]["value"]
                except KeyError:
                    self._ariston_sensors[parameter][self._VALUE] = None

                parameter = self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_DHW_MODE][zone_number]
                try:
                    self._ariston_sensors[parameter][self._VALUE] = \
                        self._VALUE_TO_DHW_MODE[self._ariston_data["dhwMode"]]
                except KeyError:
                    self._ariston_sensors[parameter][self._VALUE] = None

                parameter = self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_HOLIDAY_MODE][zone_number]
                try:
                    if self._zone_data_main[zone_number]["comfortTemp"]["value"] == \
                            self._zone_data_main[zone_number]["antiFreezeTemp"] or self._ariston_data["holidayEnabled"]:
                        self._ariston_sensors[parameter][self._VALUE] = True
                    else:
                        self._ariston_sensors[parameter][self._VALUE] = False
                except KeyError:
                    self._ariston_sensors[parameter][self._VALUE] = None

                parameter = self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_FLAME][zone_number]
                try:
                    self._ariston_sensors[parameter][self._VALUE] = \
                        self._ariston_data["flameSensor"]
                except KeyError:
                    self._ariston_sensors[parameter][self._VALUE] = None

                parameter = self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_HEAT_PUMP][zone_number]
                try:
                    self._ariston_sensors[parameter][self._VALUE] = \
                        self._ariston_data["heatingPumpOn"]
                except KeyError:
                    self._ariston_sensors[parameter][self._VALUE] = None

                parameter = self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_CH_PILOT][zone_number]
                try:
                    self._ariston_sensors[parameter][self._VALUE] = \
                        self._zone_data_main[zone_number]["pilotOn"]
                except KeyError:
                    self._ariston_sensors[parameter][self._VALUE] = None

                parameter = self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_CH_FLAME][zone_number]
                try:
                    self._ariston_sensors[parameter][self._VALUE] = \
                        self._zone_data_main[zone_number]["heatRequest"]
                    if self._ariston_data["dhwStorageTemp"] != self._INVALID_STORAGE_TEMP \
                            and self._dhw_trend_up \
                            and self._VALUE_TO_MODE[self._ariston_data["mode"]] in {self._VAL_SUMMER, self._VAL_WINTER}\
                            and self._ariston_data["flameSensor"] and not self._ch_and_dhw:
                        self._ariston_sensors[parameter][self._VALUE] = False
                except KeyError:
                    self._ariston_sensors[parameter][self._VALUE] = None

                parameter = self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_DHW_FLAME][zone_number]
                try:
                    if self._ariston_data["dhwStorageTemp"] != self._INVALID_STORAGE_TEMP:
                        # trend can be used
                        _dhw_automation_possible = True
                    else:
                        _dhw_automation_possible = False
                    _dhw_flame = False
                    if self._ariston_data["flameSensor"] and \
                        self._VALUE_TO_MODE[self._ariston_data["mode"]] in [self._VAL_SUMMER, self._VAL_WINTER]:
                        if self._ariston_data["flameForDhw"]:
                            # wow, does DHW flag actually work for someone
                            _dhw_flame = True
                        elif _dhw_automation_possible and self._dhw_trend_up:
                            # temeparture increases, assume flame on
                            _dhw_flame = True
                        elif not _dhw_automation_possible and self._dhw_unknown_as_on:
                            # no automation, use default value
                            _dhw_flame = True
                        else:
                            any_ch_flame = False
                            for zone in self._ZONE_ORDER:
                                if self._zone_data_main[zone_number] and self._zone_data_main[zone_number]["heatRequest"]:
                                    any_ch_flame = True
                                    break
                            if not any_ch_flame:
                                # flame is not CH meaning it is DHW
                                _dhw_flame = True
                    self._ariston_sensors[parameter][self._VALUE] = _dhw_flame
                except KeyError:
                    self._ariston_sensors[parameter][self._VALUE] = None

            else:
                for parameter in self._GET_REQUEST_MAIN:
                    self._ariston_sensors[parameter][self._VALUE] = None

        if request_type == self._REQUEST_GET_CH:

            if self.available and self._zone_data_ch[zone_number] != {}:

                parameter = self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_CH_PROGRAM][zone_number]
                try:
                    self._ariston_sensors[parameter][self._VALUE] = {}
                    for day_of_week in self._DAYS_OF_WEEK:
                        if day_of_week in self._zone_data_ch[zone_number]:
                            for day_slices in self._zone_data_ch[zone_number][day_of_week]["slices"]:
                                attribute_name = day_of_week + '_' + day_slices["from"] + '_' + day_slices["to"]
                                if day_slices["temperatureId"] == 1:
                                    attribute_value = "Comfort"
                                else:
                                    attribute_value = "Economy"
                                self._ariston_sensors[parameter][self._VALUE][attribute_name] = \
                                    attribute_value
                except KeyError:
                    self._ariston_sensors[parameter][self._VALUE] = None

            else:
                self._ariston_sensors[parameter][self._VALUE] = None

        if request_type == self._REQUEST_GET_DHW:

            if self.available and self._ariston_dhw_data != {}:

                try:
                    self._ariston_sensors[self._PARAM_DHW_PROGRAM][self._VALUE] = {}
                    for day_of_week in self._DAYS_OF_WEEK:
                        if day_of_week in self._ariston_dhw_data:
                            for day_slices in self._ariston_dhw_data[day_of_week]["slices"]:
                                attribute_name = day_of_week + '_' + day_slices["from"] + '_' + day_slices["to"]
                                if day_slices["temperatureId"] == 1:
                                    attribute_value = "Comfort"
                                else:
                                    attribute_value = "Economy"
                                self._ariston_sensors[self._PARAM_DHW_PROGRAM][self._VALUE][attribute_name] = \
                                    attribute_value
                except KeyError:
                    self._ariston_sensors[self._PARAM_DHW_PROGRAM][self._VALUE] = None

            else:
                self._ariston_sensors[self._PARAM_DHW_PROGRAM][self._VALUE] = None

        if request_type == self._REQUEST_GET_ERROR:

            if self.available and self._ariston_error_data != {}:

                try:
                    error_struct = dict()
                    self._ariston_sensors[self._PARAM_ERRORS_COUNT][self._VALUE] = \
                        len(self._ariston_error_data["result"])
                    for count, error in enumerate(self._ariston_error_data["result"]):
                        error_struct[f"Error{count + 1}_Slogan"] = error["Fault"]
                        error_struct[f"Error{count + 1}_Severity"] = error["Severity"]
                        error_struct[f"Error{count + 1}_Timestamp"] = error["Timestamp"]
                    self._ariston_sensors[self._PARAM_ERRORS][self._VALUE] = error_struct
                except KeyError as ex:
                    self._ariston_sensors[self._PARAM_ERRORS_COUNT][self._VALUE] = None
                    self._ariston_sensors[self._PARAM_ERRORS][self._VALUE] = None

            else:
                self._ariston_sensors[self._PARAM_ERRORS][self._VALUE] = None
                self._ariston_sensors[self._PARAM_ERRORS_COUNT][self._VALUE] = None

        if request_type == self._REQUEST_GET_GAS:

            if self.available and self._ariston_gas_data != {}:

                try:
                    self._ariston_sensors[self._PARAM_ACCOUNT_CH_GAS][self._VALUE] = \
                        self._ariston_gas_data["account"]["gasHeat"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_ACCOUNT_CH_GAS][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_ACCOUNT_DHW_GAS][self._VALUE] = \
                        self._ariston_gas_data["account"]["gasDhw"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_ACCOUNT_DHW_GAS][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_ACCOUNT_CH_ELECTRICITY][self._VALUE] = \
                        self._ariston_gas_data["account"]["elecHeat"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_ACCOUNT_CH_ELECTRICITY][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_ACCOUNT_DHW_ELECTRICITY][self._VALUE] = \
                        self._ariston_gas_data["account"]["elecDhw"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_ACCOUNT_DHW_ELECTRICITY][self._VALUE] = None

                try:
                    sum_obj = 0
                    self._ariston_sensors[self._PARAM_HEATING_LAST_24H_LIST][self._VALUE] = {}
                    for iteration, item in enumerate(self._ariston_gas_data["daily"]["data"], 1):
                        self._ariston_sensors[self._PARAM_HEATING_LAST_24H_LIST][self._VALUE][
                            "Period" + str(iteration)] = item["y2"]
                        sum_obj = sum_obj + item["y2"]
                    self._ariston_sensors[self._PARAM_HEATING_LAST_24H][self._VALUE] = round(sum_obj, 3)
                except KeyError:
                    self._ariston_sensors[self._PARAM_HEATING_LAST_24H][self._VALUE] = None
                    self._ariston_sensors[self._PARAM_HEATING_LAST_24H_LIST][self._VALUE] = None

                try:
                    sum_obj = 0
                    self._ariston_sensors[self._PARAM_COOLING_LAST_24H_LIST][self._VALUE] = {}
                    for iteration, item in enumerate(self._ariston_gas_data["daily"]["data"], 1):
                        self._ariston_sensors[self._PARAM_COOLING_LAST_24H_LIST][self._VALUE][
                            "Period" + str(iteration)] = item["y3"]
                        sum_obj = sum_obj + item["y3"]
                    self._ariston_sensors[self._PARAM_COOLING_LAST_24H][self._VALUE] = round(sum_obj, 3)
                except KeyError:
                    self._ariston_sensors[self._PARAM_COOLING_LAST_24H][self._VALUE] = None
                    self._ariston_sensors[self._PARAM_COOLING_LAST_24H_LIST][self._VALUE] = None

                try:
                    sum_obj = 0
                    self._ariston_sensors[self._PARAM_WATER_LAST_24H_LIST][self._VALUE] = {}
                    for iteration, item in enumerate(self._ariston_gas_data["daily"]["data"], 1):
                        self._ariston_sensors[self._PARAM_WATER_LAST_24H_LIST][self._VALUE][
                            "Period" + str(iteration)] = item["y"]
                        sum_obj = sum_obj + item["y"]
                    self._ariston_sensors[self._PARAM_WATER_LAST_24H][self._VALUE] = round(sum_obj, 3)
                except KeyError:
                    self._ariston_sensors[self._PARAM_WATER_LAST_24H][self._VALUE] = None
                    self._ariston_sensors[self._PARAM_WATER_LAST_24H_LIST][self._VALUE] = None

                try:
                    sum_obj = 0
                    self._ariston_sensors[self._PARAM_HEATING_LAST_7D_LIST][self._VALUE] = {}
                    for iteration, item in enumerate(self._ariston_gas_data["weekly"]["data"], 1):
                        self._ariston_sensors[self._PARAM_HEATING_LAST_7D_LIST][self._VALUE]["Period" +
                                                                                             str(iteration)] = \
                            item["y2"]
                        sum_obj = sum_obj + item["y2"]
                    self._ariston_sensors[self._PARAM_HEATING_LAST_7D][self._VALUE] = round(sum_obj, 3)
                except KeyError:
                    self._ariston_sensors[self._PARAM_HEATING_LAST_7D][self._VALUE] = None
                    self._ariston_sensors[self._PARAM_HEATING_LAST_7D_LIST][self._VALUE] = None

                try:
                    sum_obj = 0
                    self._ariston_sensors[self._PARAM_COOLING_LAST_7D_LIST][self._VALUE] = {}
                    for iteration, item in enumerate(self._ariston_gas_data["weekly"]["data"], 1):
                        self._ariston_sensors[self._PARAM_COOLING_LAST_7D_LIST][self._VALUE]["Period" +
                                                                                             str(iteration)] = \
                            item["y3"]
                        sum_obj = sum_obj + item["y3"]
                    self._ariston_sensors[self._PARAM_COOLING_LAST_7D][self._VALUE] = round(sum_obj, 3)
                except KeyError:
                    self._ariston_sensors[self._PARAM_COOLING_LAST_7D][self._VALUE] = None
                    self._ariston_sensors[self._PARAM_COOLING_LAST_7D_LIST][self._VALUE] = None

                try:
                    sum_obj = 0
                    self._ariston_sensors[self._PARAM_WATER_LAST_7D_LIST][self._VALUE] = {}
                    for iteration, item in enumerate(self._ariston_gas_data["weekly"]["data"], 1):
                        self._ariston_sensors[self._PARAM_WATER_LAST_7D_LIST][self._VALUE]["Period" +
                                                                                           str(iteration)] = \
                            item["y"]
                        sum_obj = sum_obj + item["y"]
                    self._ariston_sensors[self._PARAM_WATER_LAST_7D][self._VALUE] = round(sum_obj, 3)
                except KeyError:
                    self._ariston_sensors[self._PARAM_WATER_LAST_7D][self._VALUE] = None
                    self._ariston_sensors[self._PARAM_WATER_LAST_7D_LIST][self._VALUE] = None

                try:
                    sum_obj = 0
                    self._ariston_sensors[self._PARAM_HEATING_LAST_30D_LIST][self._VALUE] = {}
                    for iteration, item in enumerate(self._ariston_gas_data["monthly"]["data"], 1):
                        self._ariston_sensors[self._PARAM_HEATING_LAST_30D_LIST][self._VALUE][
                            "Period" + str(iteration)] = item["y2"]
                        sum_obj = sum_obj + item["y2"]
                    self._ariston_sensors[self._PARAM_HEATING_LAST_30D][self._VALUE] = round(sum_obj, 3)
                except KeyError:
                    self._ariston_sensors[self._PARAM_HEATING_LAST_30D][self._VALUE] = None
                    self._ariston_sensors[self._PARAM_HEATING_LAST_30D_LIST][self._VALUE] = None

                try:
                    sum_obj = 0
                    self._ariston_sensors[self._PARAM_COOLING_LAST_30D_LIST][self._VALUE] = {}
                    for iteration, item in enumerate(self._ariston_gas_data["monthly"]["data"], 1):
                        self._ariston_sensors[self._PARAM_COOLING_LAST_30D_LIST][self._VALUE][
                            "Period" + str(iteration)] = item["y3"]
                        sum_obj = sum_obj + item["y3"]
                    self._ariston_sensors[self._PARAM_COOLING_LAST_30D][self._VALUE] = round(sum_obj, 3)
                except KeyError:
                    self._ariston_sensors[self._PARAM_COOLING_LAST_30D][self._VALUE] = None
                    self._ariston_sensors[self._PARAM_COOLING_LAST_30D_LIST][self._VALUE] = None

                try:
                    sum_obj = 0
                    self._ariston_sensors[self._PARAM_WATER_LAST_30D_LIST][self._VALUE] = {}
                    for iteration, item in enumerate(self._ariston_gas_data["monthly"]["data"], 1):
                        self._ariston_sensors[self._PARAM_WATER_LAST_30D_LIST][self._VALUE]["Period" +
                                                                                            str(iteration)] = \
                            item["y"]
                        sum_obj = sum_obj + item["y"]
                    self._ariston_sensors[self._PARAM_WATER_LAST_30D][self._VALUE] = round(sum_obj, 3)
                except KeyError:
                    self._ariston_sensors[self._PARAM_WATER_LAST_30D][self._VALUE] = None
                    self._ariston_sensors[self._PARAM_WATER_LAST_30D_LIST][self._VALUE] = None

                try:
                    sum_obj = 0
                    self._ariston_sensors[self._PARAM_HEATING_LAST_365D_LIST][self._VALUE] = {}
                    for iteration, item in enumerate(self._ariston_gas_data["yearly"]["data"], 1):
                        self._ariston_sensors[self._PARAM_HEATING_LAST_365D_LIST][self._VALUE][
                            "Period" + str(iteration)] = item["y2"]
                        sum_obj = sum_obj + item["y2"]
                    self._ariston_sensors[self._PARAM_HEATING_LAST_365D][self._VALUE] = round(sum_obj, 3)
                except KeyError:
                    self._ariston_sensors[self._PARAM_HEATING_LAST_365D][self._VALUE] = None
                    self._ariston_sensors[self._PARAM_HEATING_LAST_365D_LIST][self._VALUE] = None

                try:
                    sum_obj = 0
                    self._ariston_sensors[self._PARAM_COOLING_LAST_365D_LIST][self._VALUE] = {}
                    for iteration, item in enumerate(self._ariston_gas_data["yearly"]["data"], 1):
                        self._ariston_sensors[self._PARAM_COOLING_LAST_365D_LIST][self._VALUE][
                            "Period" + str(iteration)] = item["y3"]
                        sum_obj = sum_obj + item["y3"]
                    self._ariston_sensors[self._PARAM_COOLING_LAST_365D][self._VALUE] = round(sum_obj, 3)
                except KeyError:
                    self._ariston_sensors[self._PARAM_COOLING_LAST_365D][self._VALUE] = None
                    self._ariston_sensors[self._PARAM_COOLING_LAST_365D_LIST][self._VALUE] = None

                try:
                    sum_obj = 0
                    self._ariston_sensors[self._PARAM_WATER_LAST_365D_LIST][self._VALUE] = {}
                    for iteration, item in enumerate(self._ariston_gas_data["yearly"]["data"], 1):
                        self._ariston_sensors[self._PARAM_WATER_LAST_365D_LIST][self._VALUE]["Period" +
                                                                                             str(iteration)] = \
                            item["y"]
                        sum_obj = sum_obj + item["y"]
                    self._ariston_sensors[self._PARAM_WATER_LAST_365D][self._VALUE] = round(sum_obj, 3)
                except KeyError:
                    self._ariston_sensors[self._PARAM_WATER_LAST_365D][self._VALUE] = None
                    self._ariston_sensors[self._PARAM_WATER_LAST_365D_LIST][self._VALUE] = None

                new_todays_values = dict()
                old_todays_values = dict()

                for today_sensor in self._TODAY_SENSORS:
                    try:
                        if today_sensor == self._PARAM_COOLING_TODAY:
                            key = "y3"
                        elif today_sensor == self._PARAM_HEATING_TODAY:
                            key = "y2"
                        elif today_sensor == self._PARAM_WATER_TODAY:
                            key = "y"
                        else:
                            # Unknown key
                            continue
                        # Store old values
                        old_todays_values[today_sensor] = self._ariston_sensors[today_sensor][self._VALUE]
                        sum_obj = 0
                        start_hour = int(self._ariston_gas_data["daily"]["leftColumnLabel"])
                        use_iterated = False
                        for item in self._ariston_gas_data["daily"]["data"]:
                            if start_hour == 0 or start_hour == 24:
                                use_iterated = True
                            start_hour += 2
                            if use_iterated:
                                sum_obj = sum_obj + item[key]
                        new_todays_values[today_sensor] = round(sum_obj, 3)
                    except KeyError:
                        new_todays_values[today_sensor] = None
                        continue

                if all(new_todays_values[today_sensor] == 0 for today_sensor in self._TODAY_SENSORS):
                    all_zero = True
                else:
                    all_zero = False
                
                for today_sensor in self._TODAY_SENSORS:
                    try:
                        if all_zero and old_todays_values[today_sensor] and self._today_count_ignore < self._MAX_ZERO_TOLERANCE_TODAY_PARAMS:
                            # Use old value if reports are all 0, old value is non-zero and we have not exceeded tolarance
                            self._ariston_sensors[today_sensor][self._VALUE] = old_todays_values[today_sensor]
                            self._today_count_ignore[today_sensor] += 1
                        else:
                            # Use new value
                            self._ariston_sensors[today_sensor][self._VALUE] = new_todays_values[today_sensor]
                            self._today_count_ignore[today_sensor] = 0
                    except:
                        continue

            else:
                for parameter in self._GET_REQUEST_GAS:
                    self._ariston_sensors[parameter][self._VALUE] = None

        if request_type == self._REQUEST_GET_OTHER:

            if self.available and self._ariston_other_data != {}:

                for param_item in self._ariston_other_data:
                    ariston_param = param_item["id"]
                    if ariston_param in self._ARISTON_TO_PARAM:
                        parameter = self._ARISTON_TO_PARAM[ariston_param]
                        try:
                            if parameter in {
                                self._PARAM_INTERNET_TIME,
                                self._ARISTON_INTERNET_WEATHER,
                                self._ARISTON_CH_AUTO_FUNCTION,
                                self._ARISTON_THERMAL_CLEANSE_FUNCTION
                            }:
                                if param_item["value"] == 1:
                                    self._ariston_sensors[parameter][self._VALUE] = True
                                else:
                                    self._ariston_sensors[parameter][self._VALUE] = False
                            elif parameter == self._PARAM_DHW_COMFORT_FUNCTION:
                                 self._ariston_sensors[parameter][self._VALUE] = \
                                     self._DHW_COMFORT_VALUE_TO_FUNCT[param_item["value"]]
                            else:
                                self._ariston_sensors[parameter][self._VALUE] = param_item["value"]
                        except KeyError:
                            self._ariston_sensors[parameter][self._VALUE] = None
                            continue

            else:
                for parameter in self._GET_REQUEST_PARAM:
                    self._ariston_sensors[parameter][self._VALUE] = None

        if request_type == self._REQUEST_GET_UNITS:

            if self._units == self._UNIT_AUTO:
                if self.available and self._ariston_units != {}:
                    try:
                        self._ariston_sensors[self._PARAM_UNITS][self._VALUE] = \
                            self._VALUE_TO_UNIT[self._ariston_units["measurementSystem"]]
                        self._update_units()
                    except KeyError:
                        self._ariston_sensors[self._PARAM_UNITS][self._VALUE] = None
                else:
                    self._ariston_sensors[self._PARAM_UNITS][self._VALUE] = None
            else:
                self._ariston_sensors[self._PARAM_UNITS][self._VALUE] = self._units

            self._set_statuses()

        if request_type == self._REQUEST_GET_CURRENCY:

            if self.available and self._ariston_currency != {}:

                try:
                    type_fetch = next((item for item in self._ariston_currency["gasTypeOptions"] if
                                       item["value"] == self._ariston_currency["gasType"]), {})
                    currency_fetch = next((item for item in self._ariston_currency["gasEnergyUnitOptions"] if
                                           item["value"] == self._ariston_currency["gasEnergyUnit"]), {})
                    self._ariston_sensors[self._PARAM_GAS_TYPE][self._VALUE] = type_fetch["text"]
                    self._ariston_sensors[self._PARAM_GAS_TYPE][self._UNITS] = currency_fetch["text"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_GAS_TYPE][self._VALUE] = None
                    self._ariston_sensors[self._PARAM_GAS_TYPE][self._UNITS] = None

                try:
                    currency_symbol = next((item for item in self._ariston_currency["currencySymbols"] if
                                            item["Key"] == self._ariston_currency["currency"]), {})
                    """
                    currency_description = next((item for item in self._ariston_currency["currencyOptions"] if
                                                 item["value"] == self._ariston_currency["currency"]), {})
                    """
                    if self._ariston_currency["gasCost"] is None:
                        self._ariston_sensors[self._PARAM_GAS_COST][self._VALUE] = None
                        self._ariston_sensors[self._PARAM_GAS_COST][self._UNITS] = None
                    else:
                        self._ariston_sensors[self._PARAM_GAS_COST][self._VALUE] = \
                            str(self._ariston_currency["gasCost"])
                        self._ariston_sensors[self._PARAM_GAS_COST][self._UNITS] = currency_symbol["Value"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_GAS_COST][self._VALUE] = None
                    self._ariston_sensors[self._PARAM_GAS_COST][self._UNITS] = None

                try:
                    currency_symbol = next((item for item in self._ariston_currency["currencySymbols"] if
                                            item["Key"] == self._ariston_currency["currency"]), {})
                    """
                    currency_description = next((item for item in self._ariston_currency["currencyOptions"] if
                                                 item["value"] == self._ariston_currency["currency"]), {})
                    """
                    if self._ariston_currency["gasCost"] is None:
                        self._ariston_sensors[self._PARAM_ELECTRICITY_COST][self._VALUE] = None
                        self._ariston_sensors[self._PARAM_ELECTRICITY_COST][self._UNITS] = None
                    else:
                        self._ariston_sensors[self._PARAM_ELECTRICITY_COST][self._VALUE] = \
                            str(self._ariston_currency["electricityCost"])
                        self._ariston_sensors[self._PARAM_ELECTRICITY_COST][self._UNITS] = currency_symbol["Value"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_ELECTRICITY_COST][self._VALUE] = None
                    self._ariston_sensors[self._PARAM_ELECTRICITY_COST][self._UNITS] = None

            else:
                self._ariston_sensors[self._PARAM_GAS_TYPE][self._VALUE] = None
                self._ariston_sensors[self._PARAM_GAS_COST][self._VALUE] = None
                self._ariston_sensors[self._PARAM_ELECTRICITY_COST][self._VALUE] = None

        if request_type == self._REQUEST_GET_VERSION:
            try:
                if self._version != "":
                    self._ariston_sensors[self._PARAM_ONLINE_VERSION][self._VALUE] = self._version
                    web_version = self._version.split(".")
                    installed_version = self._VERSION.split(".")
                    web_symbols = len(web_version)
                    installed_symbols = len(installed_version)
                    if web_symbols <= installed_symbols:
                        # same amount of symbols to check, update available if web has higher value
                        for symbol in range(0, web_symbols):
                            if int(web_version[symbol]) > int(installed_version[symbol]):
                                self._ariston_sensors[self._PARAM_UPDATE][self._VALUE] = True
                                break
                        else:
                            self._ariston_sensors[self._PARAM_UPDATE][self._VALUE] = False
                    else:
                        # update available if web has higher value
                        self._ariston_sensors[self._PARAM_UPDATE][self._VALUE] = True
                else:
                    self._ariston_sensors[self._PARAM_UPDATE][self._VALUE] = None
                    self._ariston_sensors[self._PARAM_ONLINE_VERSION][self._VALUE] = None

            except KeyError:
                self._ariston_sensors[self._PARAM_UPDATE][self._VALUE] = None
                self._ariston_sensors[self._PARAM_ONLINE_VERSION][self._VALUE] = None

    def _set_visible_data(self, zone_number):
        # set visible values as if they have in fact changed
        for parameter, value in self._set_param.items():
            try:
                if parameter in self._SENSOR_SET_LIST:
                    if parameter in self._ariston_sensors \
                            and self._valid_requests[self._get_request_for_parameter(parameter)]:

                        if self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_MODE:

                            self._ariston_sensors[parameter][self._VALUE] = self._VALUE_TO_MODE[value]

                        elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_CH_MODE:

                            self._ariston_sensors[parameter][self._VALUE] = self._VALUE_TO_CH_MODE[value]

                        elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_CH_SET_TEMPERATURE:

                            self._ariston_sensors[parameter][self._VALUE] = value
                            if self._current_temp_economy_ch[zone_number]:
                                self._ariston_sensors[self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_CH_ECONOMY_TEMPERATURE][zone_number]][self._VALUE] = value
                            elif self._current_temp_economy_ch[zone_number] is False:
                                self._ariston_sensors[self._PARAM_CH_COMFORT_TEMPERATURE][self._VALUE] = value

                        elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_CH_COMFORT_TEMPERATURE:

                            self._ariston_sensors[parameter][self._VALUE] = value
                            if self._current_temp_economy_ch[zone_number] is False:
                                self._ariston_sensors[self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_CH_SET_TEMPERATURE][zone_number]][self._VALUE] = value

                        elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_CH_ECONOMY_TEMPERATURE:

                            self._ariston_sensors[parameter][self._VALUE] = value
                            if self._current_temp_economy_ch[zone_number]:
                                self._ariston_sensors[self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_CH_SET_TEMPERATURE][zone_number]][self._VALUE] = value

                        elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_DHW_SET_TEMPERATURE:

                            self._ariston_sensors[parameter][self._VALUE] = value
                            if self._current_temp_economy_dhw:
                                self._ariston_sensors[self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_DHW_ECONOMY_TEMPERATURE][zone_number]][self._VALUE] = value
                            else:
                                self._ariston_sensors[self._PARAM_DHW_COMFORT_TEMPERATURE][self._VALUE] = value

                        elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_DHW_COMFORT_TEMPERATURE:

                            self._ariston_sensors[parameter][self._VALUE] = value
                            if not self._current_temp_economy_dhw:
                                self._ariston_sensors[self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_DHW_SET_TEMPERATURE][zone_number]][self._VALUE] = value

                        elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_DHW_ECONOMY_TEMPERATURE:

                            self._ariston_sensors[parameter][self._VALUE] = value
                            if self._current_temp_economy_dhw:
                                self._ariston_sensors[self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_DHW_SET_TEMPERATURE][zone_number]][self._VALUE] = value

                        elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_DHW_MODE:

                            self._ariston_sensors[parameter][self._VALUE] = self._VALUE_TO_DHW_MODE[value]

                        elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_DHW_COMFORT_FUNCTION:

                            self._ariston_sensors[parameter][self._VALUE] = self._DHW_COMFORT_VALUE_TO_FUNCT[value]

                        elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_INTERNET_TIME:

                            if value == 1:
                                self._ariston_sensors[parameter][self._VALUE] = True
                            else:
                                self._ariston_sensors[parameter][self._VALUE] = False

                        elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_INTERNET_WEATHER:

                            if value == 1:
                                self._ariston_sensors[parameter][self._VALUE] = True
                            else:
                                self._ariston_sensors[parameter][self._VALUE] = False

                        elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_CH_AUTO_FUNCTION:

                            if value == 1:
                                self._ariston_sensors[parameter][self._VALUE] = True
                            else:
                                self._ariston_sensors[parameter][self._VALUE] = False

                        elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_UNITS:

                            self._ariston_sensors[parameter][self._VALUE] = self._VALUE_TO_UNIT[value]
                            self._update_units()

                        elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_THERMAL_CLEANSE_CYCLE:

                            self._ariston_sensors[parameter][self._VALUE] = value

                        elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_CH_WATER_TEMPERATURE:

                            self._ariston_sensors[parameter][self._VALUE] = value

                        elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_THERMAL_CLEANSE_FUNCTION:

                            if value == 1:
                                self._ariston_sensors[parameter][self._VALUE] = True
                            else:
                                self._ariston_sensors[parameter][self._VALUE] = False

            except KeyError:
                continue

        self._subscribers_sensors_inform()

        if self._store_file:
            if not os.path.isdir(self._store_folder):
                os.makedirs(self._store_folder)
            store_file = self._gw_name + 'data_ariston_temp_main.json'
            store_file_path = os.path.join(self._store_folder, store_file)
            with open(store_file_path, 'w') as ariston_fetched:
                json.dump(self._ariston_data, ariston_fetched)
            store_file = self._gw_name + 'data_ariston_temp_param.json'
            store_file_path = os.path.join(self._store_folder, store_file)
            with open(store_file_path, 'w') as ariston_fetched:
                json.dump(self._ariston_other_data, ariston_fetched)
            store_file = self._gw_name + 'data_ariston_temp_units.json'
            store_file_path = os.path.join(self._store_folder, store_file)
            with open(store_file_path, 'w') as ariston_fetched:
                json.dump(self._ariston_units, ariston_fetched)

    def _store_data(self, resp, request_type="", zone_number=_ZONE_1):
        """Store received dictionary"""
        if resp.status_code != 200:
            if self._store_file:
                if not os.path.isdir(self._store_folder):
                    os.makedirs(self._store_folder)
                store_file = self._gw_name + "data_ariston" + request_type + "_" + str(resp.status_code) + "_error.txt"
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, "w") as f:
                    f.write(resp.text)
            if request_type == self._REQUEST_GET_OTHER and resp.status_code == 500:
                not_supported = set()
                for re_string in re.findall('Violated Postcondition.*menu', resp.text):
                    for menu_item in self._MENU_TO_SENSOR:
                        check_menu = f"&quot;{menu_item}&quot;"
                        if check_menu in re_string:
                            not_supported.add(self._MENU_TO_SENSOR[menu_item])
                if not_supported:
                    self._LOGGER.error('%s Unsupported sensors detected: %s, disable corresponding binary_sensors/sensors/switches in the configuration', self, not_supported)
            self._LOGGER.warning('%s %s invalid reply code %s', self, request_type, resp.status_code)
            raise Exception("Unexpected code {} received for the request {}".format(resp.status_code, request_type))
        if not self._json_validator(resp.json()):
            if self._store_file:
                if not os.path.isdir(self._store_folder):
                    os.makedirs(self._store_folder)
                store_file = self._gw_name + "data_ariston" + request_type + "_non_json_error.txt"
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, "w") as f:
                    f.write(resp.text)
            self._LOGGER.warning('%s %s No json detected', self, request_type)
            raise Exception("JSON did not pass validation for the request {}".format(request_type))
        store_none_zero = False
        last_temp = {}
        last_temp_min = {}
        last_temp_max = {}
        if request_type in {self._REQUEST_GET_MAIN, self._REQUEST_SET_MAIN}:
            """ 
            It happens occasionally that modes are not reported and/or temperatures are not reported.
            If this happens then use last valid value.
            """
            try:
                allowed_modes = \
                    self._ariston_data["allowedModes"]
                last_temp[self._PARAM_DHW_STORAGE_TEMPERATURE] = \
                    self._ariston_data["dhwStorageTemp"]
                last_temp[self._PARAM_DHW_COMFORT_TEMPERATURE] = \
                    self._ariston_data["dhwTimeProgComfortTemp"]["value"]
                last_temp[self._PARAM_DHW_ECONOMY_TEMPERATURE] = \
                    self._ariston_data["dhwTimeProgEconomyTemp"]["value"]
                last_temp[self._PARAM_DHW_SET_TEMPERATURE] = \
                    self._ariston_data["dhwTemp"]["value"]
                last_temp_min[self._PARAM_DHW_COMFORT_TEMPERATURE] = \
                    self._ariston_data["dhwTimeProgComfortTemp"]["min"]
                last_temp_min[self._PARAM_DHW_ECONOMY_TEMPERATURE] = \
                    self._ariston_data["dhwTimeProgEconomyTemp"]["min"]
                last_temp_min[self._PARAM_DHW_SET_TEMPERATURE] = \
                    self._ariston_data["dhwTemp"]["min"]
                last_temp_max[self._PARAM_DHW_COMFORT_TEMPERATURE] = \
                    self._ariston_data["dhwTimeProgComfortTemp"]["max"]
                last_temp_max[self._PARAM_DHW_ECONOMY_TEMPERATURE] = \
                    self._ariston_data["dhwTimeProgEconomyTemp"]["max"]
                last_temp_max[self._PARAM_DHW_SET_TEMPERATURE] = \
                    self._ariston_data["dhwTemp"]["max"]
                allowed_ch_modes = \
                    self._zone_data_main[zone_number]["mode"]["allowedOptions"]
                last_temp_min[self._PARAM_CH_SET_TEMPERATURE] = \
                    self._zone_data_main[zone_number]["comfortTemp"]["min"]
                last_temp_max[self._PARAM_CH_SET_TEMPERATURE] = \
                    self._zone_data_main[zone_number]["comfortTemp"]["max"]
                last_temp[self._PARAM_CH_DETECTED_TEMPERATURE] = \
                    self._zone_data_main[zone_number]["roomTemp"]
                last_temp[self._PARAM_CH_SET_TEMPERATURE] = \
                    self._zone_data_main[zone_number]["desiredTemp"]
            except KeyError:
                # Reading failed or no data was present in the first place
                allowed_modes = []
                allowed_ch_modes = []
                last_temp[self._PARAM_DHW_STORAGE_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp[self._PARAM_DHW_COMFORT_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp[self._PARAM_DHW_ECONOMY_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp[self._PARAM_DHW_SET_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp[self._PARAM_CH_DETECTED_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp[self._PARAM_CH_SET_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp_min[self._PARAM_DHW_COMFORT_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp_min[self._PARAM_DHW_ECONOMY_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp_min[self._PARAM_DHW_SET_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp_min[self._PARAM_CH_SET_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp_max[self._PARAM_DHW_COMFORT_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp_max[self._PARAM_DHW_ECONOMY_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp_max[self._PARAM_DHW_SET_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp_max[self._PARAM_CH_SET_TEMPERATURE] = self._UNKNOWN_TEMP
            try:
                self._ariston_data = copy.deepcopy(resp.json())
                del self._ariston_data["zone"]
                self._zone_data_main[zone_number] = copy.deepcopy(resp.json()["zone"])
                
            except copy.error:
                self._ariston_data = {}
                self._zone_data_main = {
                    self._ZONE_1: dict(),
                    self._ZONE_2: dict(),
                    self._ZONE_3: dict()
                }
                self._set_statuses()
                self._LOGGER.warning("%s Invalid data received for Main, not JSON", self)
                raise Exception("Corruption at reading data of the request {}".format(request_type))
            try:
                # force default modes if received none
                if not self._ariston_data["allowedModes"]:
                    if allowed_modes:
                        self._ariston_data["allowedModes"] = allowed_modes
                    else:
                        self._ariston_data = {}
                        self._zone_data_main = {
                            self._ZONE_1: dict(),
                            self._ZONE_2: dict(),
                            self._ZONE_3: dict()
                        }
                        self._set_statuses()
                        raise Exception("Invalid allowed modes in the request {}".format(request_type))
                # force default CH modes if received none
                if not self._zone_data_main[zone_number]["mode"]["allowedOptions"]:
                    if allowed_ch_modes:
                        self._zone_data_main[zone_number]["mode"]["allowedOptions"] = allowed_ch_modes
                # keep latest DHW storage temperature if received invalid
                if self._ariston_data["dhwStorageTemp"] == self._UNKNOWN_TEMP:
                    if last_temp[self._PARAM_DHW_STORAGE_TEMPERATURE] != self._UNKNOWN_TEMP:
                        self._get_zero_temperature[self._PARAM_DHW_STORAGE_TEMPERATURE] += 1
                        store_none_zero = True
                        if self._get_zero_temperature[self._PARAM_DHW_STORAGE_TEMPERATURE] < self._MAX_ZERO_TOLERANCE:
                            self._ariston_data["dhwStorageTemp"] = last_temp[self._PARAM_DHW_STORAGE_TEMPERATURE]
                else:
                    self._get_zero_temperature[self._PARAM_DHW_STORAGE_TEMPERATURE] = 0
                # keep latest DHW comfort temperature if received invalid
                if self._ariston_data["dhwTimeProgComfortTemp"]["value"] == self._UNKNOWN_TEMP:
                    if last_temp[self._PARAM_DHW_COMFORT_TEMPERATURE] != self._UNKNOWN_TEMP and \
                            last_temp_min[self._PARAM_DHW_COMFORT_TEMPERATURE] != self._UNKNOWN_TEMP and \
                            last_temp_max[self._PARAM_DHW_COMFORT_TEMPERATURE] != self._UNKNOWN_TEMP:
                        self._get_zero_temperature[self._PARAM_DHW_COMFORT_TEMPERATURE] += 1
                        store_none_zero = True
                        if self._get_zero_temperature[self._PARAM_DHW_COMFORT_TEMPERATURE] < self._MAX_ZERO_TOLERANCE:
                            self._ariston_data["dhwTimeProgComfortTemp"]["value"] = last_temp[
                                self._PARAM_DHW_COMFORT_TEMPERATURE]
                else:
                    self._get_zero_temperature[self._PARAM_DHW_COMFORT_TEMPERATURE] = 0
                # keep latest DHW economy temperature if received invalid
                if self._ariston_data["dhwTimeProgEconomyTemp"]["value"] == self._UNKNOWN_TEMP:
                    if last_temp[self._PARAM_DHW_ECONOMY_TEMPERATURE] != self._UNKNOWN_TEMP and \
                            last_temp_min[self._PARAM_DHW_ECONOMY_TEMPERATURE] != self._UNKNOWN_TEMP and \
                            last_temp_max[self._PARAM_DHW_ECONOMY_TEMPERATURE] != self._UNKNOWN_TEMP:
                        self._get_zero_temperature[self._PARAM_DHW_ECONOMY_TEMPERATURE] += 1
                        store_none_zero = True
                        if self._get_zero_temperature[self._PARAM_DHW_ECONOMY_TEMPERATURE] < self._MAX_ZERO_TOLERANCE:
                            self._ariston_data["dhwTimeProgEconomyTemp"]["value"] = last_temp[
                                self._PARAM_DHW_ECONOMY_TEMPERATURE]
                else:
                    self._get_zero_temperature[self._PARAM_DHW_ECONOMY_TEMPERATURE] = 0
                # keep latest DHW set temperature if received invalid
                if self._ariston_data["dhwTemp"]["value"] == self._UNKNOWN_TEMP:
                    if last_temp[self._PARAM_DHW_SET_TEMPERATURE] != self._UNKNOWN_TEMP:
                        self._get_zero_temperature[self._PARAM_DHW_SET_TEMPERATURE] += 1
                        store_none_zero = True
                        if self._get_zero_temperature[self._PARAM_DHW_SET_TEMPERATURE] < self._MAX_ZERO_TOLERANCE:
                            self._ariston_data["dhwTemp"]["value"] = last_temp[
                                self._PARAM_DHW_SET_TEMPERATURE]
                else:
                    self._get_zero_temperature[self._PARAM_DHW_SET_TEMPERATURE] = 0
                # keep latest CH detected temperature if received invalid
                if self._zone_data_main[zone_number]["roomTemp"] == self._UNKNOWN_TEMP:
                    if last_temp[self._PARAM_CH_DETECTED_TEMPERATURE] != self._UNKNOWN_TEMP:
                        self._get_zero_temperature[self._PARAM_CH_DETECTED_TEMPERATURE] += 1
                        store_none_zero = True
                        if self._get_zero_temperature[self._PARAM_CH_DETECTED_TEMPERATURE] < self._MAX_ZERO_TOLERANCE:
                            self._zone_data_main[zone_number]["roomTemp"] = last_temp[
                                self._PARAM_CH_DETECTED_TEMPERATURE]
                else:
                    self._get_zero_temperature[self._PARAM_CH_DETECTED_TEMPERATURE] = 0
                # keep latest CH set temperature if received invalid
                if self._zone_data_main[zone_number]["desiredTemp"] == self._UNKNOWN_TEMP:
                    if last_temp[self._PARAM_CH_SET_TEMPERATURE] != self._UNKNOWN_TEMP:
                        self._get_zero_temperature[self._PARAM_CH_SET_TEMPERATURE] += 1
                        store_none_zero = True
                        if self._get_zero_temperature[self._PARAM_CH_SET_TEMPERATURE] < self._MAX_ZERO_TOLERANCE:
                            self._zone_data_main[zone_number]["desiredTemp"] = last_temp[
                                self._PARAM_CH_SET_TEMPERATURE]
                else:
                    self._get_zero_temperature[self._PARAM_CH_SET_TEMPERATURE] = 0
            except KeyError:
                self._ariston_data = {}
                self._zone_data_main = {
                    self._ZONE_1: dict(),
                    self._ZONE_2: dict(),
                    self._ZONE_3: dict()
                }
                self._set_statuses()
                self._LOGGER.warning("%s Invalid data received for Main", self)
                store_file = self._gw_name + 'main_data_from_web.json'
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, 'w') as ariston_fetched:
                    json.dump(resp.json(), ariston_fetched)
                raise Exception("Corruption at reading data of the request {}".format(request_type))

            self._set_statuses()

            try:
                self._dhw_trend_up = False
                if len(self._dhw_history) > 3:
                    del self._dhw_history[0]
                if self._ariston_data["dhwStorageTemp"] != self._UNKNOWN_TEMP:
                    for dhw_value in reversed(self._dhw_history):
                        if dhw_value != self._UNKNOWN_TEMP:
                            if self._ariston_data["dhwStorageTemp"] < dhw_value:
                                # down trend
                                break
                            elif self._ariston_data["dhwStorageTemp"] > dhw_value:
                                # up trend
                                self._dhw_trend_up = True
                                break
                self._dhw_history.append(self._ariston_data["dhwStorageTemp"])
            except KeyError:
                self._LOGGER.warning('%s Error handling DHW temperature history', self)

            self._set_sensors(request_type, zone_number)
            self._set_sensors(self._REQUEST_GET_VERSION, zone_number)
            self._set_visible_data(zone_number)

        elif request_type == self._REQUEST_GET_CH:
            """ 
            It happens occasionally that temperatures are not reported.
            If this happens then use last valid value.
            """
            try:
                last_temp[self._PARAM_CH_COMFORT_TEMPERATURE] = self._zone_data_ch[zone_number]["comfortTemp"]["value"]
                last_temp[self._PARAM_CH_ECONOMY_TEMPERATURE] = self._zone_data_ch[zone_number]["economyTemp"]["value"]
                last_temp_min[self._PARAM_CH_COMFORT_TEMPERATURE] = self._zone_data_ch[zone_number]["comfortTemp"]["min"]
                last_temp_min[self._PARAM_CH_ECONOMY_TEMPERATURE] = self._zone_data_ch[zone_number]["economyTemp"]["min"]
                last_temp_max[self._PARAM_CH_COMFORT_TEMPERATURE] = self._zone_data_ch[zone_number]["comfortTemp"]["max"]
                last_temp_max[self._PARAM_CH_ECONOMY_TEMPERATURE] = self._zone_data_ch[zone_number]["economyTemp"]["max"]
            except KeyError:
                last_temp[self._PARAM_CH_COMFORT_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp[self._PARAM_CH_ECONOMY_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp_min[self._PARAM_CH_COMFORT_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp_min[self._PARAM_CH_ECONOMY_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp_max[self._PARAM_CH_COMFORT_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp_max[self._PARAM_CH_ECONOMY_TEMPERATURE] = self._UNKNOWN_TEMP
            try:
                self._zone_data_ch[zone_number] = copy.deepcopy(resp.json())
            except copy.error:
                self._zone_data_ch[zone_number] = {}
                self._LOGGER.warning("%s Invalid data received for CH, not JSON", self)
                raise Exception("Corruption at reading data of the request {}".format(request_type))
            try:
                # keep latest CH comfort temperature if received invalid
                if self._zone_data_ch[zone_number]["comfortTemp"]["value"] == self._UNKNOWN_TEMP:
                    if last_temp[self._PARAM_CH_COMFORT_TEMPERATURE] != self._UNKNOWN_TEMP:
                        self._get_zero_temperature[self._PARAM_CH_COMFORT_TEMPERATURE] += 1
                        store_none_zero = True
                        if self._get_zero_temperature[self._PARAM_CH_COMFORT_TEMPERATURE] < self._MAX_ZERO_TOLERANCE:
                            self._zone_data_ch[zone_number]["comfortTemp"]["value"] = last_temp[
                                self._PARAM_CH_COMFORT_TEMPERATURE]
                else:
                    self._get_zero_temperature[self._PARAM_CH_COMFORT_TEMPERATURE] = 0
                # keep latest CH comfort temperature if received invalid
                if self._zone_data_ch[zone_number]["economyTemp"]["value"] == self._UNKNOWN_TEMP:
                    if last_temp[self._PARAM_CH_ECONOMY_TEMPERATURE] != self._UNKNOWN_TEMP:
                        self._get_zero_temperature[self._PARAM_CH_ECONOMY_TEMPERATURE] += 1
                        store_none_zero = True
                        if self._get_zero_temperature[self._PARAM_CH_ECONOMY_TEMPERATURE] < self._MAX_ZERO_TOLERANCE:
                            self._zone_data_ch[zone_number]["economyTemp"]["value"] = last_temp[
                                self._PARAM_CH_ECONOMY_TEMPERATURE]
                    else:
                        self._get_zero_temperature[self._PARAM_CH_ECONOMY_TEMPERATURE] = 0
            except KeyError:
                self._LOGGER.warning("%s Invalid data received for CH", self)
                raise Exception("Corruption at reading data of the request {}".format(request_type))

            self._set_sensors(request_type, zone_number)
            self._set_visible_data(zone_number)

        elif request_type == self._REQUEST_GET_ERROR:

            try:
                self._ariston_error_data = copy.deepcopy(resp.json())
            except copy.error:
                self._ariston_error_data = {}
                self._LOGGER.warning("%s Invalid data received for error, not JSON", self)
                raise Exception("Corruption at reading data of the request {}".format(request_type))

            self._set_sensors(request_type, zone_number)
            self._set_visible_data(zone_number)

        elif request_type == self._REQUEST_GET_GAS:

            try:
                self._ariston_gas_data = copy.deepcopy(resp.json())
            except copy.error:
                self._ariston_gas_data = {}
                self._LOGGER.warning("%s Invalid data received for energy use, not JSON", self)
                raise Exception("Corruption at reading data of the request {}".format(request_type))

            self._set_sensors(request_type, zone_number)
            self._set_visible_data(zone_number)

        elif request_type == self._REQUEST_GET_OTHER:
            """ 
            It happens occasionally that temperatures are not reported.
            If this happens then use last valid value.
            """
            try:
                last_temp[self._PARAM_CH_COMFORT_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp[self._PARAM_CH_ECONOMY_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp_min[self._PARAM_CH_COMFORT_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp_min[self._PARAM_CH_ECONOMY_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp_max[self._PARAM_CH_COMFORT_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp_max[self._PARAM_CH_ECONOMY_TEMPERATURE] = self._UNKNOWN_TEMP
                for param_item in self._ariston_other_data:
                    try:
                        # Copy latest DHW temperatures
                        if param_item["id"] == self._ARISTON_CH_COMFORT_TEMP:
                            last_temp[self._PARAM_CH_COMFORT_TEMPERATURE] = param_item["value"]
                        elif param_item["id"] == self._ARISTON_CH_ECONOMY_TEMP:
                            last_temp[self._PARAM_CH_ECONOMY_TEMPERATURE] = param_item["value"]
                    except KeyError:
                        continue
            except KeyError:
                last_temp[self._PARAM_CH_COMFORT_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp[self._PARAM_CH_ECONOMY_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp_min[self._PARAM_CH_COMFORT_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp_min[self._PARAM_CH_ECONOMY_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp_max[self._PARAM_CH_COMFORT_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp_max[self._PARAM_CH_ECONOMY_TEMPERATURE] = self._UNKNOWN_TEMP
            try:
                self._ariston_other_data = copy.deepcopy(resp.json())
            except copy.error:
                self._ariston_other_data = {}
                self._set_statuses()
                self._LOGGER.warning("%s Invalid data received for parameters, not JSON", self)
                raise Exception("Corruption at reading data of the request {}".format(request_type))

            self._set_statuses()

            for item, param_item in enumerate(self._ariston_other_data):
                try:
                    # Copy latest DHW temperatures
                    if param_item["id"] == self._ARISTON_DHW_TIME_PROG_COMFORT and param_item["value"] != \
                            self._UNKNOWN_TEMP:
                        if "dhwTimeProgComfortTemp" in self._ariston_data and "value" in \
                                self._ariston_data["dhwTimeProgComfortTemp"]:
                            self._ariston_data["dhwTimeProgComfortTemp"]["value"] = param_item["value"]
                            self._ariston_data["dhwTimeProgComfortTemp"]["value"] = param_item["value"]
                    elif param_item["id"] == self._ARISTON_DHW_TIME_PROG_ECONOMY and param_item["value"] != \
                            self._UNKNOWN_TEMP:
                        if "dhwTimeProgEconomyTemp" in self._ariston_data and "value" in \
                                self._ariston_data["dhwTimeProgEconomyTemp"]:
                            self._ariston_data["dhwTimeProgEconomyTemp"]["value"] = param_item["value"]
                            self._ariston_data["dhwTimeProgEconomyTemp"]["value"] = param_item["value"]
                    elif param_item["id"] == self._ARISTON_CH_COMFORT_TEMP:
                        # keep latest CH comfort temperature if received invalid
                        if param_item["value"] == self._UNKNOWN_TEMP:
                            if last_temp[self._PARAM_CH_COMFORT_TEMPERATURE] != self._UNKNOWN_TEMP:
                                self._get_zero_temperature[self._PARAM_CH_COMFORT_TEMPERATURE] += 1
                                store_none_zero = True
                                if self._get_zero_temperature[self._PARAM_CH_COMFORT_TEMPERATURE] < \
                                        self._MAX_ZERO_TOLERANCE:
                                    self._ariston_other_data[item]["value"] = last_temp[
                                        self._PARAM_CH_COMFORT_TEMPERATURE]
                        else:
                            self._get_zero_temperature[self._PARAM_CH_COMFORT_TEMPERATURE] = 0
                    elif param_item["id"] == self._ARISTON_CH_ECONOMY_TEMP:
                        # keep latest CH economy temperature if received invalid
                        if param_item["value"] == self._UNKNOWN_TEMP:
                            if last_temp[self._PARAM_CH_ECONOMY_TEMPERATURE] != self._UNKNOWN_TEMP:
                                self._get_zero_temperature[self._PARAM_CH_ECONOMY_TEMPERATURE] += 1
                                store_none_zero = True
                                if self._get_zero_temperature[self._PARAM_CH_ECONOMY_TEMPERATURE] < \
                                        self._MAX_ZERO_TOLERANCE:
                                    self._ariston_other_data[item]["value"] = last_temp[
                                        self._PARAM_CH_ECONOMY_TEMPERATURE]
                            else:
                                self._get_zero_temperature[self._PARAM_CH_ECONOMY_TEMPERATURE] = 0
                except KeyError:
                    continue

            self._set_sensors(request_type, zone_number)
            self._set_sensors(self._REQUEST_GET_MAIN, zone_number)
            self._set_visible_data(zone_number)

        elif request_type == self._REQUEST_GET_UNITS:
            try:
                self._ariston_units = copy.deepcopy(resp.json())
            except copy.error:
                self._ariston_units = {}
                self._LOGGER.warning("%s Invalid data received for units, not JSON", self)
                raise Exception("Corruption at reading data of the request {}".format(request_type))

            self._set_sensors(request_type, zone_number)
            self._set_visible_data(zone_number)

        elif request_type == self._REQUEST_GET_CURRENCY:
            try:
                self._ariston_currency = copy.deepcopy(resp.json())
            except copy.error:
                self._ariston_currency = {}
                self._LOGGER.warning("%s Invalid data received for currency, not JSON", self)
                raise Exception("Corruption at reading data of the request {}".format(request_type))

            self._set_sensors(request_type, zone_number)
            self._set_visible_data(zone_number)

        elif request_type == self._REQUEST_GET_DHW:
            try:
                self._ariston_dhw_data = copy.deepcopy(resp.json())
            except copy.error:
                self._ariston_dhw_data = {}
                self._LOGGER.warning("%s Invalid data received for DHW, not JSON", self)
                raise Exception("Corruption at reading data of the request {}".format(request_type))

            self._set_sensors(request_type, zone_number)
            self._set_visible_data(zone_number)

        elif request_type == self._REQUEST_GET_VERSION:
            try:
                self._version = resp.json()["info"]["version"]
            except KeyError:
                self._version = ""
                self._LOGGER.warning("%s Invalid version fetched", self)

            self._set_sensors(request_type, zone_number)
            self._set_visible_data(zone_number)

        self._get_time_end[request_type] = time.time()

        if self._store_file:
            if not os.path.isdir(self._store_folder):
                os.makedirs(self._store_folder)
            store_file = self._gw_name + 'data_ariston' + request_type + '.json'
            store_file_path = os.path.join(self._store_folder, store_file)
            with open(store_file_path, 'w') as ariston_fetched:
                if request_type in {self._REQUEST_GET_MAIN, self._REQUEST_SET_MAIN}:
                    json.dump({"ariston": self._ariston_data, "zone": self._zone_data_main}, ariston_fetched)
                elif request_type == self._REQUEST_GET_CH:
                    json.dump(self._zone_data_ch, ariston_fetched)
                elif request_type == self._REQUEST_GET_DHW:
                    json.dump(self._ariston_dhw_data, ariston_fetched)
                elif request_type == self._REQUEST_GET_ERROR:
                    json.dump(self._ariston_error_data, ariston_fetched)
                elif request_type == self._REQUEST_GET_GAS:
                    json.dump(self._ariston_gas_data, ariston_fetched)
                elif request_type == self._REQUEST_GET_OTHER:
                    json.dump(self._ariston_other_data, ariston_fetched)
                elif request_type == self._REQUEST_GET_UNITS:
                    json.dump(self._ariston_units, ariston_fetched)
                elif request_type == self._REQUEST_GET_CURRENCY:
                    json.dump(self._ariston_currency, ariston_fetched)
                elif request_type == self._REQUEST_GET_VERSION:
                    ariston_fetched.write(self._version)
            store_file = self._gw_name + 'data_ariston_timers.json'
            store_file_path = os.path.join(self._store_folder, store_file)
            with open(store_file_path, 'w') as ariston_fetched:
                json.dump([self._set_time_start, self._set_time_end, self._get_time_start, self._get_time_end],
                          ariston_fetched)
            store_file = self._gw_name + 'data_ariston_temp_main.json'
            store_file_path = os.path.join(self._store_folder, store_file)
            with open(store_file_path, 'w') as ariston_fetched:
                json.dump(self._ariston_data, ariston_fetched)
            store_file = self._gw_name + 'data_ariston_temp_param.json'
            store_file_path = os.path.join(self._store_folder, store_file)
            with open(store_file_path, 'w') as ariston_fetched:
                json.dump(self._ariston_other_data, ariston_fetched)
            store_file = self._gw_name + 'data_ariston_temp_units.json'
            store_file_path = os.path.join(self._store_folder, store_file)
            with open(store_file_path, 'w') as ariston_fetched:
                json.dump(self._ariston_units, ariston_fetched)
            store_file = self._gw_name + 'data_ariston_dhw_history.json'
            store_file_path = os.path.join(self._store_folder, store_file)
            with open(store_file_path, 'w') as ariston_fetched:
                json.dump(self._dhw_history, ariston_fetched)
            if store_none_zero:
                store_file = self._gw_name + 'data_ariston' + request_type + '_last_temp.json'
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, 'w') as ariston_fetched:
                    json.dump([last_temp, last_temp_min, last_temp_max], ariston_fetched)
                store_file = self._gw_name + 'data_ariston' + request_type + '_reply_zero.json'
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, 'w') as ariston_fetched:
                    json.dump(resp.json(), ariston_fetched)
                store_file = self._gw_name + 'data_ariston_zero_count.json'
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, 'w') as ariston_fetched:
                    json.dump(self._get_zero_temperature, ariston_fetched)


    def _get_http_data(self, request_type=""):
        """Common fetching of http data"""
        self._login_session()
        if self._login and self._plant_id != "":
            try:
                last_set_of_data = \
                    self._set_time_start[max(self._set_time_start.keys(), key=(lambda k: self._set_time_start[k]))]
            except KeyError:
                last_set_of_data = 0
            if time.time() - last_set_of_data > self._HTTP_TIMER_SET_LOCK:
                # do not read immediately during set attempt
                if request_type == self._REQUEST_GET_CH:
                    url = self._url + '/TimeProg/GetWeeklyPlan/' + self._plant_id
                    http_timeout = self._timeout_medium
                    send_params = self._send_params_get_program()
                elif request_type == self._REQUEST_GET_DHW:
                    url = self._url + '/TimeProg/GetWeeklyPlan/' + self._plant_id + '?progId=Dhw&umsys=si'
                    http_timeout = self._timeout_medium
                    send_params = ['']
                elif request_type == self._REQUEST_GET_ERROR:
                    url = self._url + '/Error/ActiveDataSource/' + self._plant_id + \
                          '?$inlinecount=allpages&$skip=0&$top=100'
                    http_timeout = self._timeout_medium
                    send_params = ['']
                elif request_type == self._REQUEST_GET_GAS:
                    url = self._url + '/Metering/GetData/' + self._plant_id + '?kind=1&umsys=si'
                    http_timeout = self._timeout_medium
                    send_params = ['']
                elif request_type == self._REQUEST_GET_OTHER:
                    list_to_send = [
                        self._ARISTON_DHW_COMFORT_TEMP,
                        self._ARISTON_DHW_COMFORT_FUNCTION,
                        self._ARISTON_CH_COMFORT_TEMP,
                        self._ARISTON_CH_ECONOMY_TEMP,
                        self._ARISTON_CH_AUTO_FUNCTION
                    ]
                    # Add defined sensors
                    if self._param_sensors:
                        for param_to_add in self._param_sensors:
                            if param_to_add not in list_to_send:
                                list_to_send.append(param_to_add)
                    ids_to_fetch = ",".join(map(str, list_to_send))
                    url = self._url + '/Menu/User/Refresh/' + self._plant_id + '?paramIds=' + ids_to_fetch + '&umsys=si'
                    http_timeout = self._timeout_long
                    send_params = ['']
                elif request_type == self._REQUEST_GET_UNITS:
                    url = self._url + '/PlantPreference/GetData/' + self._plant_id
                    http_timeout = self._timeout_short
                    send_params = ['']
                elif request_type == self._REQUEST_GET_CURRENCY:
                    url = self._url + '/Metering/GetCurrencySettings/' + self._plant_id
                    http_timeout = self._timeout_medium
                    send_params = ['']
                elif request_type == self._REQUEST_GET_VERSION:
                    url = self._GITHUB_LATEST_RELEASE
                    http_timeout = self._timeout_short
                    send_params = ['']
                else:
                    url = self._url + '/PlantDashboard/GetPlantData/' + self._plant_id
                    if self.available:
                        http_timeout = self._timeout_long
                    else:
                        # for not available give a bit more time
                        http_timeout = (self._timeout_long + 4)
                    send_params = self._send_params_get_main()
                with self._data_lock:
                    for order, param in enumerate(send_params):
                        current_zone = self._ZONE_ORDER[order]
                        try:
                            self._get_time_start[request_type] = time.time()
                            resp = self._session.get(
                                url + param,
                                auth=self._token,
                                timeout=http_timeout,
                                verify=True)
                        except requests.exceptions.RequestException as ex:
                            self._LOGGER.warning("%s %s Problem reading data: %s", self, request_type, ex)
                            raise Exception("Request {} has failed with an exception".format(request_type))
                        self._store_data(resp, request_type, current_zone)
                        if order + 1 < len(send_params):
                            time.sleep(self._timer_between_param_delay)

            else:
                self._LOGGER.debug("%s %s Still setting data, read restricted", self, request_type)
                return False
        else:
            self._LOGGER.warning("%s %s Not properly logged in to get the data", self, request_type)
            raise Exception("Not logged in to fetch the data")
        self._LOGGER.info(f'Data fetched for {request_type}')
        return True

    def _add_delay(self, req_name):
        delay = 0
        if req_name in {
            self._REQUEST_GET_MAIN,
            self._REQUEST_GET_CH,
            self._REQUEST_SET_MAIN
        }:
            if self._zones > 1:
                delay = self._timer_between_param_delay * (self._zones - 1)
        return delay

    def _queue_get_data(self):
        """Queue all request items"""
        with self._data_lock:
            # schedule next get request
            if self._errors >= self._MAX_ERRORS_TIMER_EXTEND:
                # give a little rest to the system if too many errors
                retry_in = self._timer_between_param_delay * self._HTTP_DELAY_MULTIPLY
                self._timer_between_set = self._timer_between_param_delay * self._HTTP_DELAY_MULTIPLY + \
                                          self._HTTP_TIMER_SET_WAIT
            else:
                # work as usual
                retry_in = self._timer_between_param_delay
                self._timer_between_set = self._timer_between_param_delay + self._HTTP_TIMER_SET_WAIT
            self._timer_periodic_read.cancel()

            try:
                    
                if not self.available or self._errors > 0:
                    # first always initiate main data
                    self._timer_queue_delay.cancel()
                    if self._started:
                        self._timer_queue_delay = threading.Timer(1, self._control_availability_state,
                                                                [self._REQUEST_GET_MAIN])
                        retry_in += self._add_delay(self._REQUEST_GET_MAIN)
                        self._timer_queue_delay.start()
                    # force skip after fetching data
                    self._get_request_number_high_prio = 1
                # next trigger fetching parameters that are being changed
                elif self._set_param_group[self._REQUEST_GET_MAIN]:
                    # setting of main data is ongoing, prioritize it
                    self._timer_queue_delay.cancel()
                    if self._started:
                        self._timer_queue_delay = threading.Timer(1, self._control_availability_state,
                                                                [self._REQUEST_GET_MAIN])
                        retry_in += self._add_delay(self._REQUEST_GET_MAIN)
                        self._timer_queue_delay.start()
                    if not self._set_scheduled:
                        self._set_param_group[self._REQUEST_GET_MAIN] = False
                elif self._set_param_group[self._REQUEST_GET_OTHER]:
                    # setting of parameter data is ongoing, prioritize it
                    self._timer_queue_delay.cancel()
                    if self._started:
                        self._timer_queue_delay = threading.Timer(1, self._control_availability_state,
                                                                [self._REQUEST_GET_OTHER])
                        retry_in += self._add_delay(self._REQUEST_GET_OTHER)
                        self._timer_queue_delay.start()
                    if not self._set_scheduled:
                        self._set_param_group[self._REQUEST_GET_OTHER] = False
                elif self._set_param_group[self._REQUEST_GET_UNITS]:
                    # setting of parameter units is ongoing, prioritize it
                    self._timer_queue_delay.cancel()
                    if self._started:
                        self._timer_queue_delay = threading.Timer(1, self._control_availability_state,
                                                                [self._REQUEST_GET_UNITS])
                        retry_in += self._add_delay(self._REQUEST_GET_UNITS)
                        self._timer_queue_delay.start()
                    if not self._set_scheduled:
                        self._set_param_group[self._REQUEST_GET_UNITS] = False
                else:
                    # last is fetch higher priority list items
                    # select next item from high priority list
                    if self._get_request_number_high_prio < len(self._request_list_high_prio):
                        # item is available in the list
                        self._timer_queue_delay.cancel()
                        if self._started:
                            self._timer_queue_delay = threading.Timer(
                                1, self._control_availability_state,
                                [self._request_list_high_prio[self._get_request_number_high_prio]])
                            retry_in += self._add_delay(self._request_list_high_prio[self._get_request_number_high_prio])
                            self._timer_queue_delay.start()
                        self._get_request_number_high_prio += 1
                    elif self._get_request_number_high_prio > len(self._request_list_high_prio):
                        # start from the beginning of the list
                        self._get_request_number_high_prio = 0
                    else:
                        # third we reserve one place for one of lower priority tasks among higher priority ones
                        self._get_request_number_high_prio += 1
                        if self._errors < self._MAX_ERRORS_TIMER_EXTEND:
                            # skip lower priority requests if too many errors and give time to recover
                            # other data is not that important, so just handle in queue
                            if self._get_request_number_low_prio < len(self._request_list_low_prio):
                                # item is available in the list
                                self._timer_queue_delay.cancel()
                                if self._started:
                                    self._timer_queue_delay = threading.Timer(
                                        1, self._control_availability_state,
                                        [self._request_list_low_prio[self._get_request_number_low_prio]])
                                    retry_in += self._add_delay(self._request_list_low_prio[self._get_request_number_low_prio])
                                    self._timer_queue_delay.start()
                                self._get_request_number_low_prio += 1
                            if self._get_request_number_low_prio >= len(self._request_list_low_prio):
                                self._get_request_number_low_prio = 0
            
            except Exception as ex:
                self._LOGGER.warning(f'Could not handle availability state due to: {ex}')

            if self._started:
                self._LOGGER.info('%s Shall send next request in %s seconds', self, retry_in)
                self._timer_periodic_read = threading.Timer(retry_in, self._queue_get_data)
                self._timer_periodic_read.start()

            if self._store_file:
                if not os.path.isdir(self._store_folder):
                    os.makedirs(self._store_folder)
                store_file = self._gw_name + 'data_ariston_all_set_get.json'
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, 'w') as ariston_fetched:
                    json.dump(self._set_param_group, ariston_fetched)

    def _error_detected(self, request_type):
        """Error detected"""
        if request_type in {self._REQUEST_GET_MAIN, self._REQUEST_SET_MAIN, self._REQUEST_SET_OTHER}:
            with self._lock:
                was_online = self.available
                self._errors += 1
                self._set_statuses()
                self._LOGGER.warning("Connection errors: %i", self._errors)
                offline = not self.available
            if offline and was_online:
                self._clear_data()
                self._LOGGER.error("Ariston is offline: Too many errors")

    def _no_error_detected(self, request_type):
        """No errors detected"""
        if request_type in {self._REQUEST_GET_MAIN, self._REQUEST_SET_MAIN}:
            with self._lock:
                was_offline = not self.available
                self._errors = 0
                self._set_statuses()
            if was_offline:
                self._LOGGER.info("No more errors")

    def _control_availability_state(self, request_type=""):
        """Control component availability"""
        try:
            result_ok = self._get_http_data(request_type)
            self._LOGGER.info(f"ariston action ok for {request_type}")
        except Exception as ex:
            self._error_detected(request_type)
            self._LOGGER.warning(f"ariston action nok for {request_type}: {ex}")
            return
        if result_ok:
            self._no_error_detected(request_type)
        return

    def _setting_http_data(self, set_data, request_type="", zone_number=_ZONE_1):
        """setting of data"""
        self._LOGGER.info('setting http data')
        try:
            if self._store_file:
                if not os.path.isdir(self._store_folder):
                    os.makedirs(self._store_folder)
                if request_type == self._SET_REQUEST_MAIN:
                    store_file = self._gw_name + 'data_ariston' + request_type + zone_number + '.json'
                else:
                    store_file = self._gw_name + 'data_ariston' + request_type + '.json'
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, 'w') as ariston_fetched:
                    json.dump(set_data, ariston_fetched)
                store_file = self._gw_name + 'data_ariston_all_set.json'
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, 'w') as ariston_fetched:
                    json.dump(self._set_param, ariston_fetched)
                store_file = self._gw_name + 'data_ariston_timers.json'
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, 'w') as ariston_fetched:
                    json.dump([self._set_time_start, self._set_time_end, self._get_time_start, self._get_time_end],
                              ariston_fetched)
        except TypeError:
            self._LOGGER.warning('%s Problem storing files', self)

        if request_type == self._REQUEST_SET_OTHER:
            url = self._url + '/Menu/User/Submit/' + self._plant_id + '?umsys=si'
            http_timeout = self._timeout_medium
        elif request_type == self._REQUEST_SET_UNITS:
            url = self._url + '/PlantPreference/SetData/' + self._plant_id
            http_timeout = self._timeout_short
        else:
            url = self._url + '/PlantDashboard/SetPlantAndZoneData/' + self._plant_id + self._send_params_set(zone_number)
            http_timeout = self._timeout_long
        try:
            self._set_time_start[request_type] = time.time()
            resp = self._session.post(
                url,
                auth=self._token,
                timeout=http_timeout,
                json=set_data,
                verify=True)
        except requests.exceptions.RequestException:
            self._error_detected(request_type)
            self._LOGGER.warning('%s %s error', self, request_type)
            raise Exception("Unexpected error for setting in the request {}".format(request_type))
        if resp.status_code != 200:
            self._error_detected(request_type)
            if self._store_file:
                if not os.path.isdir(self._store_folder):
                    os.makedirs(self._store_folder)
                store_file = self._gw_name + "data_ariston" + request_type + "_" + str(resp.status_code) + "_error.txt"
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, "w") as f:
                    f.write(resp.text)
            self._LOGGER.warning("%s %s Command to set data failed with code: %s", self, request_type, resp.status_code)
            raise Exception("Unexpected code {} for setting in the request {}".format(resp.status_code, request_type))
        self._set_time_end[request_type] = time.time()
        self._no_error_detected(request_type)
        if request_type == self._REQUEST_SET_MAIN:
            """
            data in reply cannot be fully trusted as occasionally we receive changed data but on next read turns out 
            that it was in fact not changed, so uncomment below on your own risk
            """
            # self._store_data(resp, request_type, zone_num)
            if self._store_file:
                if not os.path.isdir(self._store_folder):
                    os.makedirs(self._store_folder)
                if request_type == self._SET_REQUEST_MAIN:
                    store_file = self._gw_name + "data_ariston" + request_type + zone_number + "_reply.txt"
                else:
                    store_file = self._gw_name + "data_ariston" + request_type + "_reply.txt"
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, "w") as f:
                    f.write(resp.text)
        self._LOGGER.info('%s %s Data was presumably changed', self, request_type)

    def _preparing_setting_http_data(self):
        """Preparing and setting http data"""
        self._login_session()
        with self._data_lock:
            if not self._set_new_data_pending:
                # initiated from schedule, no longer scheduled
                self._set_scheduled = False
            else:
                # initiated from set_http_data, no longer pending
                self._set_new_data_pending = False
                for request_item in self._set_retry:
                    self._set_retry[request_item] = 0
                if self._set_scheduled:
                    # we wait for another attempt after timeout, data will be set then
                    return
            if self._login and self.available and self._plant_id != "":

                changed_parameter = {
                    self._REQUEST_SET_MAIN: {},
                    self._REQUEST_SET_OTHER: {},
                    self._REQUEST_SET_UNITS: {}
                }

                zone_changes = set()
                for key in self._set_param:
                    if key in self._SET_REQUEST_MAIN:
                        for zone in reversed(self._ZONE_ORDER):
                            if zone != self._ZONE_1:
                                if key.endswith(zone):
                                    zone_changes.add(zone)
                                    break
                            else:
                                zone_changes.add(self._ZONE_1)

                for zone in self._ZONE_ORDER:
                    if not zone_changes:
                        zone_number = self._ZONE_1
                        break
                    elif zone in zone_changes:
                        zone_number = zone
                        break

                set_data = dict()
                # prepare setting of main data dictionary
                set_data["NewValue"] = copy.deepcopy(self._ariston_data)
                set_data["OldValue"] = copy.deepcopy(self._ariston_data)
                set_data["NewValue"]["zone"] = copy.deepcopy(self._zone_data_main[zone_number])
                set_data["OldValue"]["zone"] = copy.deepcopy(self._zone_data_main[zone_number])

                # Format is received in 12H format but for some reason python must send 24H format, not other tools
                try:
                    set_data["NewValue"]["zone"]["derogaUntil"] = self._change_to_24h_format(
                        self._zone_data_main[zone_number]["derogaUntil"])
                    set_data["OldValue"]["zone"]["derogaUntil"] = self._change_to_24h_format(
                        self._zone_data_main[zone_number]["derogaUntil"])
                except KeyError:
                    set_data["NewValue"]["zone"]["derogaUntil"] = self._DEFAULT_TIME
                    set_data["OldValue"]["zone"]["derogaUntil"] = self._DEFAULT_TIME

                set_units_data = {}
                try:
                    set_units_data["measurementSystem"] = self._ariston_units["measurementSystem"]
                except KeyError:
                    set_units_data["measurementSystem"] = self._UNKNOWN_UNITS

                dhw_temp = {}
                dhw_temp_time = {}
                try:
                    dhw_temp[self._PARAM_DHW_COMFORT_TEMPERATURE] = self._UNKNOWN_TEMP
                    dhw_temp[self._PARAM_DHW_ECONOMY_TEMPERATURE] = self._UNKNOWN_TEMP
                    dhw_temp_time[self._PARAM_DHW_COMFORT_TEMPERATURE] = 0
                    dhw_temp_time[self._PARAM_DHW_ECONOMY_TEMPERATURE] = 0
                    if self._get_time_end[self._REQUEST_GET_MAIN] > self._get_time_end[self._REQUEST_GET_OTHER] and \
                            self._get_zero_temperature[self._PARAM_DHW_COMFORT_TEMPERATURE] == 0:
                        if set_data["NewValue"]["dhwTimeProgSupported"]:
                            dhw_temp[self._PARAM_DHW_COMFORT_TEMPERATURE] = \
                                set_data["NewValue"]["dhwTimeProgComfortTemp"]["value"]
                            dhw_temp_time[self._PARAM_DHW_COMFORT_TEMPERATURE] = \
                                self._get_time_end[self._REQUEST_GET_MAIN]
                        else:
                            dhw_temp[self._PARAM_DHW_COMFORT_TEMPERATURE] = set_data["NewValue"]["dhwTemp"]["value"]
                            dhw_temp_time[self._PARAM_DHW_COMFORT_TEMPERATURE] = \
                                self._get_time_end[self._REQUEST_GET_MAIN]
                    else:
                        for param_item in self._ariston_other_data:
                            if param_item["id"] == self._ARISTON_DHW_TIME_PROG_COMFORT:
                                dhw_temp[self._PARAM_DHW_COMFORT_TEMPERATURE] = param_item["value"]
                                dhw_temp_time[self._PARAM_DHW_COMFORT_TEMPERATURE] = \
                                    self._get_time_end[self._REQUEST_GET_OTHER]

                    if self._get_time_end[self._REQUEST_GET_MAIN] > self._get_time_end[self._REQUEST_GET_OTHER] and \
                            self._get_zero_temperature[self._PARAM_DHW_ECONOMY_TEMPERATURE] == 0 \
                            and set_data["NewValue"]["dhwTimeProgSupported"]:
                        dhw_temp[self._PARAM_DHW_ECONOMY_TEMPERATURE] = set_data["NewValue"]["dhwTimeProgEconomyTemp"][
                            "value"]
                        dhw_temp_time[self._PARAM_DHW_ECONOMY_TEMPERATURE] = self._get_time_end[self._REQUEST_GET_MAIN]
                    else:
                        for param_item in self._ariston_other_data:
                            if param_item["id"] == self._ARISTON_DHW_TIME_PROG_ECONOMY:
                                dhw_temp[self._PARAM_DHW_ECONOMY_TEMPERATURE] = param_item["value"]
                                dhw_temp_time[self._PARAM_DHW_ECONOMY_TEMPERATURE] = \
                                    self._get_time_end[self._REQUEST_GET_OTHER]

                except KeyError:
                    dhw_temp[self._PARAM_DHW_COMFORT_TEMPERATURE] = self._UNKNOWN_TEMP
                    dhw_temp[self._PARAM_DHW_ECONOMY_TEMPERATURE] = self._UNKNOWN_TEMP
                    dhw_temp_time[self._PARAM_DHW_COMFORT_TEMPERATURE] = 0
                    dhw_temp_time[self._PARAM_DHW_ECONOMY_TEMPERATURE] = 0

                # prepare setting of parameter data dictionary
                set_param_data = []

                temp_dict = copy.deepcopy(self._set_param)

                for parameter in temp_dict:

                    if self._MAP_PARAM_NAME_TO_ZONE_NUMBER[parameter] == zone_number and \
                        self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] in {
                        self._PARAM_MODE,
                        self._PARAM_CH_MODE,
                        self._PARAM_DHW_MODE,
                    }:
                        checked_param = self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL]
                        if checked_param == self._PARAM_MODE:
                            temp_dict = set_data["NewValue"]
                            temp_key = "mode"
                        elif checked_param == self._PARAM_CH_MODE:
                            temp_dict = set_data["NewValue"]["zone"]["mode"]
                            temp_key = "value"
                        elif checked_param == self._PARAM_DHW_MODE:
                            temp_dict = set_data["NewValue"]
                            temp_key = "dhwMode"

                        if temp_dict[temp_key] == self._set_param[parameter]:
                            if self._set_time_start[self._set_request_for_parameter(parameter)] < \
                                    self._get_time_end[self._get_request_for_parameter(parameter)]:
                                # value should be up to date and match to remove from setting
                                del self._set_param[parameter]
                            else:
                                # assume data was not yet changed
                                changed_parameter[self._set_request_for_parameter(parameter)][
                                    self._get_request_for_parameter(parameter)] = True
                        else:
                            temp_dict[temp_key] = self._set_param[parameter]
                            changed_parameter[self._set_request_for_parameter(parameter)][
                                self._get_request_for_parameter(parameter)] = True

                    elif self._MAP_PARAM_NAME_TO_ZONE_NUMBER[parameter] == zone_number and \
                        self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] in {
                        self._PARAM_DHW_COMFORT_TEMPERATURE,
                        self._PARAM_DHW_ECONOMY_TEMPERATURE,
                    }:

                        checked_param = self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL]
                        if checked_param == self._PARAM_DHW_COMFORT_TEMPERATURE:
                            temp_value = set_data["NewValue"]["dhwTimeProgComfortTemp"]["value"]
                        elif checked_param == self._PARAM_DHW_ECONOMY_TEMPERATURE:
                            temp_value = set_data["NewValue"]["dhwTimeProgEconomyTemp"]["value"]

                        if math.isclose(
                                dhw_temp[parameter],
                                self._set_param[parameter],
                                abs_tol=0.01):
                            if self._set_time_start[self._set_request_for_parameter(parameter)] <\
                                    dhw_temp_time[parameter]:
                                # value should be up to date and match to remove from setting
                                del self._set_param[parameter]
                            else:
                                # assume data was not yet changed
                                param_data = {
                                    "id": self._PARAM_TO_ARISTON[parameter],
                                    "newValue": self._set_param[parameter],
                                    "oldValue": temp_value}
                                set_param_data.append(param_data)
                                changed_parameter[self._set_request_for_parameter(parameter)][
                                    self._get_request_for_parameter(parameter)] = True
                        else:
                            param_data = {
                                "id": self._PARAM_TO_ARISTON[parameter],
                                "newValue": self._set_param[parameter],
                                "oldValue": temp_value}
                            set_param_data.append(param_data)
                            changed_parameter[self._set_request_for_parameter(parameter)][
                                self._get_request_for_parameter(parameter)] = True

                    elif self._MAP_PARAM_NAME_TO_ZONE_NUMBER[parameter] == zone_number and \
                        self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] in {
                        self._PARAM_CH_SET_TEMPERATURE,
                        self._PARAM_DHW_SET_TEMPERATURE,
                    }:

                        checked_param = self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL]
                        if checked_param == self._PARAM_CH_SET_TEMPERATURE:
                            temp_dict = set_data["NewValue"]["zone"]
                            temp_key = "desiredTemp"
                        elif checked_param == self._PARAM_DHW_SET_TEMPERATURE:
                            temp_dict = set_data["NewValue"]["dhwTemp"]
                            temp_key = "value"

                        if math.isclose(
                                set_data["NewValue"]["zone"]["desiredTemp"],
                                self._set_param[parameter],
                                abs_tol=0.01):
                            if self._set_time_start[self._set_request_for_parameter(parameter)] < \
                                    self._get_time_end[self._get_request_for_parameter(parameter)] and\
                                    self._get_zero_temperature[parameter] == 0:
                                # value should be up to date and match to remove from setting
                                del self._set_param[parameter]
                            else:
                                # assume data was not yet changed
                                changed_parameter[self._set_request_for_parameter(parameter)][
                                    self._get_request_for_parameter(parameter)] = True
                        else:
                            set_data["NewValue"]["zone"]["desiredTemp"] = \
                                self._set_param[parameter]
                            changed_parameter[self._set_request_for_parameter(parameter)][
                                self._get_request_for_parameter(parameter)] = True


                    elif self._MAP_PARAM_NAME_TO_ZONE_NUMBER[parameter] == zone_number and \
                        self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] in {
                        self._PARAM_THERMAL_CLEANSE_CYCLE,
                        self._PARAM_CH_WATER_TEMPERATURE,
                        self._PARAM_CH_COMFORT_TEMPERATURE,
                        self._PARAM_CH_ECONOMY_TEMPERATURE,
                    }:

                        try:
                            for param_item in self._ariston_other_data:
                                if param_item["id"] == self._PARAM_TO_ARISTON[parameter]:
                                    if math.isclose(
                                            param_item["value"],
                                            self._set_param[parameter],
                                            abs_tol=0.01):
                                        if self._set_time_start[self._set_request_for_parameter(
                                                parameter)] < \
                                                self._get_time_end[
                                                    self._get_request_for_parameter(parameter)]:
                                            # value should be up to date and match to remove from setting
                                            del self._set_param[parameter]
                                        else:
                                            # assume data was not yet changed
                                            param_data = {
                                                "id": self._PARAM_TO_ARISTON[parameter],
                                                "newValue": self._set_param[parameter],
                                                "oldValue": param_item["value"]}
                                            set_param_data.append(param_data)
                                            changed_parameter[self._set_request_for_parameter(
                                                parameter)][
                                                self._get_request_for_parameter(parameter)] = True
                                        break
                                    else:
                                        param_data = {
                                            "id": self._PARAM_TO_ARISTON[parameter],
                                            "newValue": self._set_param[parameter],
                                            "oldValue": param_item["value"]}
                                        set_param_data.append(param_data)
                                        changed_parameter[self._set_request_for_parameter(
                                            parameter)][
                                            self._get_request_for_parameter(parameter)] = True
                                        break
                        except KeyError:
                            changed_parameter[self._set_request_for_parameter(parameter)][
                                self._get_request_for_parameter(parameter)] = True

                    elif self._MAP_PARAM_NAME_TO_ZONE_NUMBER[parameter] == zone_number and \
                        self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] in {
                        self._PARAM_DHW_COMFORT_FUNCTION,
                        self._PARAM_INTERNET_TIME,
                        self._PARAM_INTERNET_WEATHER,
                        self._PARAM_THERMAL_CLEANSE_FUNCTION,
                        self._PARAM_CH_AUTO_FUNCTION,
                    }:

                        try:
                            for param_item in self._ariston_other_data:
                                if param_item["id"] == self._PARAM_TO_ARISTON[parameter]:
                                    if param_item["value"] == self._set_param[parameter]:
                                        if self._set_time_start[self._set_request_for_parameter(
                                                parameter)] < \
                                                self._get_time_end[self._get_request_for_parameter(
                                                    parameter)]:
                                            # value should be up to date and match to remove from setting
                                            del self._set_param[parameter]
                                        else:
                                            # assume data was not yet changed
                                            param_data = {
                                                "id": self._PARAM_TO_ARISTON[parameter],
                                                "newValue": self._set_param[parameter],
                                                "oldValue": param_item["value"]}
                                            set_param_data.append(param_data)
                                            changed_parameter[self._set_request_for_parameter(
                                                parameter)][self._get_request_for_parameter(
                                                    parameter)] = True
                                        break
                                    else:
                                        param_data = {
                                            "id": self._PARAM_TO_ARISTON[parameter],
                                            "newValue": self._set_param[parameter],
                                            "oldValue": param_item["value"]}
                                        set_param_data.append(param_data)
                                        changed_parameter[self._set_request_for_parameter(
                                            parameter)][
                                            self._get_request_for_parameter(parameter)] = True
                                        break
                        except KeyError:
                            changed_parameter[self._set_request_for_parameter(parameter)][
                                self._get_request_for_parameter(parameter)] = True

                    elif self._MAP_PARAM_NAME_TO_ZONE_NUMBER[parameter] == zone_number and \
                        self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_UNITS:

                        if set_units_data["measurementSystem"] == self._set_param[parameter]:
                            if self._set_time_start[self._set_request_for_parameter(parameter)] < \
                                    self._get_time_end[self._get_request_for_parameter(parameter)]:
                                # value should be up to date and match to remove from setting
                                del self._set_param[parameter]
                            else:
                                # assume data was not yet changed
                                changed_parameter[self._set_request_for_parameter(parameter)][
                                    self._get_request_for_parameter(parameter)] = True
                        else:
                            set_units_data["measurementSystem"] = self._set_param[parameter]
                            changed_parameter[self._set_request_for_parameter(parameter)][
                                self._get_request_for_parameter(parameter)] = True

                for request_item in self._set_param_group:
                    self._set_param_group[request_item] = False

                for key, value in changed_parameter.items():
                    if value != {} and self._set_retry[key] < self._set_max_retries:
                        if not self._set_scheduled:
                            # retry again after enough time
                            retry_in = self._timer_between_set
                            self._timer_periodic_set.cancel()
                            if self._started:
                                self._timer_periodic_set = threading.Timer(retry_in, self._preparing_setting_http_data)
                                self._timer_periodic_set.start()
                            self._set_retry[key] += 1
                            self._set_scheduled = True
                    elif value != {} and self._set_retry[key] == self._set_max_retries:
                        # last retry, we keep changed parameter but do not schedule anything
                        self._set_retry[key] += 1
                    else:
                        changed_parameter[key] = {}

                try:
                    for parameter, value in self._set_param.items():
                        if self._get_request_for_parameter(parameter) not in \
                                changed_parameter[self._set_request_for_parameter(parameter)]:
                            del self._set_param[parameter]
                except KeyError:
                    self._LOGGER.warning('%s Can not clear set parameters', self)

                # show data as changed in case we were able to read data in between requests
                self._set_visible_data(zone_number)

                if changed_parameter[self._REQUEST_SET_MAIN] != {}:
                    try:
                        self._setting_http_data(set_data, self._REQUEST_SET_MAIN, zone_number)
                    except TypeError:
                        self._LOGGER.warning('%s Setting main data failed', self)
                    except requests.exceptions.RequestException:
                        self._LOGGER.warning('%s Setting main data failed', self)
                    except Exception:
                        self._LOGGER.warning('%s Setting main data failed with code', self)

                elif changed_parameter[self._REQUEST_SET_OTHER] != {}:

                    try:
                        if set_param_data:
                            self._setting_http_data(set_param_data, self._REQUEST_SET_OTHER, zone_number)
                        else:
                            self._LOGGER.warning('%s No valid data to set parameters', self)
                    except TypeError:
                        self._LOGGER.warning('%s Setting parameter data failed', self)
                    except requests.exceptions.RequestException:
                        self._LOGGER.warning('%s Setting parameter data failed', self)
                    except Exception:
                        self._LOGGER.warning('%s Setting parameter data failed with code', self)

                elif changed_parameter[self._REQUEST_SET_UNITS]:
                    try:
                        self._setting_http_data(set_units_data, self._REQUEST_SET_UNITS, zone_number)
                    except TypeError:
                        self._LOGGER.warning('%s Setting units data failed', self)
                    except requests.exceptions.RequestException:
                        self._LOGGER.warning('%s Setting units data failed', self)
                    except Exception:
                        self._LOGGER.warning('%s Setting parameter data failed with code', self)

                else:
                    self._LOGGER.debug('%s Same data was used', self)

                for key, value in changed_parameter.items():
                    if value != {}:
                        for request_item in value:
                            self._set_param_group[request_item] = True

                if not self._set_scheduled:
                    # no more retries or no changes, no need to keep any changed data
                    self._set_param = {}
                    self._set_statuses()

                if self._store_file:
                    if not os.path.isdir(self._store_folder):
                        os.makedirs(self._store_folder)
                    store_file = self._gw_name + 'data_ariston_all_set_get.json'
                    store_file_path = os.path.join(self._store_folder, store_file)
                    with open(store_file_path, 'w') as ariston_fetched:
                        json.dump(self._set_param_group, ariston_fetched)
                    store_file = self._gw_name + 'data_ariston_all_set.json'
                    store_file_path = os.path.join(self._store_folder, store_file)
                    with open(store_file_path, 'w') as ariston_fetched:
                        json.dump(self._set_param, ariston_fetched)

            else:
                # api is down
                if not self._set_scheduled:
                    if self._set_retry[self._REQUEST_SET_MAIN] < self._set_max_retries:
                        # retry again after enough time to fetch data twice
                        retry_in = self._timer_between_set
                        self._timer_periodic_set.cancel()
                        if self._started:
                            self._timer_periodic_set = threading.Timer(retry_in, self._preparing_setting_http_data)
                            self._timer_periodic_set.start()
                        self._set_retry[self._REQUEST_SET_MAIN] += 1
                        self._set_scheduled = True
                    else:
                        # no more retries, no need to keep changed data
                        self._set_param = {}
                        self._set_statuses()

                        for request_item in self._set_param_group:
                            self._set_param_group[request_item] = False

                        self._LOGGER.warning("%s No stable connection to set the data", self)
                        raise Exception("Unstable connection to set the data")

    def _check_if_dhw_economy(self):
        try:
            dhw_params = [
                self._PARAM_DHW_SET_TEMPERATURE,
                self._PARAM_DHW_COMFORT_TEMPERATURE,
                self._PARAM_DHW_ECONOMY_TEMPERATURE
            ]
            if any([i in self._set_param for i in dhw_params]) and self._current_temp_economy_dhw is not None:
                # data is still changing, assume it is the least value
                return self._current_temp_economy_dhw
            if self._ariston_data != {}:
                if self._VALUE_TO_DHW_MODE[self._ariston_data["dhwMode"]] == self._VAL_PROGRAM:
                    if not self._ariston_data["dhwTimeProgComfortActive"]:
                        # economy temperature is being used
                        self._current_temp_economy_dhw = True
                    else:
                        self._current_temp_economy_dhw = False
                else:
                    self._current_temp_economy_dhw = False
            else:
                self._current_temp_economy_dhw = None
        except KeyError:
            self._current_temp_economy_dhw = None
        return self._current_temp_economy_dhw

    def _check_if_ch_economy(self, zone_number):
        try:
            ch_params = [
                self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_CH_SET_TEMPERATURE][zone_number],
                self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_CH_COMFORT_TEMPERATURE][zone_number],
                self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_CH_ECONOMY_TEMPERATURE][zone_number]
            ]
            if any([i in self._set_param for i in ch_params]) and self._current_temp_economy_ch[zone_number] is not None:
                # data is still changing, assume it is the least value
                return self._current_temp_economy_ch[zone_number]
            if self._ariston_other_data != {} and self._ariston_data != {}:
                if self._VALUE_TO_CH_MODE[self._zone_data_main[zone_number]["mode"]["value"]] == self._VAL_PROGRAM:
                    for param_item in self._ariston_other_data:
                        if param_item["id"] == self._ARISTON_CH_ECONOMY_TEMP:
                            if math.isclose(
                                    self._zone_data_main[zone_number]["desiredTemp"],
                                    param_item["value"],
                                    abs_tol=0.01):
                                self._current_temp_economy_ch[zone_number] = True
                                break
                        else:
                            self._current_temp_economy_ch[zone_number] = False
                else:
                    self._current_temp_economy_ch[zone_number] = False
            else:
                self._current_temp_economy_ch[zone_number] = None
        except KeyError:
            self._current_temp_economy_ch[zone_number] = None
        return self._current_temp_economy_ch[zone_number]

    def set_http_data(self, **parameter_list: Union[str, int, float, bool]) -> None:
        """
        Set data over http, where **parameter_list excepts parameters and wanted values.

        Supported parameters:
            - 'mode'
            - 'ch_mode'
            - 'ch_mode_zone_2'
            - 'ch_mode_zone_3'
            - 'ch_set_temperature'
            - 'ch_set_temperature_zone_2'
            - 'ch_set_temperature_zone_3'
            - 'ch_comfort_temperature'
            - 'ch_comfort_temperature_zone_2'
            - 'ch_comfort_temperature_zone_3'
            - 'ch_economy_temperature'
            - 'ch_economy_temperature_zone_2'
            - 'ch_economy_temperature_zone_3'
            - 'ch_auto_function'
            - 'ch_water_temperature'
            - 'dhw_mode'
            - 'dhw_set_temperature'
            - 'dhw_comfort_temperature'
            - 'dhw_economy_temperature'
            - 'dhw_comfort_function'
            - 'internet_time'
            - 'internet_weather'
            - 'dhw_thermal_cleanse_function'
            - 'dhw_thermal_cleanse_cycle'
            - 'units'

        Supported values must be viewed in the property 'supported_sensors_set_values',
        which are generated dynamically based on reported values.

        Example:
            set_http_data(mode='off',internet_time=True)
        """

        if self._ariston_data != {}:
            with self._data_lock:

                allowed_values = self.supported_sensors_set_values
                good_values = {}
                bad_values = {}
                for parameter in parameter_list:
                    value = parameter_list[parameter]
                    try:
                        good_parameter = False
                        if self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] in {
                            self._PARAM_MODE,
                            self._PARAM_CH_MODE,
                            self._PARAM_CH_AUTO_FUNCTION,
                            self._PARAM_DHW_MODE,
                            self._PARAM_DHW_COMFORT_FUNCTION,
                            self._PARAM_INTERNET_TIME,
                            self._PARAM_INTERNET_WEATHER,
                            self._PARAM_THERMAL_CLEANSE_FUNCTION,
                            self._PARAM_UNITS
                        }:
                            value = str(value).lower()
                            if value in allowed_values[parameter]:
                                good_values[parameter] = value
                                good_parameter = True
                        elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] in {
                            self._PARAM_CH_SET_TEMPERATURE,
                            self._PARAM_CH_COMFORT_TEMPERATURE,
                            self._PARAM_CH_ECONOMY_TEMPERATURE,
                            self._PARAM_DHW_SET_TEMPERATURE,
                            self._PARAM_DHW_COMFORT_TEMPERATURE,
                            self._PARAM_DHW_ECONOMY_TEMPERATURE,
                            self._PARAM_THERMAL_CLEANSE_CYCLE,
                            self._PARAM_CH_WATER_TEMPERATURE
                        }:
                            value = float(value)
                            if allowed_values[parameter]["min"] - 0.01 <= value \
                                    <= allowed_values[parameter]["max"] + 0.01:
                                good_values[parameter] = value
                                good_parameter = True
                        if not good_parameter:
                            bad_values[parameter] = value
                    except KeyError:
                        bad_values[parameter] = value
                        continue

                for parameter in good_values:

                    zone_number = self._MAP_PARAM_NAME_TO_ZONE_NUMBER[parameter]

                    # check mode and set it
                    if self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_MODE:
                        try:
                            self._set_param[parameter] = self._MODE_TO_VALUE[good_values[parameter]]
                            self._LOGGER.info('%s New mode %s', self, good_values[parameter])
                        except KeyError:
                            self._LOGGER.warning('%s Unknown or unsupported mode or key error: %s', self,
                                            good_values[parameter])
                            bad_values[parameter] = good_values[parameter]

                    # check CH temperature
                    elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_CH_SET_TEMPERATURE:
                        try:
                            # round to nearest 0.5
                            temperature = round(float(good_values[parameter]) * 2.0) / 2.0
                            self._check_if_ch_economy(zone_number)
                            if self._current_temp_economy_ch[zone_number]:
                                self._set_param[self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_CH_ECONOMY_TEMPERATURE][zone_number]] = temperature
                                self._LOGGER.info('%s New economy CH temperature %s', self, temperature)
                            elif self._current_temp_economy_ch[zone_number] is False:
                                self._set_param[self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_CH_COMFORT_TEMPERATURE][zone_number]] = temperature
                                self._LOGGER.info('%s New comfort CH temperature %s', self, temperature)
                            else:
                                # None value
                                self._set_param[parameter] = temperature
                                self._LOGGER.info('%s New CH temperature %s', self, temperature)
                        except KeyError:
                            self._LOGGER.warning('%s Not supported CH temperature value: %s', self,
                                            good_values[parameter])
                            bad_values[parameter] = good_values[parameter]

                    # check dhw temperature
                    elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_DHW_SET_TEMPERATURE:
                        try:
                            # round to nearest 1
                            temperature = round(float(good_values[parameter]))
                            self._check_if_dhw_economy()
                            if self._current_temp_economy_dhw:
                                self._set_param[self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_DHW_ECONOMY_TEMPERATURE][zone_number]] = temperature
                            else:
                                self._set_param[self._MAP_PARAM_NAME_TO_ZONE_PARAM_NAME[self._PARAM_DHW_COMFORT_TEMPERATURE][zone_number]] = temperature
                            self._LOGGER.info('%s New DHW temperature %s', self, temperature)
                        except KeyError:
                            self._LOGGER.warning('%s Not supported DHW temperature value: %s', self,
                                            good_values[parameter])
                            bad_values[parameter] = good_values[parameter]

                    # check dhw comfort temperature
                    elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_DHW_COMFORT_TEMPERATURE:
                        try:
                            # round to nearest 1
                            temperature = round(float(good_values[parameter]))
                            self._set_param[parameter] = temperature
                            self._LOGGER.info('%s New DHW scheduled comfort temperature %s', self,
                                        good_values[parameter])
                            self._check_if_dhw_economy()
                        except KeyError:
                            self._LOGGER.warning('%s Not supported DHW scheduled comfort temperature value: %s', self,
                                            good_values[parameter])
                            bad_values[parameter] = \
                                good_values[parameter]

                    # check dhw economy temperature
                    elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_DHW_ECONOMY_TEMPERATURE:
                        try:
                            # round to nearest 1
                            temperature = round(float(good_values[parameter]))
                            self._set_param[parameter] = temperature
                            self._LOGGER.info('%s New DHW scheduled economy temperature %s', self, temperature)
                            self._check_if_dhw_economy()
                        except KeyError:
                            self._LOGGER.warning('%s Not supported DHW scheduled economy temperature value: %s', self,
                                            good_values[parameter])
                            bad_values[parameter] = \
                                good_values[parameter]

                    # check CH comfort scheduled temperature
                    elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_CH_COMFORT_TEMPERATURE:
                        try:
                            # round to nearest 0.5
                            temperature = round(float(good_values[parameter]) * 2.0) / 2.0
                            self._set_param[parameter] = temperature
                            self._LOGGER.info('%s New CH temperature %s', self, temperature)
                            self._check_if_ch_economy(zone_number)
                        except KeyError:
                            self._LOGGER.warning('%s Not supported CH comfort scheduled temperature value: %s', self,
                                            good_values[parameter])
                            bad_values[parameter] = \
                                good_values[parameter]

                    # check CH economy scheduled temperature
                    elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_CH_ECONOMY_TEMPERATURE:
                        try:
                            # round to nearest 0.5
                            temperature = round(float(good_values[parameter]) * 2.0) / 2.0
                            self._set_param[parameter] = temperature
                            self._LOGGER.info('%s New CH temperature %s', self, temperature)
                            self._check_if_ch_economy(zone_number)
                        except KeyError:
                            self._LOGGER.warning('%s Not supported CH economy scheduled temperature value: %s', self,
                                            good_values[parameter])
                            bad_values[parameter] = \
                                good_values[parameter]

                    # check CH mode
                    elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_CH_MODE:
                        try:
                            self._set_param[parameter] = self._CH_MODE_TO_VALUE[good_values[parameter]]
                            self._LOGGER.info('%s New CH mode %s', self, good_values[parameter])
                        except KeyError:
                            self._LOGGER.warning('%s Unknown or unsupported CH mode or key error: %s', self,
                                            good_values[parameter])
                            bad_values[parameter] = good_values[parameter]

                    # check DHW mode
                    elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_DHW_MODE:
                        try:
                            self._set_param[parameter] = self._DHW_MODE_TO_VALUE[parameter]
                            self._LOGGER.info('%s New DHW mode %s', self, good_values[parameter])
                        except KeyError:
                            self._LOGGER.warning('%s Unknown or unsupported DHW mode or key error: %s', self,
                                            good_values[parameter])
                            bad_values[parameter] = good_values[parameter]

                    # check DHW Comfort mode
                    elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_DHW_COMFORT_FUNCTION:
                        try:
                            self._set_param[parameter] = \
                                self._DHW_COMFORT_FUNCT_TO_VALUE[good_values[parameter]]
                            self._LOGGER.info('%s New DHW Comfort function %s', self,
                                        good_values[parameter])
                        except KeyError:
                            self._LOGGER.warning('%s Unknown or unsupported DHW Comfort function or key error: %s', self,
                                            good_values[parameter])
                            bad_values[parameter] = good_values[parameter]

                    # check internet time
                    elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_INTERNET_TIME:
                        try:
                            self._set_param[parameter] = \
                                self._PARAM_STRING_TO_VALUE[good_values[parameter]]
                            self._LOGGER.info('%s New Internet time is %s', self, good_values[parameter])
                        except KeyError:
                            self._LOGGER.warning('%s Unknown or unsupported Internet time or key error: %s', self,
                                            good_values[parameter])
                            bad_values[parameter] = good_values[parameter]

                    # check internet time
                    elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_INTERNET_WEATHER:
                        try:
                            self._set_param[parameter] = \
                                self._PARAM_STRING_TO_VALUE[good_values[parameter]]
                            self._LOGGER.info('%s New Internet weather is %s', self, good_values[parameter])
                        except KeyError:
                            self._LOGGER.warning('%s Unknown or unsupported Internet weather or key error: %s', self,
                                            good_values[parameter])
                            bad_values[parameter] = good_values[parameter]

                    # check cleanse cycle
                    elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_THERMAL_CLEANSE_CYCLE:
                        try:
                            item_present = False
                            for param_item in self._ariston_other_data:
                                if param_item["id"] == self._PARAM_TO_ARISTON[parameter]:
                                    self._set_param[parameter] = \
                                        good_values[parameter]
                                    item_present = True
                                    self._LOGGER.info('%s New Thermal Cleanse Cycle is %s', self,
                                                good_values[parameter])
                                    break
                            if not item_present:
                                self._LOGGER.warning('%s Can not set Thermal Cleanse Cycle: %s', self,
                                                good_values[parameter])
                                bad_values[parameter] = \
                                    good_values[parameter]
                        except KeyError:
                            self._LOGGER.warning('%s Unknown or unsupported Thermal Cleanse Cycle or key error: %s', self,
                                            good_values[parameter])
                            bad_values[parameter] = good_values[parameter]

                    # check ch water temperature
                    elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_CH_WATER_TEMPERATURE:
                        try:
                            item_present = False
                            for param_item in self._ariston_other_data:
                                if param_item["id"] == self._PARAM_TO_ARISTON[parameter]:
                                    self._set_param[parameter] = \
                                        good_values[parameter]
                                    item_present = True
                                    self._LOGGER.info('%s New CH water temperature is %s', self,
                                                good_values[parameter])
                                    break
                            if not item_present:
                                self._LOGGER.warning('%s Can not set CH water temperature: %s', self,
                                                good_values[parameter])
                                bad_values[parameter] = \
                                    good_values[parameter]
                        except KeyError:
                            self._LOGGER.warning('%s Unknown or unsupported CH water temperature or key error: %s', self,
                                            good_values[parameter])
                            bad_values[parameter] = good_values[parameter]

                    # check cleanse function
                    elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_THERMAL_CLEANSE_FUNCTION:
                        try:
                            item_present = False
                            for param_item in self._ariston_other_data:
                                if param_item["id"] == self._PARAM_TO_ARISTON[parameter]:
                                    self._set_param[parameter] = \
                                        self._PARAM_STRING_TO_VALUE[good_values[parameter]]
                                    item_present = True
                                    self._LOGGER.info('%s New Thermal Cleanse Function is %s', self,
                                                good_values[parameter])
                                    break
                            if not item_present:
                                self._LOGGER.warning('%s Can not set Thermal Cleanse Function: %s', self,
                                                good_values[parameter])
                                bad_values[parameter] = \
                                    good_values[parameter]
                        except KeyError:
                            self._LOGGER.warning('%s Unknown or unsupported Thermal Cleanse Function or key error: %s', self,
                                            good_values[parameter])
                            bad_values[parameter] = \
                                good_values[parameter]

                    # check CH auto function
                    elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_CH_AUTO_FUNCTION:
                        try:
                            self._set_param[parameter] = \
                                self._PARAM_STRING_TO_VALUE[good_values[parameter]]
                            self._LOGGER.info('%s New Internet weather is %s', self,
                                        good_values[parameter])
                        except KeyError:
                            self._LOGGER.warning('%s Unknown or unsupported CH auto function or key error: %s', self,
                                            good_values[parameter])
                            bad_values[parameter] = good_values[parameter]

                    # check units of measurement
                    elif self._MAP_ZONE_TO_ORIGINAL_PARAM[parameter][self._SUB_ORIGINAL] == self._PARAM_UNITS:
                        try:
                            self._set_param[parameter] = self._UNIT_TO_VALUE[good_values[parameter]]
                            self._LOGGER.info('%s New units of measurement is %s', self, good_values[parameter])
                        except KeyError:
                            self._LOGGER.warning('%s Unknown or unsupported units of measurement or key error: %s', self,
                                            good_values[parameter])
                            bad_values[parameter] = good_values[parameter]

                    # show data as changed
                    self._set_visible_data(zone_number)

                self._set_statuses()

                self._set_new_data_pending = True
                # set after short delay to not affect switch or climate or water_heater
                self._timer_set_delay.cancel()
                if self._started:
                    self._timer_set_delay = threading.Timer(1, self._preparing_setting_http_data)
                    self._timer_set_delay.start()

                if bad_values != {}:
                    raise Exception("Following values could not be set: {}".format(bad_values))

        else:
            self._LOGGER.warning("%s No valid data fetched from server to set changes", self)
            raise Exception("Connection data error, problem to set data")

    def _clear_data(self):
        with self._plant_id_lock:
            self._login = False
        self._ariston_data = {}
        self._ariston_gas_data = {}
        self._ariston_error_data = {}
        self._ariston_dhw_data = {}
        self._ariston_currency = {}
        self._ariston_other_data = {}
        self._ariston_units = {}
        self._zone_data_ch = {
            self._ZONE_1: dict(),
            self._ZONE_2: dict(),
            self._ZONE_3: dict()
        }
        self._zone_data_main = {
            self._ZONE_1: dict(),
            self._ZONE_2: dict(),
            self._ZONE_3: dict()
        }
        for today_param in self._TODAY_SENSORS:
            self._today_count_ignore[today_param] = 0
        for sensor in self._SENSOR_LIST:
            if sensor in self._ariston_sensors and sensor != self._PARAM_UNITS:
                self._ariston_sensors[sensor][self._VALUE] = None
        self._subscribers_sensors_inform()

    def start(self) -> None:
        """Start communication with the server."""
        self._timer_periodic_read = threading.Timer(1, self._queue_get_data)
        self._timer_periodic_read.start()
        self._started = True
        self._LOGGER.info("Connection started")

    def stop(self) -> None:
        """Stop communication with the server."""
        self._started = False
        self._timer_periodic_read.cancel()
        self._timer_queue_delay.cancel()
        self._timer_periodic_set.cancel()
        self._timer_set_delay.cancel()

        if self._login and self.available:
            url = self._url + "/Account/Logout"
            try:
                self._session.post(
                    url,
                    auth=self._token,
                    timeout=self._HTTP_TIMEOUT_LOGIN,
                    json={},
                    verify=True)
            except requests.exceptions.RequestException:
                self._LOGGER.warning('%s Logout error', self)
        self._session.close()
        self._clear_data()
        self._set_statuses()
        self._LOGGER.info("Connection stopped")
