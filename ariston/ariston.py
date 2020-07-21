"""Suppoort for Ariston."""
import copy
import json
import logging
import math
import os
import threading
import time
from typing import Union
import requests


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

    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    _VERSION = "1.0.16"

    _LOGGER = logging.getLogger(__name__)

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
    _MAX_ERRORS_TIMER_EXTEND = 5
    _MAX_ZERO_TOLERANCE = 10
    _HTTP_DELAY_MULTIPLY = 3
    _HTTP_TIMER_SET_LOCK = 25
    _HTTP_TIMER_SET_WAIT = 30
    _HTTP_TIMEOUT_LOGIN = 5.0
    _HTTP_TIMEOUT_GET_LONG = 16.0
    _HTTP_TIMEOUT_GET_MEDIUM = 10.0
    _HTTP_TIMEOUT_GET_SHORT = 6.0
    _HTTP_PARAM_DELAY = 30.0

    # Conversions between parameters
    _MODE_TO_VALUE = {_VAL_WINTER: 1, _VAL_SUMMER: 0, _VAL_OFF: 5, _VAL_HEATING_ONLY: 2}
    _VALUE_TO_MODE = {1: _VAL_WINTER, 0: _VAL_SUMMER, 5: _VAL_OFF, 2: _VAL_HEATING_ONLY}
    _CH_MODE_TO_VALUE = {_VAL_MANUAL: 2, _VAL_PROGRAM: 3, _VAL_UNKNOWN: 0}
    _VALUE_TO_CH_MODE = {2: _VAL_MANUAL, 3: _VAL_PROGRAM, 0: _VAL_UNKNOWN}
    _DHW_MODE_TO_VALUE = {_VAL_MANUAL: 2, _VAL_PROGRAM: 1, _VAL_DEFAULT: 0}
    _VALUE_TO_DHW_MODE = {2: _VAL_MANUAL, 1: _VAL_PROGRAM, 0: _VAL_DEFAULT, -1: _VAL_UNSUPPORTED}
    _DHW_COMFORT_FUNCT_TO_VALUE = {_VAL_DISABLED: 0, _VAL_TIME_BASED: 1, _VAL_ALWAYS_ACTIVE: 2}
    _DHW_COMFORT_VALUE_TO_FUNCT = {0: _VAL_DISABLED, 1: _VAL_TIME_BASED, 2: _VAL_ALWAYS_ACTIVE}
    _UNIT_TO_VALUE = {_VAL_METRIC: 0, _VAL_IMPERIAL: 1}
    _VALUE_TO_UNIT = {0: _VAL_METRIC, 1: _VAL_IMPERIAL}
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
    _ARISTON_CH_ECONOMY_TEMP = "U6_3_1_0_1"
    _ARISTON_CH_AUTO_FUNCTION = "U6_3_3"
    _ARISTON_THERMAL_CLEANSE_FUNCTION = "U6_9_5_0"
    _ARISTON_THERMAL_CLEANSE_CYCLE = "U6_9_5_1"
    _ARISTON_S_W_FUNCTION_ACTIVATION = "U6_3_5_0_0"
    _ARISTON_S_W_TEMPERATURE_THRESHOLD = "U6_3_5_0_1"
    _ARISTON_S_W_DELAY_TIME = "U6_3_5_0_2"
    _ARISTON_CH_COMFORT_TEMP_ZONE_2 = "U6_3_1_1_0"
    _ARISTON_CH_ECONOMY_TEMP_ZONE_2 = "U6_3_1_1_1"
    _ARISTON_CH_COMFORT_TEMP_ZONE_3 = "U6_3_1_2_0"
    _ARISTON_CH_ECONOMY_TEMP_ZONE_3 = "U6_3_1_2_1"
    _ARISTON_S_W_FUNCTION_ACTIVATION_ZONE_2 = "U6_3_5_1_0"
    _ARISTON_S_W_TEMPERATURE_THRESHOLD_ZONE_2 = "U6_3_5_1_1"
    _ARISTON_S_W_DELAY_TIME_ZONE_2 = "U6_3_5_1_2"
    _ARISTON_S_W_FUNCTION_ACTIVATION_ZONE_3 = "U6_3_5_2_0"
    _ARISTON_S_W_TEMPERATURE_THRESHOLD_ZONE_3 = "U6_3_5_2_1"
    _ARISTON_S_W_DELAY_TIME_ZONE_3 = "U6_3_5_2_2"

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

    # Mapping of parameter to request
    _GET_REQUEST_CH_PROGRAM = {
        _PARAM_CH_PROGRAM
    }
    _GET_REQUEST_CURRENCY = {
        _PARAM_GAS_TYPE,
        _PARAM_GAS_COST,
        _PARAM_ELECTRICITY_COST
    }
    _GET_REQUEST_DHW_PROGRAM = {
        _PARAM_DHW_PROGRAM
    }
    _GET_REQUEST_ERRORS = {
        _PARAM_ERRORS,
        _PARAM_ERRORS_COUNT
    }
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
        _PARAM_WATER_LAST_24H,
        _PARAM_WATER_LAST_7D,
        _PARAM_WATER_LAST_30D,
        _PARAM_WATER_LAST_365D,
        _PARAM_WATER_LAST_24H_LIST,
        _PARAM_WATER_LAST_7D_LIST,
        _PARAM_WATER_LAST_30D_LIST,
        _PARAM_WATER_LAST_365D_LIST
    }
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
    _GET_REQUEST_PARAM = {
        _PARAM_INTERNET_TIME,
        _PARAM_INTERNET_WEATHER,
        _PARAM_THERMAL_CLEANSE_FUNCTION,
        _PARAM_CH_AUTO_FUNCTION,
        _PARAM_DHW_COMFORT_FUNCTION,
        _PARAM_CH_COMFORT_TEMPERATURE,
        _PARAM_CH_ECONOMY_TEMPERATURE,
        _PARAM_SIGNAL_STRENGTH,
        _PARAM_THERMAL_CLEANSE_CYCLE
    }
    _GET_REQUEST_UNITS = {
        _PARAM_UNITS
    }
    _GET_REQUEST_VERSION = {
        _PARAM_UPDATE,
        _PARAM_ONLINE_VERSION
    }

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
        _PARAM_THERMAL_CLEANSE_CYCLE
    }
    _SET_REQUEST_UNITS = {
        _PARAM_UNITS
    }

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
        _PARAM_THERMAL_CLEANSE_FUNCTION
    }

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
            self._ariston_sensors[self._PARAM_CH_ANTIFREEZE_TEMPERATURE][self._UNITS] = '°F'
            self._ariston_sensors[self._PARAM_CH_DETECTED_TEMPERATURE][self._UNITS] = '°F'
            self._ariston_sensors[self._PARAM_CH_SET_TEMPERATURE][self._UNITS] = '°F'
            self._ariston_sensors[self._PARAM_CH_COMFORT_TEMPERATURE][self._UNITS] = '°F'
            self._ariston_sensors[self._PARAM_CH_ECONOMY_TEMPERATURE][self._UNITS] = '°F'
            self._ariston_sensors[self._PARAM_DHW_SET_TEMPERATURE][self._UNITS] = '°F'
            self._ariston_sensors[self._PARAM_DHW_STORAGE_TEMPERATURE][self._UNITS] = '°F'
            self._ariston_sensors[self._PARAM_DHW_COMFORT_TEMPERATURE][self._UNITS] = '°F'
            self._ariston_sensors[self._PARAM_DHW_ECONOMY_TEMPERATURE][self._UNITS] = '°F'
            self._ariston_sensors[self._PARAM_OUTSIDE_TEMPERATURE][self._UNITS] = '°F'
            self._ariston_sensors[self._PARAM_ACCOUNT_CH_GAS][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_ACCOUNT_DHW_GAS][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_ACCOUNT_CH_ELECTRICITY][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_ACCOUNT_DHW_ELECTRICITY][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_HEATING_LAST_24H][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_HEATING_LAST_7D][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_HEATING_LAST_30D][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_HEATING_LAST_365D][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_WATER_LAST_24H][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_WATER_LAST_7D][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_WATER_LAST_30D][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_WATER_LAST_365D][self._UNITS] = 'kBtuh'
            self._ariston_sensors[self._PARAM_SIGNAL_STRENGTH][self._UNITS] = '%'
            self._ariston_sensors[self._PARAM_THERMAL_CLEANSE_CYCLE][self._UNITS] = 'h'
        elif self._ariston_sensors[self._PARAM_UNITS][self._VALUE] == self._VAL_METRIC:
            self._ariston_sensors[self._PARAM_CH_ANTIFREEZE_TEMPERATURE][self._UNITS] = '°C'
            self._ariston_sensors[self._PARAM_CH_DETECTED_TEMPERATURE][self._UNITS] = '°C'
            self._ariston_sensors[self._PARAM_CH_SET_TEMPERATURE][self._UNITS] = '°C'
            self._ariston_sensors[self._PARAM_CH_COMFORT_TEMPERATURE][self._UNITS] = '°C'
            self._ariston_sensors[self._PARAM_CH_ECONOMY_TEMPERATURE][self._UNITS] = '°C'
            self._ariston_sensors[self._PARAM_DHW_SET_TEMPERATURE][self._UNITS] = '°C'
            self._ariston_sensors[self._PARAM_DHW_STORAGE_TEMPERATURE][self._UNITS] = '°C'
            self._ariston_sensors[self._PARAM_DHW_COMFORT_TEMPERATURE][self._UNITS] = '°C'
            self._ariston_sensors[self._PARAM_DHW_ECONOMY_TEMPERATURE][self._UNITS] = '°C'
            self._ariston_sensors[self._PARAM_OUTSIDE_TEMPERATURE][self._UNITS] = '°C'
            self._ariston_sensors[self._PARAM_ACCOUNT_CH_GAS][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_ACCOUNT_DHW_GAS][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_ACCOUNT_CH_ELECTRICITY][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_ACCOUNT_DHW_ELECTRICITY][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_HEATING_LAST_24H][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_HEATING_LAST_7D][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_HEATING_LAST_30D][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_HEATING_LAST_365D][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_WATER_LAST_24H][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_WATER_LAST_7D][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_WATER_LAST_30D][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_WATER_LAST_365D][self._UNITS] = 'kWh'
            self._ariston_sensors[self._PARAM_SIGNAL_STRENGTH][self._UNITS] = '%'
            self._ariston_sensors[self._PARAM_THERMAL_CLEANSE_CYCLE][self._UNITS] = 'h'

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
                 ) -> None:
        """
        Initialize API.
        """
        if sensors is None:
            sensors = []

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

        if sensors:
            for sensor in sensors:
                if sensor not in self._SENSOR_LIST:
                    sensors.remove(sensor)

        if store_file:
            if store_folder != "":
                self._store_folder = store_folder
            else:
                self._store_folder = os.path.join(os.getcwd(), self._FILE_FOLDER)
            if not os.path.isdir(self._store_folder):
                os.mkdir(self._store_folder)
        else:
            self._store_folder = ""

        # clear read sensor values
        self._ariston_sensors = {}
        for sensor in self._SENSOR_LIST:
            self._ariston_sensors[sensor] = {}
            self._ariston_sensors[sensor][self._VALUE] = None
            self._ariston_sensors[sensor][self._UNITS] = None

        if units in {self._UNIT_METRIC, self._UNIT_IMPERIAL}:
            self._ariston_sensors[self._PARAM_UNITS][self._VALUE] = units

        # clear configuration data
        self._ariston_data = {}
        self._ariston_gas_data = {}
        self._ariston_error_data = {}
        self._ariston_ch_data = {}
        self._ariston_dhw_data = {}
        self._ariston_currency = {}
        self._ariston_other_data = {}
        self._ariston_units = {}
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

        self._token_lock = threading.Lock()
        self._token = None
        self._units = units
        self._url = self._ARISTON_URL
        self._user = username
        self._verify = True
        self._version = ""
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

        self._current_temp_economy_ch = None
        self._current_temp_economy_dhw = None

        self._started = False

        if self._store_file:
            store_file = 'data_ariston_valid_requests.json'
            store_file_path = os.path.join(self._store_folder, store_file)
            with open(store_file_path, 'w') as ariston_fetched:
                json.dump(self._valid_requests, ariston_fetched)

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

    @property
    def available(self) -> bool:
        """Return if Aristons's API is responding."""
        return self._errors <= self._MAX_ERRORS and self._login and self._plant_id != "" and self._ariston_data != {}

    @property
    def ch_available(self) -> bool:
        """Return if Aristons's API is responding and if there is data available for the CH."""
        if self._ariston_sensors[self._PARAM_UNITS][self._VALUE] not in {self._VAL_METRIC, self._VAL_IMPERIAL}:
            return False
        if self._ariston_other_data == {}:
            return False
        return self.available and self._ariston_data["zone"]["mode"]["allowedOptions"] != []

    @property
    def dhw_available(self) -> bool:
        """Return if Aristons's API is responding and if there is data available for the DHW."""
        if self._ariston_sensors[self._PARAM_UNITS][self._VALUE] not in {self._VAL_METRIC, self._VAL_IMPERIAL}:
            return False
        if self._ariston_other_data == {}:
            return False
        return self.available

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
        return self._set_param != {}

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
            if parameter == self._PARAM_MODE:
                param_values = set()
                if self._ariston_data != {}:
                    for value in self._ariston_data["allowedModes"]:
                        if value in self._VALUE_TO_MODE:
                            param_values.add(self._VALUE_TO_MODE[value])
                sensors_dictionary[parameter] = param_values
            elif parameter == self._PARAM_CH_MODE:
                param_values = set()
                if self._ariston_data != {}:
                    for value in self._ariston_data["zone"]["mode"]["allowedOptions"]:
                        if value in self._VALUE_TO_CH_MODE:
                            param_values.add(self._VALUE_TO_CH_MODE[value])
                sensors_dictionary[parameter] = param_values
            elif parameter == self._PARAM_CH_SET_TEMPERATURE:
                param_values = dict()
                if self._ariston_data != {}:
                    param_values["min"] = self._ariston_data["zone"]["comfortTemp"]["min"]
                    param_values["max"] = self._ariston_data["zone"]["comfortTemp"]["max"]
                    param_values["step"] = 0.5
                sensors_dictionary[parameter] = param_values
            elif parameter == self._PARAM_CH_COMFORT_TEMPERATURE:
                param_values = dict()
                if self._ariston_data != {}:
                    param_values["min"] = self._ariston_data["zone"]["comfortTemp"]["min"]
                    param_values["max"] = self._ariston_data["zone"]["comfortTemp"]["max"]
                    param_values["step"] = 0.5
                sensors_dictionary[parameter] = param_values
            elif parameter == self._PARAM_CH_ECONOMY_TEMPERATURE:
                param_values = dict()
                if self._ariston_data != {}:
                    param_values["min"] = self._ariston_data["zone"]["comfortTemp"]["min"]
                    param_values["max"] = self._ariston_data["zone"]["comfortTemp"]["max"]
                    param_values["step"] = 0.5
                sensors_dictionary[parameter] = param_values
            elif parameter == self._PARAM_CH_AUTO_FUNCTION:
                sensors_dictionary[parameter] = [*self._PARAM_STRING_TO_VALUE]
            elif parameter == self._PARAM_DHW_SET_TEMPERATURE:
                param_values = dict()
                if self._ariston_data != {}:
                    param_values["min"] = self._ariston_data["dhwTemp"]["min"]
                    param_values["max"] = self._ariston_data["dhwTemp"]["max"]
                    param_values["step"] = 1
                sensors_dictionary[parameter] = param_values
            elif parameter == self._PARAM_DHW_COMFORT_TEMPERATURE:
                param_values = dict()
                if self._ariston_data != {}:
                    param_values["min"] = max(self._ariston_data["dhwTemp"]["min"],
                                              self._ariston_data["dhwTimeProgComfortTemp"]["min"])
                    param_values["max"] = max(self._ariston_data["dhwTemp"]["max"],
                                              self._ariston_data["dhwTimeProgComfortTemp"]["max"])
                    param_values["step"] = 1
                sensors_dictionary[parameter] = param_values
            elif parameter == self._PARAM_DHW_ECONOMY_TEMPERATURE:
                param_values = dict()
                if self._ariston_data != {}:
                    param_values["min"] = self._ariston_data["dhwTemp"]["min"]
                    param_values["max"] = self._ariston_data["dhwTemp"]["max"]
                    param_values["step"] = 1
                sensors_dictionary[parameter] = param_values
            elif parameter == self._PARAM_DHW_MODE:
                param_values = set()
                if self._ariston_data != {}:
                    if not self._ariston_data["dhwModeNotChangeable"]:
                        param_values = {self._VAL_MANUAL, self._VAL_PROGRAM}
                sensors_dictionary[parameter] = param_values
            elif parameter == self._PARAM_DHW_COMFORT_FUNCTION:
                sensors_dictionary[parameter] = [*self._DHW_COMFORT_FUNCT_TO_VALUE]
            elif parameter == self._PARAM_INTERNET_TIME:
                sensors_dictionary[parameter] = [*self._PARAM_STRING_TO_VALUE]
            elif parameter == self._PARAM_INTERNET_WEATHER:
                sensors_dictionary[parameter] = [*self._PARAM_STRING_TO_VALUE]
            elif parameter == self._PARAM_UNITS:
                sensors_dictionary[parameter] = [*self._UNIT_TO_VALUE]
            elif parameter == self._PARAM_THERMAL_CLEANSE_CYCLE:
                param_values = dict()
                if self._ariston_other_data != {}:
                    for param_item in self._ariston_other_data:
                        if param_item["id"] == self._ARISTON_THERMAL_CLEANSE_CYCLE:
                            param_values["min"] = param_item["min"]
                            param_values["max"] = param_item["max"]
                            param_values["step"] = 1.
                sensors_dictionary[parameter] = param_values
            elif parameter == self._PARAM_THERMAL_CLEANSE_FUNCTION:
                sensors_dictionary[parameter] = [*self._PARAM_STRING_TO_VALUE]
        return sensors_dictionary

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
                self._LOGGER.warning('%s Unexpected reply during login: %s', self, resp.status_code)
                raise Exception("Login unexpected reply code")
            if resp.url.startswith(self._url + "/PlantDashboard/Index/") or resp.url.startswith(
                    self._url + "/PlantManagement/Index/") or resp.url.startswith(
                    self._url + "/PlantPreference/Index/") or resp.url.startswith(
                    self._url + "/Error/Active/") or resp.url.startswith(
                    self._url + "/PlantGuest/Index/") or resp.url.startswith(
                    self._url + "/TimeProg/Index/"):
                with self._plant_id_lock:
                    self._plant_id = resp.url.split("/")[5]
                    self._login = True
                    self._LOGGER.info('%s Plant ID is %s', self, self._plant_id)
            elif resp.url.startswith(self._url + "/PlantData/Index/") or resp.url.startswith(
                    self._url + "/UserData/Index/"):
                with self._plant_id_lock:
                    plant_id_attribute = resp.url.split("/")[5]
                    self._plant_id = plant_id_attribute.split("?")[0]
                    self._login = True
                    self._LOGGER.info('%s Plant ID is %s', self, self._plant_id)
            elif resp.url.startswith(self._url + "/Menu/User/Index/"):
                with self._plant_id_lock:
                    self._plant_id = resp.url.split("/")[6]
                    self._login = True
                    self._LOGGER.info('%s Plant ID is %s', self, self._plant_id)
            else:
                self._LOGGER.warning('%s Authentication login error', self)
                raise Exception("Login parsing of URL failed")
        return

    def _set_sensors(self, request_type=""):

        if request_type in {self._REQUEST_GET_MAIN, self._REQUEST_SET_MAIN}:

            if self.available and self._ariston_data != {}:

                try:
                    self._ariston_sensors[self._PARAM_CH_DETECTED_TEMPERATURE][self._VALUE] = \
                        self._ariston_data["zone"]["roomTemp"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_CH_DETECTED_TEMPERATURE][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_CH_ANTIFREEZE_TEMPERATURE][self._VALUE] = \
                        self._ariston_data["zone"]["antiFreezeTemp"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_CH_ANTIFREEZE_TEMPERATURE][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_CH_MODE][self._VALUE] = \
                        self._VALUE_TO_CH_MODE[self._ariston_data["zone"]["mode"]["value"]]
                except KeyError:
                    self._ariston_sensors[self._PARAM_CH_MODE][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_CH_SET_TEMPERATURE][self._VALUE] = \
                        self._ariston_data["zone"]["comfortTemp"]["value"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_CH_SET_TEMPERATURE][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_DHW_SET_TEMPERATURE][self._VALUE] = \
                        self._ariston_data["dhwTemp"]["value"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_DHW_SET_TEMPERATURE][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_MODE][self._VALUE] = \
                        self._VALUE_TO_MODE[self._ariston_data["mode"]]
                except KeyError:
                    self._ariston_sensors[self._PARAM_MODE][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_DHW_STORAGE_TEMPERATURE][self._VALUE] = \
                        self._ariston_data["dhwStorageTemp"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_DHW_STORAGE_TEMPERATURE][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_OUTSIDE_TEMPERATURE][self._VALUE] = \
                        self._ariston_data["outsideTemp"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_OUTSIDE_TEMPERATURE][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_DHW_COMFORT_TEMPERATURE][self._VALUE] = \
                        self._ariston_data["dhwTimeProgComfortTemp"]["value"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_DHW_COMFORT_TEMPERATURE][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_DHW_ECONOMY_TEMPERATURE][self._VALUE] = \
                        self._ariston_data["dhwTimeProgEconomyTemp"]["value"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_DHW_ECONOMY_TEMPERATURE][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_DHW_MODE][self._VALUE] = \
                        self._VALUE_TO_DHW_MODE[self._ariston_data["dhwMode"]]
                except KeyError:
                    self._ariston_sensors[self._PARAM_DHW_MODE][self._VALUE] = None

                try:
                    if self._ariston_data["zone"]["comfortTemp"]["value"] == \
                            self._ariston_data["zone"]["antiFreezeTemp"] or self._ariston_data["holidayEnabled"]:
                        self._ariston_sensors[self._PARAM_HOLIDAY_MODE][self._VALUE] = True
                    else:
                        self._ariston_sensors[self._PARAM_HOLIDAY_MODE][self._VALUE] = False
                except KeyError:
                    self._ariston_sensors[self._PARAM_HOLIDAY_MODE][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_FLAME][self._VALUE] = \
                        self._ariston_data["flameSensor"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_FLAME][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_HEAT_PUMP][self._VALUE] = \
                        self._ariston_data["heatingPumpOn"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_HEAT_PUMP][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_CH_PILOT][self._VALUE] = \
                        self._ariston_data["zone"]["pilotOn"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_CH_PILOT][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_CH_FLAME][self._VALUE] = \
                        self._ariston_data["zone"]["heatRequest"]
                    if self._ariston_data["dhwStorageTemp"] != self._INVALID_STORAGE_TEMP \
                            and self._dhw_trend_up \
                            and self._VALUE_TO_MODE[self._ariston_data["mode"]] in {self._VAL_SUMMER, self._VAL_WINTER}\
                            and self._ariston_data["flameSensor"] and not self._ch_and_dhw:
                        self._ariston_sensors[self._PARAM_CH_FLAME][self._VALUE] = False
                except KeyError:
                    self._ariston_sensors[self._PARAM_CH_FLAME][self._VALUE] = None

                try:
                    if not self._ariston_data["zone"]["heatRequest"] and self._ariston_data["flameSensor"]:
                        self._ariston_sensors[self._PARAM_DHW_FLAME][self._VALUE] = True
                    elif self._ariston_data["flameForDhw"]:
                        self._ariston_sensors[self._PARAM_DHW_FLAME][self._VALUE] = True
                    elif self._ariston_data["dhwStorageTemp"] != self._INVALID_STORAGE_TEMP \
                            and self._dhw_trend_up \
                            and self._VALUE_TO_MODE[self._ariston_data["mode"]] in [self._VAL_SUMMER, self._VAL_WINTER]\
                            and self._ariston_data["flameSensor"]:
                        self._ariston_sensors[self._PARAM_DHW_FLAME][self._VALUE] = True
                    elif self._dhw_unknown_as_on and self._ariston_data["flameSensor"]:
                        self._ariston_sensors[self._PARAM_DHW_FLAME][self._VALUE] = True
                    else:
                        self._ariston_sensors[self._PARAM_DHW_FLAME][self._VALUE] = False
                except KeyError:
                    self._ariston_sensors[self._PARAM_DHW_FLAME][self._VALUE] = None

            else:
                self._ariston_sensors[self._PARAM_CH_DETECTED_TEMPERATURE][self._VALUE] = None
                self._ariston_sensors[self._PARAM_CH_ANTIFREEZE_TEMPERATURE][self._VALUE] = None
                self._ariston_sensors[self._PARAM_CH_MODE][self._VALUE] = None
                self._ariston_sensors[self._PARAM_CH_SET_TEMPERATURE][self._VALUE] = None
                self._ariston_sensors[self._PARAM_DHW_SET_TEMPERATURE][self._VALUE] = None
                self._ariston_sensors[self._PARAM_MODE][self._VALUE] = None
                self._ariston_sensors[self._PARAM_DHW_STORAGE_TEMPERATURE][self._VALUE] = None
                self._ariston_sensors[self._PARAM_OUTSIDE_TEMPERATURE][self._VALUE] = None
                self._ariston_sensors[self._PARAM_DHW_COMFORT_TEMPERATURE][self._VALUE] = None
                self._ariston_sensors[self._PARAM_DHW_ECONOMY_TEMPERATURE][self._VALUE] = None
                self._ariston_sensors[self._PARAM_DHW_MODE][self._VALUE] = None
                self._ariston_sensors[self._PARAM_HOLIDAY_MODE][self._VALUE] = None
                self._ariston_sensors[self._PARAM_FLAME][self._VALUE] = None
                self._ariston_sensors[self._PARAM_HEAT_PUMP][self._VALUE] = None
                self._ariston_sensors[self._PARAM_CH_PILOT][self._VALUE] = None
                self._ariston_sensors[self._PARAM_CH_FLAME][self._VALUE] = None
                self._ariston_sensors[self._PARAM_DHW_FLAME][self._VALUE] = None

        if request_type == self._REQUEST_GET_CH:

            if self.available and self._ariston_ch_data != {}:

                try:
                    self._ariston_sensors[self._PARAM_CH_PROGRAM][self._VALUE] = {}
                    for day_of_week in self._DAYS_OF_WEEK:
                        if day_of_week in self._ariston_ch_data:
                            for day_slices in self._ariston_ch_data[day_of_week]["slices"]:
                                attribute_name = day_of_week + '_' + day_slices["from"] + '_' + day_slices["to"]
                                if day_slices["temperatureId"] == 1:
                                    attribute_value = "Comfort"
                                else:
                                    attribute_value = "Economy"
                                self._ariston_sensors[self._PARAM_CH_PROGRAM][self._VALUE][attribute_name] = \
                                    attribute_value
                except KeyError:
                    self._ariston_sensors[self._PARAM_CH_PROGRAM][self._VALUE] = None

            else:
                self._ariston_sensors[self._PARAM_CH_PROGRAM][self._VALUE] = None

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
                    self._ariston_sensors[self._PARAM_ERRORS_COUNT][self._VALUE] = \
                        self._ariston_error_data["count"]
                except KeyError:
                    self._ariston_sensors[self._PARAM_ERRORS_COUNT][self._VALUE] = None

                try:
                    self._ariston_sensors[self._PARAM_ERRORS][self._VALUE] = \
                        self._ariston_error_data["result"]
                except KeyError:
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

            else:
                self._ariston_sensors[self._PARAM_ACCOUNT_CH_GAS][self._VALUE] = None
                self._ariston_sensors[self._PARAM_ACCOUNT_DHW_GAS][self._VALUE] = None
                self._ariston_sensors[self._PARAM_ACCOUNT_CH_ELECTRICITY][self._VALUE] = None
                self._ariston_sensors[self._PARAM_ACCOUNT_DHW_ELECTRICITY][self._VALUE] = None
                self._ariston_sensors[self._PARAM_HEATING_LAST_24H][self._VALUE] = None
                self._ariston_sensors[self._PARAM_WATER_LAST_24H][self._VALUE] = None
                self._ariston_sensors[self._PARAM_HEATING_LAST_7D][self._VALUE] = None
                self._ariston_sensors[self._PARAM_WATER_LAST_7D][self._VALUE] = None
                self._ariston_sensors[self._PARAM_HEATING_LAST_30D][self._VALUE] = None
                self._ariston_sensors[self._PARAM_WATER_LAST_30D][self._VALUE] = None
                self._ariston_sensors[self._PARAM_HEATING_LAST_365D][self._VALUE] = None
                self._ariston_sensors[self._PARAM_WATER_LAST_365D][self._VALUE] = None
                self._ariston_sensors[self._PARAM_HEATING_LAST_24H_LIST][self._VALUE] = None
                self._ariston_sensors[self._PARAM_WATER_LAST_24H_LIST][self._VALUE] = None
                self._ariston_sensors[self._PARAM_HEATING_LAST_7D_LIST][self._VALUE] = None
                self._ariston_sensors[self._PARAM_WATER_LAST_7D_LIST][self._VALUE] = None
                self._ariston_sensors[self._PARAM_HEATING_LAST_30D_LIST][self._VALUE] = None
                self._ariston_sensors[self._PARAM_WATER_LAST_30D_LIST][self._VALUE] = None
                self._ariston_sensors[self._PARAM_HEATING_LAST_365D_LIST][self._VALUE] = None
                self._ariston_sensors[self._PARAM_WATER_LAST_365D_LIST][self._VALUE] = None

        if request_type == self._REQUEST_GET_OTHER:

            if self.available and self._ariston_other_data != {}:

                try:
                    for param_item in self._ariston_other_data:
                        if param_item["id"] == self._ARISTON_CH_COMFORT_TEMP:
                            self._ariston_sensors[self._PARAM_CH_COMFORT_TEMPERATURE][self._VALUE] = \
                                param_item["value"]
                            break
                    else:
                        self._ariston_sensors[self._PARAM_CH_COMFORT_TEMPERATURE][self._VALUE] = None
                except KeyError:
                    self._ariston_sensors[self._PARAM_CH_COMFORT_TEMPERATURE][self._VALUE] = None

                try:
                    for param_item in self._ariston_other_data:
                        if param_item["id"] == self._ARISTON_CH_ECONOMY_TEMP:
                            self._ariston_sensors[self._PARAM_CH_ECONOMY_TEMPERATURE][self._VALUE] = \
                                param_item["value"]
                            break
                    else:
                        self._ariston_sensors[self._PARAM_CH_ECONOMY_TEMPERATURE][self._VALUE] = None
                except KeyError:
                    self._ariston_sensors[self._PARAM_CH_ECONOMY_TEMPERATURE][self._VALUE] = None

                try:
                    for param_item in self._ariston_other_data:
                        if param_item["id"] == self._ARISTON_DHW_COMFORT_FUNCTION:
                            self._ariston_sensors[self._PARAM_DHW_COMFORT_FUNCTION][self._VALUE] = \
                                self._DHW_COMFORT_VALUE_TO_FUNCT[param_item["value"]]
                            break
                    else:
                        self._ariston_sensors[self._PARAM_DHW_COMFORT_FUNCTION][self._VALUE] = None
                except KeyError:
                    self._ariston_sensors[self._PARAM_DHW_COMFORT_FUNCTION][self._VALUE] = None

                try:
                    for param_item in self._ariston_other_data:
                        if param_item["id"] == self._ARISTON_SIGNAL_STRENGHT:
                            self._ariston_sensors[self._PARAM_SIGNAL_STRENGTH][self._VALUE] = \
                                param_item["value"]
                            break
                    else:
                        self._ariston_sensors[self._PARAM_SIGNAL_STRENGTH][self._VALUE] = None
                except KeyError:
                    self._ariston_sensors[self._PARAM_SIGNAL_STRENGTH][self._VALUE] = None

                try:
                    for param_item in self._ariston_other_data:
                        if param_item["id"] == self._ARISTON_THERMAL_CLEANSE_CYCLE:
                            self._ariston_sensors[self._PARAM_THERMAL_CLEANSE_CYCLE][self._VALUE] = \
                                param_item["value"]
                            break
                    else:
                        self._ariston_sensors[self._PARAM_THERMAL_CLEANSE_CYCLE][self._VALUE] = None
                except KeyError:
                    self._ariston_sensors[self._PARAM_THERMAL_CLEANSE_CYCLE][self._VALUE] = None

                try:
                    for param_item in self._ariston_other_data:
                        if param_item["id"] == self._ARISTON_INTERNET_TIME:
                            if param_item["value"] == 1:
                                self._ariston_sensors[self._PARAM_INTERNET_TIME][self._VALUE] = True
                            else:
                                self._ariston_sensors[self._PARAM_INTERNET_TIME][self._VALUE] = False
                            break
                    else:
                        self._ariston_sensors[self._PARAM_INTERNET_TIME][self._VALUE] = None
                except KeyError:
                    self._ariston_sensors[self._PARAM_INTERNET_TIME][self._VALUE] = None

                try:
                    for param_item in self._ariston_other_data:
                        if param_item["id"] == self._ARISTON_INTERNET_WEATHER:
                            if param_item["value"] == 1:
                                self._ariston_sensors[self._PARAM_INTERNET_WEATHER][self._VALUE] = True
                            else:
                                self._ariston_sensors[self._PARAM_INTERNET_WEATHER][self._VALUE] = False
                            break
                    else:
                        self._ariston_sensors[self._PARAM_INTERNET_WEATHER][self._VALUE] = None
                except KeyError:
                    self._ariston_sensors[self._PARAM_INTERNET_WEATHER][self._VALUE] = None

                try:
                    for param_item in self._ariston_other_data:
                        if param_item["id"] == self._ARISTON_CH_AUTO_FUNCTION:
                            if param_item["value"] == 1:
                                self._ariston_sensors[self._PARAM_CH_AUTO_FUNCTION][self._VALUE] = True
                            else:
                                self._ariston_sensors[self._PARAM_CH_AUTO_FUNCTION][self._VALUE] = False
                            break
                    else:
                        self._ariston_sensors[self._PARAM_CH_AUTO_FUNCTION][self._VALUE] = None
                except KeyError:
                    self._ariston_sensors[self._PARAM_CH_AUTO_FUNCTION][self._VALUE] = None

                try:
                    for param_item in self._ariston_other_data:
                        if param_item["id"] == self._ARISTON_THERMAL_CLEANSE_FUNCTION:
                            if param_item["value"] == 1:
                                self._ariston_sensors[self._PARAM_THERMAL_CLEANSE_FUNCTION][self._VALUE] = True
                            else:
                                self._ariston_sensors[self._PARAM_THERMAL_CLEANSE_FUNCTION][self._VALUE] = False
                            break
                    else:
                        self._ariston_sensors[self._PARAM_THERMAL_CLEANSE_FUNCTION][self._VALUE] = None
                except KeyError:
                    self._ariston_sensors[self._PARAM_THERMAL_CLEANSE_FUNCTION][self._VALUE] = None

            else:
                self._ariston_sensors[self._PARAM_CH_COMFORT_TEMPERATURE][self._VALUE] = None
                self._ariston_sensors[self._PARAM_CH_ECONOMY_TEMPERATURE][self._VALUE] = None
                self._ariston_sensors[self._PARAM_DHW_COMFORT_FUNCTION][self._VALUE] = None
                self._ariston_sensors[self._PARAM_SIGNAL_STRENGTH][self._VALUE] = None
                self._ariston_sensors[self._PARAM_THERMAL_CLEANSE_CYCLE][self._VALUE] = None
                self._ariston_sensors[self._PARAM_INTERNET_TIME][self._VALUE] = None
                self._ariston_sensors[self._PARAM_INTERNET_WEATHER][self._VALUE] = None
                self._ariston_sensors[self._PARAM_CH_AUTO_FUNCTION][self._VALUE] = None
                self._ariston_sensors[self._PARAM_THERMAL_CLEANSE_FUNCTION][self._VALUE] = None

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

    def _set_visible_data(self):
        # set visible values as if they have in fact changed
        for parameter, value in self._set_param.items():
            try:
                if parameter in self._SENSOR_SET_LIST:
                    if parameter in self._ariston_sensors \
                            and self._valid_requests[self._get_request_for_parameter(parameter)]:

                        if parameter == self._PARAM_MODE:

                            self._ariston_sensors[parameter][self._VALUE] = self._VALUE_TO_MODE[value]

                        elif parameter == self._PARAM_CH_MODE:

                            self._ariston_sensors[parameter][self._VALUE] = self._VALUE_TO_CH_MODE[value]

                        elif parameter == self._PARAM_CH_SET_TEMPERATURE:

                            self._ariston_sensors[parameter][self._VALUE] = value
                            if self._current_temp_economy_ch:
                                self._ariston_sensors[self._PARAM_CH_ECONOMY_TEMPERATURE][self._VALUE] = value
                            elif self._current_temp_economy_ch is False:
                                self._ariston_sensors[self._PARAM_CH_COMFORT_TEMPERATURE][self._VALUE] = value

                        elif parameter == self._PARAM_CH_COMFORT_TEMPERATURE:

                            self._ariston_sensors[parameter][self._VALUE] = value
                            if self._current_temp_economy_ch is False:
                                self._ariston_sensors[self._PARAM_CH_SET_TEMPERATURE][self._VALUE] = value

                        elif parameter == self._PARAM_CH_ECONOMY_TEMPERATURE:

                            self._ariston_sensors[parameter][self._VALUE] = value
                            if self._current_temp_economy_ch:
                                self._ariston_sensors[self._PARAM_CH_SET_TEMPERATURE][self._VALUE] = value

                        elif parameter == self._PARAM_DHW_SET_TEMPERATURE:

                            self._ariston_sensors[parameter][self._VALUE] = value
                            if self._current_temp_economy_dhw:
                                self._ariston_sensors[self._PARAM_DHW_ECONOMY_TEMPERATURE][self._VALUE] = value
                            else:
                                self._ariston_sensors[self._PARAM_DHW_COMFORT_TEMPERATURE][self._VALUE] = value

                        elif parameter == self._PARAM_DHW_COMFORT_TEMPERATURE:

                            self._ariston_sensors[parameter][self._VALUE] = value
                            if not self._current_temp_economy_dhw:
                                self._ariston_sensors[self._PARAM_DHW_SET_TEMPERATURE][self._VALUE] = value

                        elif parameter == self._PARAM_DHW_ECONOMY_TEMPERATURE:

                            self._ariston_sensors[parameter][self._VALUE] = value
                            if self._current_temp_economy_dhw:
                                self._ariston_sensors[self._PARAM_DHW_SET_TEMPERATURE][self._VALUE] = value

                        elif parameter == self._PARAM_DHW_MODE:

                            self._ariston_sensors[parameter][self._VALUE] = self._VALUE_TO_DHW_MODE[value]

                        elif parameter == self._PARAM_DHW_COMFORT_FUNCTION:

                            self._ariston_sensors[parameter][self._VALUE] = self._DHW_COMFORT_VALUE_TO_FUNCT[value]

                        elif parameter == self._PARAM_INTERNET_TIME:

                            if value == 1:
                                self._ariston_sensors[parameter][self._VALUE] = True
                            else:
                                self._ariston_sensors[parameter][self._VALUE] = False

                        elif parameter == self._PARAM_INTERNET_WEATHER:

                            if value == 1:
                                self._ariston_sensors[parameter][self._VALUE] = True
                            else:
                                self._ariston_sensors[parameter][self._VALUE] = False

                        elif parameter == self._PARAM_CH_AUTO_FUNCTION:

                            if value == 1:
                                self._ariston_sensors[parameter][self._VALUE] = True
                            else:
                                self._ariston_sensors[parameter][self._VALUE] = False

                        elif parameter == self._PARAM_UNITS:

                            self._ariston_sensors[parameter][self._VALUE] = self._VALUE_TO_UNIT[value]
                            self._update_units()

                        elif parameter == self._PARAM_THERMAL_CLEANSE_CYCLE:

                            self._ariston_sensors[parameter][self._VALUE] = value

                        elif parameter == self._PARAM_THERMAL_CLEANSE_FUNCTION:

                            if value == 1:
                                self._ariston_sensors[parameter][self._VALUE] = True
                            else:
                                self._ariston_sensors[parameter][self._VALUE] = False

            except KeyError:
                continue

        if self._store_file:
            store_file = 'data_ariston_temp_main.json'
            store_file_path = os.path.join(self._store_folder, store_file)
            with open(store_file_path, 'w') as ariston_fetched:
                json.dump(self._ariston_data, ariston_fetched)
            store_file = 'data_ariston_temp_param.json'
            store_file_path = os.path.join(self._store_folder, store_file)
            with open(store_file_path, 'w') as ariston_fetched:
                json.dump(self._ariston_other_data, ariston_fetched)
            store_file = 'data_ariston_temp_units.json'
            store_file_path = os.path.join(self._store_folder, store_file)
            with open(store_file_path, 'w') as ariston_fetched:
                json.dump(self._ariston_units, ariston_fetched)

    def _store_data(self, resp, request_type=""):
        """Store received dictionary"""
        if resp.status_code != 200:
            self._LOGGER.warning('%s %s invalid reply code %s', self, request_type, resp.status_code)
            raise Exception("Unexpected code {} received for the request {}".format(resp.status_code, request_type))
        if not self._json_validator(resp.json()):
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
                allowed_ch_modes = \
                    self._ariston_data["zone"]["mode"]["allowedOptions"]
                last_temp[self._PARAM_DHW_STORAGE_TEMPERATURE] = \
                    self._ariston_data["dhwStorageTemp"]
                last_temp[self._PARAM_DHW_COMFORT_TEMPERATURE] = \
                    self._ariston_data["dhwTimeProgComfortTemp"]["value"]
                last_temp[self._PARAM_DHW_ECONOMY_TEMPERATURE] = \
                    self._ariston_data["dhwTimeProgEconomyTemp"]["value"]
                last_temp[self._PARAM_DHW_SET_TEMPERATURE] = \
                    self._ariston_data["dhwTemp"]["value"]
                last_temp[self._PARAM_CH_DETECTED_TEMPERATURE] = \
                    self._ariston_data["zone"]["roomTemp"]
                last_temp[self._PARAM_CH_SET_TEMPERATURE] = \
                    self._ariston_data["zone"]["comfortTemp"]["value"]
                last_temp_min[self._PARAM_DHW_COMFORT_TEMPERATURE] = \
                    self._ariston_data["dhwTimeProgComfortTemp"]["min"]
                last_temp_min[self._PARAM_DHW_ECONOMY_TEMPERATURE] = \
                    self._ariston_data["dhwTimeProgEconomyTemp"]["min"]
                last_temp_min[self._PARAM_DHW_SET_TEMPERATURE] = \
                    self._ariston_data["dhwTemp"]["min"]
                last_temp_min[self._PARAM_CH_SET_TEMPERATURE] = \
                    self._ariston_data["zone"]["comfortTemp"]["min"]
                last_temp_max[self._PARAM_DHW_COMFORT_TEMPERATURE] = \
                    self._ariston_data["dhwTimeProgComfortTemp"]["max"]
                last_temp_max[self._PARAM_DHW_ECONOMY_TEMPERATURE] = \
                    self._ariston_data["dhwTimeProgEconomyTemp"]["max"]
                last_temp_max[self._PARAM_DHW_SET_TEMPERATURE] = \
                    self._ariston_data["dhwTemp"]["max"]
                last_temp_max[self._PARAM_CH_SET_TEMPERATURE] = \
                    self._ariston_data["zone"]["comfortTemp"]["max"]
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
            except copy.error:
                self._ariston_data = {}
                self._LOGGER.warning("%s Invalid data received for Main, not JSON", self)
                raise Exception("Corruption at reading data of the request {}".format(request_type))
            try:
                # force default modes if received none
                if not self._ariston_data["allowedModes"]:
                    if allowed_modes:
                        self._ariston_data["allowedModes"] = allowed_modes
                    else:
                        self._ariston_data = {}
                        raise Exception("Invalid allowed modes in the request {}".format(request_type))
                # force default CH modes if received none
                if not self._ariston_data["zone"]["mode"]["allowedOptions"]:
                    if allowed_ch_modes:
                        self._ariston_data["zone"]["mode"]["allowedOptions"] = allowed_ch_modes
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
                if self._ariston_data["zone"]["roomTemp"] == self._UNKNOWN_TEMP:
                    if last_temp[self._PARAM_CH_DETECTED_TEMPERATURE] != self._UNKNOWN_TEMP:
                        self._get_zero_temperature[self._PARAM_CH_DETECTED_TEMPERATURE] += 1
                        store_none_zero = True
                        if self._get_zero_temperature[self._PARAM_CH_DETECTED_TEMPERATURE] < self._MAX_ZERO_TOLERANCE:
                            self._ariston_data["zone"]["roomTemp"] = last_temp[
                                self._PARAM_CH_DETECTED_TEMPERATURE]
                else:
                    self._get_zero_temperature[self._PARAM_CH_DETECTED_TEMPERATURE] = 0
                # keep latest CH set temperature if received invalid
                if self._ariston_data["zone"]["comfortTemp"]["value"] == self._UNKNOWN_TEMP:
                    if last_temp[self._PARAM_CH_SET_TEMPERATURE] != self._UNKNOWN_TEMP:
                        self._get_zero_temperature[self._PARAM_CH_SET_TEMPERATURE] += 1
                        store_none_zero = True
                        if self._get_zero_temperature[self._PARAM_CH_SET_TEMPERATURE] < self._MAX_ZERO_TOLERANCE:
                            self._ariston_data["zone"]["comfortTemp"]["value"] = last_temp[
                                self._PARAM_CH_SET_TEMPERATURE]
                else:
                    self._get_zero_temperature[self._PARAM_CH_SET_TEMPERATURE] = 0
            except KeyError:
                self._ariston_data = {}
                self._LOGGER.warning("%s Invalid data received for Main", self)
                store_file = 'main_data_from_web.json'
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, 'w') as ariston_fetched:
                    json.dump(resp.json(), ariston_fetched)
                raise Exception("Corruption at reading data of the request {}".format(request_type))

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

            self._set_sensors(request_type)
            self._set_sensors(self._REQUEST_GET_VERSION)
            self._set_visible_data()

        elif request_type == self._REQUEST_GET_CH:
            """ 
            It happens occasionally that temperatures are not reported.
            If this happens then use last valid value.
            """
            try:
                last_temp[self._PARAM_CH_COMFORT_TEMPERATURE] = self._ariston_ch_data["comfortTemp"]["value"]
                last_temp[self._PARAM_CH_ECONOMY_TEMPERATURE] = self._ariston_ch_data["economyTemp"]["value"]
                last_temp_min[self._PARAM_CH_COMFORT_TEMPERATURE] = self._ariston_ch_data["comfortTemp"]["min"]
                last_temp_min[self._PARAM_CH_ECONOMY_TEMPERATURE] = self._ariston_ch_data["economyTemp"]["min"]
                last_temp_max[self._PARAM_CH_COMFORT_TEMPERATURE] = self._ariston_ch_data["comfortTemp"]["max"]
                last_temp_max[self._PARAM_CH_ECONOMY_TEMPERATURE] = self._ariston_ch_data["economyTemp"]["max"]
            except KeyError:
                last_temp[self._PARAM_CH_COMFORT_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp[self._PARAM_CH_ECONOMY_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp_min[self._PARAM_CH_COMFORT_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp_min[self._PARAM_CH_ECONOMY_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp_max[self._PARAM_CH_COMFORT_TEMPERATURE] = self._UNKNOWN_TEMP
                last_temp_max[self._PARAM_CH_ECONOMY_TEMPERATURE] = self._UNKNOWN_TEMP
            try:
                self._ariston_ch_data = copy.deepcopy(resp.json())
            except copy.error:
                self._ariston_ch_data = {}
                self._LOGGER.warning("%s Invalid data received for CH, not JSON", self)
                raise Exception("Corruption at reading data of the request {}".format(request_type))
            try:
                # keep latest CH comfort temperature if received invalid
                if self._ariston_ch_data["comfortTemp"]["value"] == self._UNKNOWN_TEMP:
                    if last_temp[self._PARAM_CH_COMFORT_TEMPERATURE] != self._UNKNOWN_TEMP:
                        self._get_zero_temperature[self._PARAM_CH_COMFORT_TEMPERATURE] += 1
                        store_none_zero = True
                        if self._get_zero_temperature[self._PARAM_CH_COMFORT_TEMPERATURE] < self._MAX_ZERO_TOLERANCE:
                            self._ariston_ch_data["comfortTemp"]["value"] = last_temp[
                                self._PARAM_CH_COMFORT_TEMPERATURE]
                else:
                    self._get_zero_temperature[self._PARAM_CH_COMFORT_TEMPERATURE] = 0
                # keep latest CH comfort temperature if received invalid
                if self._ariston_ch_data["economyTemp"]["value"] == self._UNKNOWN_TEMP:
                    if last_temp[self._PARAM_CH_ECONOMY_TEMPERATURE] != self._UNKNOWN_TEMP:
                        self._get_zero_temperature[self._PARAM_CH_ECONOMY_TEMPERATURE] += 1
                        store_none_zero = True
                        if self._get_zero_temperature[self._PARAM_CH_ECONOMY_TEMPERATURE] < self._MAX_ZERO_TOLERANCE:
                            self._ariston_ch_data["economyTemp"]["value"] = last_temp[
                                self._PARAM_CH_ECONOMY_TEMPERATURE]
                    else:
                        self._get_zero_temperature[self._PARAM_CH_ECONOMY_TEMPERATURE] = 0
            except KeyError:
                self._LOGGER.warning("%s Invalid data received for CH", self)
                raise Exception("Corruption at reading data of the request {}".format(request_type))

            self._set_sensors(request_type)
            self._set_visible_data()

        elif request_type == self._REQUEST_GET_ERROR:

            try:
                self._ariston_error_data = copy.deepcopy(resp.json())
            except copy.error:
                self._ariston_error_data = {}
                self._LOGGER.warning("%s Invalid data received for error, not JSON", self)
                raise Exception("Corruption at reading data of the request {}".format(request_type))

            self._set_sensors(request_type)
            self._set_visible_data()

        elif request_type == self._REQUEST_GET_GAS:

            try:
                self._ariston_gas_data = copy.deepcopy(resp.json())
            except copy.error:
                self._ariston_gas_data = {}
                self._LOGGER.warning("%s Invalid data received for energy use, not JSON", self)
                raise Exception("Corruption at reading data of the request {}".format(request_type))

            self._set_sensors(request_type)
            self._set_visible_data()

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
                self._LOGGER.warning("%s Invalid data received for parameters, not JSON", self)
                raise Exception("Corruption at reading data of the request {}".format(request_type))

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

            self._set_sensors(request_type)
            self._set_sensors(self._REQUEST_GET_MAIN)
            self._set_visible_data()

        elif request_type == self._REQUEST_GET_UNITS:
            try:
                self._ariston_units = copy.deepcopy(resp.json())
            except copy.error:
                self._ariston_units = {}
                self._LOGGER.warning("%s Invalid data received for units, not JSON", self)
                raise Exception("Corruption at reading data of the request {}".format(request_type))

            self._set_sensors(request_type)
            self._set_visible_data()

        elif request_type == self._REQUEST_GET_CURRENCY:
            try:
                self._ariston_currency = copy.deepcopy(resp.json())
            except copy.error:
                self._ariston_currency = {}
                self._LOGGER.warning("%s Invalid data received for currency, not JSON", self)
                raise Exception("Corruption at reading data of the request {}".format(request_type))

            self._set_sensors(request_type)
            self._set_visible_data()

        elif request_type == self._REQUEST_GET_DHW:
            try:
                self._ariston_dhw_data = copy.deepcopy(resp.json())
            except copy.error:
                self._ariston_dhw_data = {}
                self._LOGGER.warning("%s Invalid data received for DHW, not JSON", self)
                raise Exception("Corruption at reading data of the request {}".format(request_type))

            self._set_sensors(request_type)
            self._set_visible_data()

        elif request_type == self._REQUEST_GET_VERSION:
            try:
                self._version = resp.json()["info"]["version"]
            except KeyError:
                self._version = ""
                self._LOGGER.warning("%s Invalid version fetched", self)

            self._set_sensors(request_type)
            self._set_visible_data()

        self._get_time_end[request_type] = time.time()

        if self._store_file:
            store_file = 'data_ariston' + request_type + '.json'
            store_file_path = os.path.join(self._store_folder, store_file)
            with open(store_file_path, 'w') as ariston_fetched:
                if request_type in {self._REQUEST_GET_MAIN, self._REQUEST_SET_MAIN}:
                    json.dump(self._ariston_data, ariston_fetched)
                elif request_type == self._REQUEST_GET_CH:
                    json.dump(self._ariston_ch_data, ariston_fetched)
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
            store_file = 'data_ariston_timers.json'
            store_file_path = os.path.join(self._store_folder, store_file)
            with open(store_file_path, 'w') as ariston_fetched:
                json.dump([self._set_time_start, self._set_time_end, self._get_time_start, self._get_time_end],
                          ariston_fetched)
            store_file = 'data_ariston_temp_main.json'
            store_file_path = os.path.join(self._store_folder, store_file)
            with open(store_file_path, 'w') as ariston_fetched:
                json.dump(self._ariston_data, ariston_fetched)
            store_file = 'data_ariston_temp_param.json'
            store_file_path = os.path.join(self._store_folder, store_file)
            with open(store_file_path, 'w') as ariston_fetched:
                json.dump(self._ariston_other_data, ariston_fetched)
            store_file = 'data_ariston_temp_units.json'
            store_file_path = os.path.join(self._store_folder, store_file)
            with open(store_file_path, 'w') as ariston_fetched:
                json.dump(self._ariston_units, ariston_fetched)
            store_file = 'data_ariston_dhw_history.json'
            store_file_path = os.path.join(self._store_folder, store_file)
            with open(store_file_path, 'w') as ariston_fetched:
                json.dump(self._dhw_history, ariston_fetched)
            if store_none_zero:
                store_file = 'data_ariston' + request_type + '_last_temp.json'
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, 'w') as ariston_fetched:
                    json.dump([last_temp, last_temp_min, last_temp_max], ariston_fetched)
                store_file = 'data_ariston' + request_type + '_reply_zero.json'
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, 'w') as ariston_fetched:
                    json.dump(resp.json(), ariston_fetched)
                store_file = 'data_ariston_zero_count.json'
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
                    url = self._url + '/TimeProg/GetWeeklyPlan/' + self._plant_id + '?progId=ChZn1&umsys=si'
                    http_timeout = self._timeout_medium
                elif request_type == self._REQUEST_GET_DHW:
                    url = self._url + '/TimeProg/GetWeeklyPlan/' + self._plant_id + '?progId=Dhw&umsys=si'
                    http_timeout = self._timeout_medium
                elif request_type == self._REQUEST_GET_ERROR:
                    url = self._url + '/Error/ActiveDataSource/' + self._plant_id + \
                          '?$inlinecount=allpages&$skip=0&$top=100'
                    http_timeout = self._timeout_medium
                elif request_type == self._REQUEST_GET_GAS:
                    url = self._url + '/Metering/GetData/' + self._plant_id + '?kind=1&umsys=si'
                    http_timeout = self._timeout_medium
                elif request_type == self._REQUEST_GET_OTHER:
                    list_to_send = [
                        self._ARISTON_DHW_COMFORT_TEMP,
                        self._ARISTON_DHW_COMFORT_FUNCTION,
                        self._ARISTON_DHW_TIME_PROG_COMFORT,
                        self._ARISTON_DHW_TIME_PROG_ECONOMY,
                        self._ARISTON_SIGNAL_STRENGHT,
                        self._ARISTON_INTERNET_TIME,
                        self._ARISTON_INTERNET_WEATHER,
                        self._ARISTON_CH_COMFORT_TEMP,
                        self._ARISTON_CH_ECONOMY_TEMP,
                        self._ARISTON_CH_AUTO_FUNCTION
                    ]
                    try:
                        if self._ariston_data["dhwBoilerPresent"]:
                            list_to_send.append(self._ARISTON_THERMAL_CLEANSE_FUNCTION)
                            list_to_send.append(self._ARISTON_THERMAL_CLEANSE_CYCLE)
                    except KeyError:
                        self._LOGGER.warning('%s Problem appending thermal cleanse', self)
                    ids_to_fetch = ",".join(map(str, list_to_send))
                    url = self._url + '/Menu/User/Refresh/' + self._plant_id + '?paramIds=' + ids_to_fetch + '&umsys=si'
                    http_timeout = self._timeout_long
                elif request_type == self._REQUEST_GET_UNITS:
                    url = self._url + '/PlantPreference/GetData/' + self._plant_id
                    http_timeout = self._timeout_short
                elif request_type == self._REQUEST_GET_CURRENCY:
                    url = self._url + '/Metering/GetCurrencySettings/' + self._plant_id
                    http_timeout = self._timeout_medium
                elif request_type == self._REQUEST_GET_VERSION:
                    url = self._GITHUB_LATEST_RELEASE
                    http_timeout = self._timeout_short
                else:
                    url = self._url + '/PlantDashboard/GetPlantData/' + self._plant_id
                    if self.available:
                        http_timeout = self._timeout_long
                    else:
                        # for not available give a bit more time
                        http_timeout = self._timeout_long + 4
                with self._data_lock:
                    try:
                        self._get_time_start[request_type] = time.time()
                        resp = self._session.get(
                            url,
                            auth=self._token,
                            timeout=http_timeout,
                            verify=True)
                    except requests.exceptions.RequestException:
                        self._LOGGER.warning("%s %s Problem reading data", self, request_type)
                        raise Exception("Request {} has failed with an exception".format(request_type))
                    self._store_data(resp, request_type)
            else:
                self._LOGGER.debug("%s %s Still setting data, read restricted", self, request_type)
        else:
            self._LOGGER.warning("%s %s Not properly logged in to get the data", self, request_type)
            raise Exception("Not logged in to fetch the data")
        self._LOGGER.info('Data fetched')
        return True

    def _queue_get_data(self):
        """Queue all request items"""
        with self._data_lock:
            # schedule next get request
            if self._errors >= self._MAX_ERRORS_TIMER_EXTEND:
                # give a little rest to the system if too many errors
                retry_in = self._timer_between_param_delay * self._HTTP_DELAY_MULTIPLY
                self._timer_between_set = self._timer_between_param_delay * self._HTTP_DELAY_MULTIPLY + \
                                          self._HTTP_TIMER_SET_WAIT
                self._LOGGER.warning('%s Retrying in %s seconds', self, retry_in)
            else:
                # work as usual
                retry_in = self._timer_between_param_delay
                self._timer_between_set = self._timer_between_param_delay + self._HTTP_TIMER_SET_WAIT
                self._LOGGER.debug('%s Fetching data in %s seconds', self, retry_in)
            self._timer_periodic_read.cancel()
            if self._started:
                self._timer_periodic_read = threading.Timer(retry_in, self._queue_get_data)
                self._timer_periodic_read.start()

            if not self.available:
                # first always initiate main data
                self._timer_queue_delay.cancel()
                if self._started:
                    self._timer_queue_delay = threading.Timer(1, self._control_availability_state,
                                                              [self._REQUEST_GET_MAIN])
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
                    self._timer_queue_delay.start()
                if not self._set_scheduled:
                    self._set_param_group[self._REQUEST_GET_MAIN] = False
            elif self._set_param_group[self._REQUEST_GET_OTHER]:
                # setting of parameter data is ongoing, prioritize it
                self._timer_queue_delay.cancel()
                if self._started:
                    self._timer_queue_delay = threading.Timer(1, self._control_availability_state,
                                                              [self._REQUEST_GET_OTHER])
                    self._timer_queue_delay.start()
                if not self._set_scheduled:
                    self._set_param_group[self._REQUEST_GET_OTHER] = False
            elif self._set_param_group[self._REQUEST_GET_UNITS]:
                # setting of parameter units is ongoing, prioritize it
                self._timer_queue_delay.cancel()
                if self._started:
                    self._timer_queue_delay = threading.Timer(1, self._control_availability_state,
                                                              [self._REQUEST_GET_UNITS])
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
                                self._timer_queue_delay.start()
                            self._get_request_number_low_prio += 1
                        if self._get_request_number_low_prio >= len(self._request_list_low_prio):
                            self._get_request_number_low_prio = 0

            if self._store_file:
                store_file = 'data_ariston_all_set_get.json'
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, 'w') as ariston_fetched:
                    json.dump(self._set_param_group, ariston_fetched)

    def _control_availability_state(self, request_type=""):
        """Control component availability"""
        try:
            self._get_http_data(request_type)
        except Exception:
            with self._lock:
                was_online = self.available
                self._errors += 1
                self._LOGGER.warning("Connection errors: %i", self._errors)
                offline = not self.available
            if offline and was_online:
                with self._plant_id_lock:
                    self._login = False
                self._LOGGER.error("Ariston is offline: Too many errors")
            raise Exception("Getting HTTP data has failed")
        self._LOGGER.info("Data fetched successfully, available %s", self.available)
        with self._lock:
            was_offline = not self.available
            self._errors = 0
        if was_offline:
            self._LOGGER.info("Ariston back online")
        return

    def _setting_http_data(self, set_data, request_type=""):
        """setting of data"""
        self._LOGGER.info('setting http data')
        try:
            if self._store_file:
                store_file = 'data_ariston' + request_type + '.json'
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, 'w') as ariston_fetched:
                    json.dump(set_data, ariston_fetched)
                store_file = 'data_ariston_all_set.json'
                store_file_path = os.path.join(self._store_folder, store_file)
                with open(store_file_path, 'w') as ariston_fetched:
                    json.dump(self._set_param, ariston_fetched)
                store_file = 'data_ariston_timers.json'
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
            url = self._url + '/PlantDashboard/SetPlantAndZoneData/' + self._plant_id + '?zoneNum=1&umsys=si'
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
            self._LOGGER.warning('%s %s error', self, request_type)
            raise Exception("Unexpected error for setting in the request {}".format(request_type))
        if resp.status_code != 200:
            self._LOGGER.warning("%s %s Command to set data failed with code: %s", self, request_type, resp.status_code)
            raise Exception("Unexpected code {} for setting in the request {}".format(resp.status_code, request_type))
        self._set_time_end[request_type] = time.time()
        if request_type == self._REQUEST_SET_MAIN:
            """
            data in reply cannot be fully trusted as occasionally we receive changed data but on next read turns out 
            that it was in fact not changed, so uncomment below on your own risk
            """
            # self._store_data(resp, request_type)
            if self._store_file:
                store_file = "data_ariston" + request_type + "_reply.txt"
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

                set_data = dict()
                # prepare setting of main data dictionary
                set_data["NewValue"] = copy.deepcopy(self._ariston_data)
                set_data["OldValue"] = copy.deepcopy(self._ariston_data)
                # Format is received in 12H format but for some reason python must send 24H format, not other tools
                try:
                    set_data["NewValue"]["zone"]["derogaUntil"] = self._change_to_24h_format(
                        self._ariston_data["zone"]["derogaUntil"])
                    set_data["OldValue"]["zone"]["derogaUntil"] = self._change_to_24h_format(
                        self._ariston_data["zone"]["derogaUntil"])
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

                if self._PARAM_MODE in self._set_param:
                    if set_data["NewValue"]["mode"] == self._set_param[self._PARAM_MODE]:
                        if self._set_time_start[self._set_request_for_parameter(self._PARAM_MODE)] < \
                                self._get_time_end[self._get_request_for_parameter(self._PARAM_MODE)]:
                            # value should be up to date and match to remove from setting
                            del self._set_param[self._PARAM_MODE]
                        else:
                            # assume data was not yet changed
                            changed_parameter[self._set_request_for_parameter(self._PARAM_MODE)][
                                self._get_request_for_parameter(self._PARAM_MODE)] = True
                    else:
                        set_data["NewValue"]["mode"] = self._set_param[self._PARAM_MODE]
                        changed_parameter[self._set_request_for_parameter(self._PARAM_MODE)][
                            self._get_request_for_parameter(self._PARAM_MODE)] = True

                if self._PARAM_DHW_SET_TEMPERATURE in self._set_param:

                    if math.isclose(
                            set_data["NewValue"]["dhwTemp"]["value"],
                            self._set_param[self._PARAM_DHW_SET_TEMPERATURE],
                            abs_tol=0.01):
                        if self._set_time_start[self._set_request_for_parameter(self._PARAM_DHW_SET_TEMPERATURE)] < \
                                self._get_time_end[self._get_request_for_parameter(self._PARAM_DHW_SET_TEMPERATURE)] \
                                and self._get_zero_temperature[self._PARAM_DHW_SET_TEMPERATURE] == 0:
                            # value should be up to date and match to remove from setting
                            del self._set_param[self._PARAM_DHW_SET_TEMPERATURE]
                        else:
                            # assume data was not yet changed
                            changed_parameter[self._set_request_for_parameter(self._PARAM_DHW_SET_TEMPERATURE)][
                                self._get_request_for_parameter(self._PARAM_DHW_SET_TEMPERATURE)] = True
                    else:
                        set_data["NewValue"]["dhwTemp"]["value"] = self._set_param[self._PARAM_DHW_SET_TEMPERATURE]
                        changed_parameter[self._set_request_for_parameter(self._PARAM_DHW_SET_TEMPERATURE)][
                            self._get_request_for_parameter(self._PARAM_DHW_SET_TEMPERATURE)] = True

                if self._PARAM_DHW_COMFORT_TEMPERATURE in self._set_param:
                    if math.isclose(
                            dhw_temp[self._PARAM_DHW_COMFORT_TEMPERATURE],
                            self._set_param[self._PARAM_DHW_COMFORT_TEMPERATURE],
                            abs_tol=0.01):
                        if self._set_time_start[self._set_request_for_parameter(self._PARAM_DHW_COMFORT_TEMPERATURE)] <\
                                dhw_temp_time[self._PARAM_DHW_COMFORT_TEMPERATURE]:
                            # value should be up to date and match to remove from setting
                            del self._set_param[self._PARAM_DHW_COMFORT_TEMPERATURE]
                        else:
                            # assume data was not yet changed
                            param_data = {
                                "id": self._ARISTON_DHW_TIME_PROG_COMFORT,
                                "newValue": self._set_param[self._PARAM_DHW_COMFORT_TEMPERATURE],
                                "oldValue": set_data["NewValue"]["dhwTimeProgComfortTemp"]["value"]}
                            set_param_data.append(param_data)
                            changed_parameter[self._set_request_for_parameter(self._PARAM_DHW_COMFORT_TEMPERATURE)][
                                self._get_request_for_parameter(self._PARAM_DHW_COMFORT_TEMPERATURE)] = True
                    else:
                        param_data = {
                            "id": self._ARISTON_DHW_TIME_PROG_COMFORT,
                            "newValue": self._set_param[self._PARAM_DHW_COMFORT_TEMPERATURE],
                            "oldValue": set_data["NewValue"]["dhwTimeProgComfortTemp"]["value"]}
                        set_param_data.append(param_data)
                        changed_parameter[self._set_request_for_parameter(self._PARAM_DHW_COMFORT_TEMPERATURE)][
                            self._get_request_for_parameter(self._PARAM_DHW_COMFORT_TEMPERATURE)] = True

                if self._PARAM_DHW_ECONOMY_TEMPERATURE in self._set_param:
                    if math.isclose(
                            dhw_temp[self._PARAM_DHW_ECONOMY_TEMPERATURE],
                            self._set_param[self._PARAM_DHW_ECONOMY_TEMPERATURE],
                            abs_tol=0.01):
                        if self._set_time_start[self._set_request_for_parameter(self._PARAM_DHW_ECONOMY_TEMPERATURE)] <\
                                dhw_temp_time[self._PARAM_DHW_ECONOMY_TEMPERATURE]:
                            # value should be up to date and match to remove from setting
                            del self._set_param[self._PARAM_DHW_ECONOMY_TEMPERATURE]
                        else:
                            # assume data was not yet changed
                            param_data = {
                                "id": self._ARISTON_DHW_TIME_PROG_ECONOMY,
                                "newValue": self._set_param[self._PARAM_DHW_ECONOMY_TEMPERATURE],
                                "oldValue": set_data["NewValue"]["dhwTimeProgEconomyTemp"]["value"]}
                            set_param_data.append(param_data)
                            changed_parameter[self._set_request_for_parameter(self._PARAM_DHW_ECONOMY_TEMPERATURE)][
                                self._get_request_for_parameter(self._PARAM_DHW_ECONOMY_TEMPERATURE)] = True
                    else:
                        param_data = {
                            "id": self._ARISTON_DHW_TIME_PROG_ECONOMY,
                            "newValue": self._set_param[self._PARAM_DHW_ECONOMY_TEMPERATURE],
                            "oldValue": set_data["NewValue"]["dhwTimeProgEconomyTemp"]["value"]}
                        set_param_data.append(param_data)
                        changed_parameter[self._set_request_for_parameter(self._PARAM_DHW_ECONOMY_TEMPERATURE)][
                            self._get_request_for_parameter(self._PARAM_DHW_ECONOMY_TEMPERATURE)] = True

                if self._PARAM_DHW_COMFORT_FUNCTION in self._set_param:
                    try:
                        for param_item in self._ariston_other_data:
                            if param_item["id"] == self._ARISTON_DHW_COMFORT_FUNCTION:
                                if param_item["value"] == self._set_param[self._PARAM_DHW_COMFORT_FUNCTION]:
                                    if self._set_time_start[self._set_request_for_parameter(
                                            self._PARAM_DHW_COMFORT_FUNCTION)] < \
                                            self._get_time_end[self._get_request_for_parameter(
                                                self._PARAM_DHW_COMFORT_FUNCTION)]:
                                        # value should be up to date and match to remove from setting
                                        del self._set_param[self._PARAM_DHW_COMFORT_FUNCTION]
                                    else:
                                        # assume data was not yet changed
                                        param_data = {
                                            "id": self._ARISTON_DHW_COMFORT_FUNCTION,
                                            "newValue": self._set_param[self._PARAM_DHW_COMFORT_FUNCTION],
                                            "oldValue": param_item["value"]}
                                        set_param_data.append(param_data)
                                        changed_parameter[self._set_request_for_parameter(
                                            self._PARAM_DHW_COMFORT_FUNCTION)][self._get_request_for_parameter(
                                                self._PARAM_DHW_COMFORT_FUNCTION)] = True
                                    break
                                else:
                                    param_data = {
                                        "id": self._ARISTON_DHW_COMFORT_FUNCTION,
                                        "newValue": self._set_param[self._PARAM_DHW_COMFORT_FUNCTION],
                                        "oldValue": param_item["value"]}
                                    set_param_data.append(param_data)
                                    changed_parameter[self._set_request_for_parameter(
                                        self._PARAM_DHW_COMFORT_FUNCTION)][
                                        self._get_request_for_parameter(self._PARAM_DHW_COMFORT_FUNCTION)] = True
                                    break
                    except KeyError:
                        changed_parameter[self._set_request_for_parameter(self._PARAM_DHW_COMFORT_FUNCTION)][
                            self._get_request_for_parameter(self._PARAM_DHW_COMFORT_FUNCTION)] = True

                if self._PARAM_INTERNET_TIME in self._set_param:
                    try:
                        for param_item in self._ariston_other_data:
                            if param_item["id"] == self._ARISTON_INTERNET_TIME:
                                if param_item["value"] == self._set_param[self._PARAM_INTERNET_TIME]:
                                    if self._set_time_start[self._set_request_for_parameter(
                                            self._PARAM_INTERNET_TIME)] < \
                                            self._get_time_end[self._get_request_for_parameter(
                                                self._PARAM_INTERNET_TIME)]:
                                        # value should be up to date and match to remove from setting
                                        del self._set_param[self._PARAM_INTERNET_TIME]
                                    else:
                                        # assume data was not yet changed
                                        param_data = {
                                            "id": self._ARISTON_INTERNET_TIME,
                                            "newValue": self._set_param[self._PARAM_INTERNET_TIME],
                                            "oldValue": param_item["value"]}
                                        set_param_data.append(param_data)
                                        changed_parameter[self._set_request_for_parameter(self._PARAM_INTERNET_TIME)][
                                            self._get_request_for_parameter(self._PARAM_INTERNET_TIME)] = True
                                    break
                                else:
                                    param_data = {
                                        "id": self._ARISTON_INTERNET_TIME,
                                        "newValue": self._set_param[self._PARAM_INTERNET_TIME],
                                        "oldValue": param_item["value"]}
                                    set_param_data.append(param_data)
                                    changed_parameter[self._set_request_for_parameter(self._PARAM_INTERNET_TIME)][
                                        self._get_request_for_parameter(self._PARAM_INTERNET_TIME)] = True
                                    break
                    except KeyError:
                        changed_parameter[self._set_request_for_parameter(self._PARAM_INTERNET_TIME)][
                            self._get_request_for_parameter(self._PARAM_INTERNET_TIME)] = True

                if self._PARAM_INTERNET_WEATHER in self._set_param:
                    try:
                        for param_item in self._ariston_other_data:
                            if param_item["id"] == self._ARISTON_INTERNET_WEATHER:
                                if param_item["value"] == self._set_param[self._PARAM_INTERNET_WEATHER]:
                                    if self._set_time_start[self._set_request_for_parameter(
                                            self._PARAM_INTERNET_WEATHER)] < \
                                            self._get_time_end[self._get_request_for_parameter(
                                                self._PARAM_INTERNET_WEATHER)]:
                                        # value should be up to date and match to remove from setting
                                        del self._set_param[self._PARAM_INTERNET_WEATHER]
                                    else:
                                        # assume data was not yet changed
                                        param_data = {
                                            "id": self._ARISTON_INTERNET_WEATHER,
                                            "newValue": self._set_param[self._PARAM_INTERNET_WEATHER],
                                            "oldValue": param_item["value"]}
                                        set_param_data.append(param_data)
                                        changed_parameter[self._set_request_for_parameter(
                                            self._PARAM_INTERNET_WEATHER)][
                                            self._get_request_for_parameter(self._PARAM_INTERNET_WEATHER)] = True
                                    break
                                else:
                                    param_data = {
                                        "id": self._ARISTON_INTERNET_WEATHER,
                                        "newValue": self._set_param[self._PARAM_INTERNET_WEATHER],
                                        "oldValue": param_item["value"]}
                                    set_param_data.append(param_data)
                                    changed_parameter[self._set_request_for_parameter(self._PARAM_INTERNET_WEATHER)][
                                        self._get_request_for_parameter(self._PARAM_INTERNET_WEATHER)] = True
                                    break
                    except KeyError:
                        changed_parameter[self._set_request_for_parameter(self._PARAM_INTERNET_WEATHER)][
                            self._get_request_for_parameter(self._PARAM_INTERNET_WEATHER)] = True

                if self._PARAM_THERMAL_CLEANSE_CYCLE in self._set_param:
                    try:
                        for param_item in self._ariston_other_data:
                            if param_item["id"] == self._ARISTON_THERMAL_CLEANSE_CYCLE:
                                if math.isclose(
                                        param_item["value"],
                                        self._set_param[self._PARAM_THERMAL_CLEANSE_CYCLE],
                                        abs_tol=0.01):
                                    if self._set_time_start[self._set_request_for_parameter(
                                            self._PARAM_THERMAL_CLEANSE_CYCLE)] < \
                                            self._get_time_end[
                                                self._get_request_for_parameter(self._PARAM_THERMAL_CLEANSE_CYCLE)]:
                                        # value should be up to date and match to remove from setting
                                        del self._set_param[self._PARAM_THERMAL_CLEANSE_CYCLE]
                                    else:
                                        # assume data was not yet changed
                                        param_data = {
                                            "id": self._ARISTON_THERMAL_CLEANSE_CYCLE,
                                            "newValue": self._set_param[self._PARAM_THERMAL_CLEANSE_CYCLE],
                                            "oldValue": param_item["value"]}
                                        set_param_data.append(param_data)
                                        changed_parameter[self._set_request_for_parameter(
                                            self._PARAM_THERMAL_CLEANSE_CYCLE)][
                                            self._get_request_for_parameter(self._PARAM_THERMAL_CLEANSE_CYCLE)] = True
                                    break
                                else:
                                    param_data = {
                                        "id": self._ARISTON_THERMAL_CLEANSE_CYCLE,
                                        "newValue": self._set_param[self._PARAM_THERMAL_CLEANSE_CYCLE],
                                        "oldValue": param_item["value"]}
                                    set_param_data.append(param_data)
                                    changed_parameter[self._set_request_for_parameter(
                                        self._PARAM_THERMAL_CLEANSE_CYCLE)][
                                        self._get_request_for_parameter(self._PARAM_THERMAL_CLEANSE_CYCLE)] = True
                                    break
                    except KeyError:
                        changed_parameter[self._set_request_for_parameter(self._PARAM_THERMAL_CLEANSE_CYCLE)][
                            self._get_request_for_parameter(self._PARAM_THERMAL_CLEANSE_CYCLE)] = True

                if self._PARAM_THERMAL_CLEANSE_FUNCTION in self._set_param:
                    try:
                        for param_item in self._ariston_other_data:
                            if param_item["id"] == self._ARISTON_THERMAL_CLEANSE_FUNCTION:
                                if param_item["value"] == self._set_param[self._PARAM_THERMAL_CLEANSE_FUNCTION]:
                                    if self._set_time_start[
                                        self._set_request_for_parameter(self._PARAM_THERMAL_CLEANSE_FUNCTION)] < \
                                            self._get_time_end[
                                                self._get_request_for_parameter(self._PARAM_THERMAL_CLEANSE_FUNCTION)]:
                                        # value should be up to date and match to remove from setting
                                        del self._set_param[self._PARAM_THERMAL_CLEANSE_FUNCTION]
                                    else:
                                        # assume data was not yet changed
                                        param_data = {
                                            "id": self._ARISTON_THERMAL_CLEANSE_FUNCTION,
                                            "newValue": self._set_param[self._PARAM_THERMAL_CLEANSE_FUNCTION],
                                            "oldValue": param_item["value"]}
                                        set_param_data.append(param_data)
                                        changed_parameter[self._set_request_for_parameter(
                                            self._PARAM_THERMAL_CLEANSE_FUNCTION)][
                                            self._get_request_for_parameter(self._PARAM_THERMAL_CLEANSE_FUNCTION)] = \
                                            True
                                    break
                                else:
                                    param_data = {
                                        "id": self._ARISTON_THERMAL_CLEANSE_FUNCTION,
                                        "newValue": self._set_param[self._PARAM_THERMAL_CLEANSE_FUNCTION],
                                        "oldValue": param_item["value"]}
                                    set_param_data.append(param_data)
                                    changed_parameter[self._set_request_for_parameter(
                                        self._PARAM_THERMAL_CLEANSE_FUNCTION)][
                                        self._get_request_for_parameter(self._PARAM_THERMAL_CLEANSE_FUNCTION)] = True
                                    break
                    except KeyError:
                        changed_parameter[self._set_request_for_parameter(self._PARAM_THERMAL_CLEANSE_FUNCTION)][
                            self._get_request_for_parameter(self._PARAM_THERMAL_CLEANSE_FUNCTION)] = True

                if self._PARAM_CH_AUTO_FUNCTION in self._set_param:
                    try:
                        for param_item in self._ariston_other_data:
                            if param_item["id"] == self._ARISTON_CH_AUTO_FUNCTION:
                                if param_item["value"] == self._set_param[self._PARAM_CH_AUTO_FUNCTION]:
                                    if self._set_time_start[self._set_request_for_parameter(
                                            self._PARAM_CH_AUTO_FUNCTION)] < \
                                            self._get_time_end[self._get_request_for_parameter(
                                                self._PARAM_CH_AUTO_FUNCTION)]:
                                        # value should be up to date and match to remove from setting
                                        del self._set_param[self._PARAM_CH_AUTO_FUNCTION]
                                    else:
                                        # assume data was not yet changed
                                        param_data = {
                                            "id": self._ARISTON_CH_AUTO_FUNCTION,
                                            "newValue": self._set_param[self._PARAM_CH_AUTO_FUNCTION],
                                            "oldValue": param_item["value"]}
                                        set_param_data.append(param_data)
                                        changed_parameter[self._set_request_for_parameter(
                                            self._PARAM_CH_AUTO_FUNCTION)][
                                            self._get_request_for_parameter(self._PARAM_CH_AUTO_FUNCTION)] = True
                                    break
                                else:
                                    param_data = {
                                        "id": self._ARISTON_CH_AUTO_FUNCTION,
                                        "newValue": self._set_param[self._PARAM_CH_AUTO_FUNCTION],
                                        "oldValue": param_item["value"]}
                                    set_param_data.append(param_data)
                                    changed_parameter[self._set_request_for_parameter(self._PARAM_CH_AUTO_FUNCTION)][
                                        self._get_request_for_parameter(self._PARAM_CH_AUTO_FUNCTION)] = True
                                    break
                    except KeyError:
                        changed_parameter[self._set_request_for_parameter(self._PARAM_CH_AUTO_FUNCTION)][
                            self._get_request_for_parameter(self._PARAM_CH_AUTO_FUNCTION)] = True

                if self._PARAM_CH_SET_TEMPERATURE in self._set_param:
                    if math.isclose(
                            set_data["NewValue"]["zone"]["comfortTemp"]["value"],
                            self._set_param[self._PARAM_CH_SET_TEMPERATURE],
                            abs_tol=0.01):
                        if self._set_time_start[self._set_request_for_parameter(self._PARAM_CH_SET_TEMPERATURE)] < \
                                self._get_time_end[self._get_request_for_parameter(self._PARAM_CH_SET_TEMPERATURE)] and\
                                self._get_zero_temperature[self._PARAM_CH_SET_TEMPERATURE] == 0:
                            # value should be up to date and match to remove from setting
                            del self._set_param[self._PARAM_CH_SET_TEMPERATURE]
                        else:
                            # assume data was not yet changed
                            changed_parameter[self._set_request_for_parameter(self._PARAM_CH_SET_TEMPERATURE)][
                                self._get_request_for_parameter(self._PARAM_CH_SET_TEMPERATURE)] = True
                    else:
                        set_data["NewValue"]["zone"]["comfortTemp"]["value"] = \
                            self._set_param[self._PARAM_CH_SET_TEMPERATURE]
                        changed_parameter[self._set_request_for_parameter(self._PARAM_CH_SET_TEMPERATURE)][
                            self._get_request_for_parameter(self._PARAM_CH_SET_TEMPERATURE)] = True

                if self._PARAM_CH_COMFORT_TEMPERATURE in self._set_param:
                    try:
                        for param_item in self._ariston_other_data:
                            if param_item["id"] == self._ARISTON_CH_COMFORT_TEMP:
                                if math.isclose(
                                        param_item["value"],
                                        self._set_param[self._PARAM_CH_COMFORT_TEMPERATURE],
                                        abs_tol=0.01):
                                    if self._set_time_start[self._set_request_for_parameter(
                                            self._PARAM_CH_COMFORT_TEMPERATURE)] < \
                                            self._get_time_end[
                                                self._get_request_for_parameter(self._PARAM_CH_COMFORT_TEMPERATURE)]:
                                        # value should be up to date and match to remove from setting
                                        del self._set_param[self._PARAM_CH_COMFORT_TEMPERATURE]
                                    else:
                                        # assume data was not yet changed
                                        param_data = {
                                            "id": self._ARISTON_CH_COMFORT_TEMP,
                                            "newValue": self._set_param[self._PARAM_CH_COMFORT_TEMPERATURE],
                                            "oldValue": param_item["value"]}
                                        set_param_data.append(param_data)
                                        changed_parameter[self._set_request_for_parameter(
                                            self._PARAM_CH_COMFORT_TEMPERATURE)][
                                            self._get_request_for_parameter(self._PARAM_CH_COMFORT_TEMPERATURE)] = True
                                    break
                                else:
                                    param_data = {
                                        "id": self._ARISTON_CH_COMFORT_TEMP,
                                        "newValue": self._set_param[self._PARAM_CH_COMFORT_TEMPERATURE],
                                        "oldValue": param_item["value"]}
                                    set_param_data.append(param_data)
                                    changed_parameter[self._set_request_for_parameter(
                                        self._PARAM_CH_COMFORT_TEMPERATURE)][
                                        self._get_request_for_parameter(self._PARAM_CH_COMFORT_TEMPERATURE)] = True
                                    break
                    except KeyError:
                        changed_parameter[self._set_request_for_parameter(self._PARAM_CH_COMFORT_TEMPERATURE)][
                            self._get_request_for_parameter(self._PARAM_CH_COMFORT_TEMPERATURE)] = True

                if self._PARAM_CH_ECONOMY_TEMPERATURE in self._set_param:
                    try:
                        for param_item in self._ariston_other_data:
                            if param_item["id"] == self._ARISTON_CH_ECONOMY_TEMP:
                                if math.isclose(
                                        param_item["value"],
                                        self._set_param[self._PARAM_CH_ECONOMY_TEMPERATURE],
                                        abs_tol=0.01):
                                    if self._set_time_start[self._set_request_for_parameter(
                                            self._PARAM_CH_ECONOMY_TEMPERATURE)] < \
                                            self._get_time_end[
                                                self._get_request_for_parameter(self._PARAM_CH_ECONOMY_TEMPERATURE)]:
                                        # value should be up to date and match to remove from setting
                                        del self._set_param[self._PARAM_CH_ECONOMY_TEMPERATURE]
                                    else:
                                        # assume data was not yet changed
                                        param_data = {
                                            "id": self._ARISTON_CH_ECONOMY_TEMP,
                                            "newValue": self._set_param[self._PARAM_CH_ECONOMY_TEMPERATURE],
                                            "oldValue": param_item["value"]}
                                        set_param_data.append(param_data)
                                        changed_parameter[self._set_request_for_parameter(
                                            self._PARAM_CH_ECONOMY_TEMPERATURE)][
                                            self._get_request_for_parameter(self._PARAM_CH_ECONOMY_TEMPERATURE)] = True
                                    break
                                else:
                                    param_data = {
                                        "id": self._ARISTON_CH_ECONOMY_TEMP,
                                        "newValue": self._set_param[self._PARAM_CH_ECONOMY_TEMPERATURE],
                                        "oldValue": param_item["value"]}
                                    set_param_data.append(param_data)
                                    changed_parameter[self._set_request_for_parameter(
                                        self._PARAM_CH_ECONOMY_TEMPERATURE)][
                                        self._get_request_for_parameter(self._PARAM_CH_ECONOMY_TEMPERATURE)] = True
                                    break
                    except KeyError:
                        changed_parameter[self._set_request_for_parameter(self._PARAM_CH_ECONOMY_TEMPERATURE)][
                            self._get_request_for_parameter(self._PARAM_CH_ECONOMY_TEMPERATURE)] = True

                if self._PARAM_CH_MODE in self._set_param:
                    if set_data["NewValue"]["zone"]["mode"]["value"] == self._set_param[self._PARAM_CH_MODE]:
                        if self._set_time_start[self._set_request_for_parameter(self._PARAM_CH_MODE)] < \
                                self._get_time_end[self._get_request_for_parameter(self._PARAM_CH_MODE)]:
                            # value should be up to date and match to remove from setting
                            del self._set_param[self._PARAM_CH_MODE]
                        else:
                            # assume data was not yet changed
                            changed_parameter[self._set_request_for_parameter(self._PARAM_CH_MODE)][
                                self._get_request_for_parameter(self._PARAM_CH_MODE)] = True
                    else:
                        set_data["NewValue"]["zone"]["mode"]["value"] = self._set_param[self._PARAM_CH_MODE]
                        changed_parameter[self._set_request_for_parameter(self._PARAM_CH_MODE)][
                            self._get_request_for_parameter(self._PARAM_CH_MODE)] = True

                if self._PARAM_DHW_MODE in self._set_param:
                    if set_data["NewValue"]["dhwMode"] == self._set_param[self._PARAM_DHW_MODE]:
                        if self._set_time_start[self._set_request_for_parameter(self._PARAM_DHW_MODE)] < \
                                self._get_time_end[self._get_request_for_parameter(self._PARAM_DHW_MODE)]:
                            # value should be up to date and match to remove from setting
                            del self._set_param[self._PARAM_DHW_MODE]
                        else:
                            # assume data was not yet changed
                            changed_parameter[self._set_request_for_parameter(self._PARAM_DHW_MODE)][
                                self._get_request_for_parameter(self._PARAM_DHW_MODE)] = True
                    else:
                        set_data["NewValue"]["dhwMode"] = self._set_param[self._PARAM_DHW_MODE]
                        changed_parameter[self._set_request_for_parameter(self._PARAM_DHW_MODE)][
                            self._get_request_for_parameter(self._PARAM_DHW_MODE)] = True

                if self._PARAM_UNITS in self._set_param:
                    if set_units_data["measurementSystem"] == self._set_param[self._PARAM_UNITS]:
                        if self._set_time_start[self._set_request_for_parameter(self._PARAM_UNITS)] < \
                                self._get_time_end[self._get_request_for_parameter(self._PARAM_UNITS)]:
                            # value should be up to date and match to remove from setting
                            del self._set_param[self._PARAM_UNITS]
                        else:
                            # assume data was not yet changed
                            changed_parameter[self._set_request_for_parameter(self._PARAM_UNITS)][
                                self._get_request_for_parameter(self._PARAM_UNITS)] = True
                    else:
                        set_units_data["measurementSystem"] = self._set_param[self._PARAM_UNITS]
                        changed_parameter[self._set_request_for_parameter(self._PARAM_UNITS)][
                            self._get_request_for_parameter(self._PARAM_UNITS)] = True

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
                self._set_visible_data()

                if changed_parameter[self._REQUEST_SET_MAIN] != {}:
                    try:
                        self._setting_http_data(set_data, self._REQUEST_SET_MAIN)
                    except TypeError:
                        self._LOGGER.warning('%s Setting main data failed', self)
                    except requests.exceptions.RequestException:
                        self._LOGGER.warning('%s Setting main data failed', self)

                elif changed_parameter[self._REQUEST_SET_OTHER] != {}:

                    try:
                        if set_param_data:
                            self._setting_http_data(set_param_data, self._REQUEST_SET_OTHER)
                        else:
                            self._LOGGER.warning('%s No valid data to set parameters', self)
                    except TypeError:
                        self._LOGGER.warning('%s Setting parameter data failed', self)
                    except requests.exceptions.RequestException:
                        self._LOGGER.warning('%s Setting parameter data failed', self)

                elif changed_parameter[self._REQUEST_SET_UNITS]:
                    try:
                        self._setting_http_data(set_units_data, self._REQUEST_SET_UNITS)
                    except TypeError:
                        self._LOGGER.warning('%s Setting units data failed', self)
                    except requests.exceptions.RequestException:
                        self._LOGGER.warning('%s Setting units data failed', self)

                else:
                    self._LOGGER.debug('%s Same data was used', self)

                for key, value in changed_parameter.items():
                    if value != {}:
                        for request_item in value:
                            self._set_param_group[request_item] = True

                if not self._set_scheduled:
                    # no more retries or no changes, no need to keep any changed data
                    self._set_param = {}

                if self._store_file:
                    store_file = 'data_ariston_all_set_get.json'
                    store_file_path = os.path.join(self._store_folder, store_file)
                    with open(store_file_path, 'w') as ariston_fetched:
                        json.dump(self._set_param_group, ariston_fetched)
                    store_file = 'data_ariston_all_set.json'
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
                return self._current_temp_economy_ch
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

    def _check_if_ch_economy(self):
        try:
            ch_params = [
                self._PARAM_CH_SET_TEMPERATURE,
                self._PARAM_CH_COMFORT_TEMPERATURE,
                self._PARAM_CH_ECONOMY_TEMPERATURE
            ]
            if any([i in self._set_param for i in ch_params]) and self._current_temp_economy_ch is not None:
                # data is still changing, assume it is the least value
                return self._current_temp_economy_ch
            if self._ariston_other_data != {} and self._ariston_data != {}:
                if self._VALUE_TO_CH_MODE[self._ariston_data["zone"]["mode"]["value"]] == self._VAL_PROGRAM:
                    for param_item in self._ariston_other_data:
                        if param_item["id"] == self._ARISTON_CH_ECONOMY_TEMP:
                            if math.isclose(
                                    self._ariston_data["zone"]["comfortTemp"]["value"],
                                    param_item["value"],
                                    abs_tol=0.01):
                                self._current_temp_economy_ch = True
                                break
                        else:
                            self._current_temp_economy_ch = False
                else:
                    self._current_temp_economy_ch = None
            else:
                self._current_temp_economy_ch = None
        except KeyError:
            self._current_temp_economy_ch = None
        return self._current_temp_economy_ch

    def set_http_data(self, **parameter_list: Union[str, int, float, bool]) -> None:
        """
        Set data over http, where **parameter_list excepts parameters and wanted values.

        Supported parameters:
            - 'mode'
            - 'ch_mode'
            - 'ch_set_temperature'
            - 'ch_comfort_temperature'
            - 'ch_economy_temperature'
            - 'ch_auto_function'
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
                        if parameter in {
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
                        elif parameter in {
                            self._PARAM_CH_SET_TEMPERATURE,
                            self._PARAM_CH_COMFORT_TEMPERATURE,
                            self._PARAM_CH_ECONOMY_TEMPERATURE,
                            self._PARAM_DHW_SET_TEMPERATURE,
                            self._PARAM_DHW_COMFORT_TEMPERATURE,
                            self._PARAM_DHW_ECONOMY_TEMPERATURE,
                            self._PARAM_THERMAL_CLEANSE_CYCLE
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

                # check mode and set it
                if self._PARAM_MODE in good_values:
                    try:
                        self._set_param[self._PARAM_MODE] = self._MODE_TO_VALUE[good_values[self._PARAM_MODE]]
                        self._LOGGER.info('%s New mode %s', self, good_values[self._PARAM_MODE])
                    except KeyError:
                        self._LOGGER.warning('%s Unknown or unsupported mode or key error: %s', self,
                                        good_values[self._PARAM_MODE])
                        bad_values[self._PARAM_MODE] = good_values[self._PARAM_MODE]

                # check CH temperature
                if self._PARAM_CH_SET_TEMPERATURE in good_values:
                    try:
                        # round to nearest 0.5
                        temperature = round(float(good_values[self._PARAM_CH_SET_TEMPERATURE]) * 2.0) / 2.0
                        self._check_if_ch_economy()
                        if self._current_temp_economy_ch:
                            self._set_param[self._PARAM_CH_ECONOMY_TEMPERATURE] = temperature
                        elif self._current_temp_economy_ch is False:
                            self._set_param[self._PARAM_CH_COMFORT_TEMPERATURE] = temperature
                        else:
                            # None value
                            self._set_param[self._PARAM_CH_SET_TEMPERATURE] = temperature
                        self._LOGGER.info('%s New CH temperature %s', self, temperature)
                    except KeyError:
                        self._LOGGER.warning('%s Not supported CH temperature value: %s', self,
                                        good_values[self._PARAM_CH_SET_TEMPERATURE])
                        bad_values[self._PARAM_CH_SET_TEMPERATURE] = good_values[self._PARAM_CH_SET_TEMPERATURE]

                # check dhw temperature
                if self._PARAM_DHW_SET_TEMPERATURE in good_values:
                    try:
                        # round to nearest 1
                        temperature = round(float(good_values[self._PARAM_DHW_SET_TEMPERATURE]))
                        self._check_if_dhw_economy()
                        if self._current_temp_economy_dhw:
                            self._set_param[self._PARAM_DHW_ECONOMY_TEMPERATURE] = temperature
                        else:
                            self._set_param[self._PARAM_DHW_COMFORT_TEMPERATURE] = temperature
                        self._LOGGER.info('%s New DHW temperature %s', self, temperature)
                    except KeyError:
                        self._LOGGER.warning('%s Not supported DHW temperature value: %s', self,
                                        good_values[self._PARAM_DHW_SET_TEMPERATURE])
                        bad_values[self._PARAM_DHW_SET_TEMPERATURE] = good_values[self._PARAM_DHW_SET_TEMPERATURE]

                # check dhw comfort temperature
                if self._PARAM_DHW_COMFORT_TEMPERATURE in good_values:
                    try:
                        # round to nearest 1
                        temperature = round(float(good_values[self._PARAM_DHW_COMFORT_TEMPERATURE]))
                        self._set_param[self._PARAM_DHW_COMFORT_TEMPERATURE] = temperature
                        self._LOGGER.info('%s New DHW scheduled comfort temperature %s', self,
                                     good_values[self._PARAM_DHW_COMFORT_TEMPERATURE])
                        self._check_if_dhw_economy()
                    except KeyError:
                        self._LOGGER.warning('%s Not supported DHW scheduled comfort temperature value: %s', self,
                                        good_values[self._PARAM_DHW_COMFORT_TEMPERATURE])
                        bad_values[self._PARAM_DHW_COMFORT_TEMPERATURE] = \
                            good_values[self._PARAM_DHW_COMFORT_TEMPERATURE]

                # check dhw economy temperature
                if self._PARAM_DHW_ECONOMY_TEMPERATURE in good_values:
                    try:
                        # round to nearest 1
                        temperature = round(float(good_values[self._PARAM_DHW_ECONOMY_TEMPERATURE]))
                        self._set_param[self._PARAM_DHW_ECONOMY_TEMPERATURE] = temperature
                        self._LOGGER.info('%s New DHW scheduled economy temperature %s', self, temperature)
                        self._check_if_dhw_economy()
                    except KeyError:
                        self._LOGGER.warning('%s Not supported DHW scheduled economy temperature value: %s', self,
                                        good_values[self._PARAM_DHW_ECONOMY_TEMPERATURE])
                        bad_values[self._PARAM_DHW_ECONOMY_TEMPERATURE] = \
                            good_values[self._PARAM_DHW_ECONOMY_TEMPERATURE]

                # check CH comfort scheduled temperature
                if self._PARAM_CH_COMFORT_TEMPERATURE in good_values:
                    try:
                        # round to nearest 0.5
                        temperature = round(float(good_values[self._PARAM_CH_COMFORT_TEMPERATURE]) * 2.0) / 2.0
                        self._set_param[self._PARAM_CH_COMFORT_TEMPERATURE] = temperature
                        self._LOGGER.info('%s New CH temperature %s', self, temperature)
                        self._check_if_ch_economy()
                    except KeyError:
                        self._LOGGER.warning('%s Not supported CH comfort scheduled temperature value: %s', self,
                                        good_values[self._PARAM_CH_COMFORT_TEMPERATURE])
                        bad_values[self._PARAM_CH_COMFORT_TEMPERATURE] = \
                            good_values[self._PARAM_CH_COMFORT_TEMPERATURE]

                # check CH economy scheduled temperature
                if self._PARAM_CH_ECONOMY_TEMPERATURE in good_values:
                    try:
                        # round to nearest 0.5
                        temperature = round(float(good_values[self._PARAM_CH_ECONOMY_TEMPERATURE]) * 2.0) / 2.0
                        self._set_param[self._PARAM_CH_ECONOMY_TEMPERATURE] = temperature
                        self._LOGGER.info('%s New CH temperature %s', self, temperature)
                        self._check_if_ch_economy()
                    except KeyError:
                        self._LOGGER.warning('%s Not supported CH economy scheduled temperature value: %s', self,
                                        good_values[self._PARAM_CH_ECONOMY_TEMPERATURE])
                        bad_values[self._PARAM_CH_ECONOMY_TEMPERATURE] = \
                            good_values[self._PARAM_CH_ECONOMY_TEMPERATURE]

                # check CH mode
                if self._PARAM_CH_MODE in good_values:
                    try:
                        self._set_param[self._PARAM_CH_MODE] = self._CH_MODE_TO_VALUE[good_values[self._PARAM_CH_MODE]]
                        self._LOGGER.info('%s New CH mode %s', self, good_values[self._PARAM_CH_MODE])
                    except KeyError:
                        self._LOGGER.warning('%s Unknown or unsupported CH mode or key error: %s', self,
                                        good_values[self._PARAM_CH_MODE])
                        bad_values[self._PARAM_CH_MODE] = good_values[self._PARAM_CH_MODE]

                # check DHW mode
                if self._PARAM_DHW_MODE in good_values:
                    try:
                        self._set_param[self._PARAM_DHW_MODE] = self._DHW_MODE_TO_VALUE[self._PARAM_DHW_MODE]
                        self._LOGGER.info('%s New DHW mode %s', self, good_values[self._PARAM_DHW_MODE])
                    except KeyError:
                        self._LOGGER.warning('%s Unknown or unsupported DHW mode or key error: %s', self,
                                        good_values[self._PARAM_DHW_MODE])
                        bad_values[self._PARAM_DHW_MODE] = good_values[self._PARAM_DHW_MODE]

                # check DHW Comfort mode
                if self._PARAM_DHW_COMFORT_FUNCTION in good_values:
                    try:
                        self._set_param[self._PARAM_DHW_COMFORT_FUNCTION] = \
                            self._DHW_COMFORT_FUNCT_TO_VALUE[good_values[self._PARAM_DHW_COMFORT_FUNCTION]]
                        self._LOGGER.info('%s New DHW Comfort function %s', self,
                                     good_values[self._PARAM_DHW_COMFORT_FUNCTION])
                    except KeyError:
                        self._LOGGER.warning('%s Unknown or unsupported DHW Comfort function or key error: %s', self,
                                        good_values[self._PARAM_DHW_COMFORT_FUNCTION])
                        bad_values[self._PARAM_DHW_COMFORT_FUNCTION] = good_values[self._PARAM_DHW_COMFORT_FUNCTION]

                # check internet time
                if self._PARAM_INTERNET_TIME in good_values:
                    try:
                        self._set_param[self._PARAM_INTERNET_TIME] = \
                            self._PARAM_STRING_TO_VALUE[good_values[self._PARAM_INTERNET_TIME]]
                        self._LOGGER.info('%s New Internet time is %s', self, good_values[self._PARAM_INTERNET_TIME])
                    except KeyError:
                        self._LOGGER.warning('%s Unknown or unsupported Internet time or key error: %s', self,
                                        good_values[self._PARAM_INTERNET_TIME])
                        bad_values[self._PARAM_INTERNET_TIME] = good_values[self._PARAM_INTERNET_TIME]

                # check internet time
                if self._PARAM_INTERNET_WEATHER in good_values:
                    try:
                        self._set_param[self._PARAM_INTERNET_WEATHER] = \
                            self._PARAM_STRING_TO_VALUE[good_values[self._PARAM_INTERNET_WEATHER]]
                        self._LOGGER.info('%s New Internet weather is %s', self, good_values[self._PARAM_INTERNET_WEATHER])
                    except KeyError:
                        self._LOGGER.warning('%s Unknown or unsupported Internet weather or key error: %s', self,
                                        good_values[self._PARAM_INTERNET_WEATHER])
                        bad_values[self._PARAM_INTERNET_WEATHER] = good_values[self._PARAM_INTERNET_WEATHER]

                # check cleanse cycle
                if self._PARAM_THERMAL_CLEANSE_CYCLE in good_values:
                    try:
                        item_present = False
                        for param_item in self._ariston_other_data:
                            if param_item["id"] == self._ARISTON_THERMAL_CLEANSE_CYCLE:
                                self._set_param[self._PARAM_THERMAL_CLEANSE_CYCLE] = \
                                    good_values[self._PARAM_THERMAL_CLEANSE_CYCLE]
                                item_present = True
                                self._LOGGER.info('%s New Thermal Cleanse Cycle is %s', self,
                                             good_values[self._PARAM_THERMAL_CLEANSE_CYCLE])
                                break
                        if not item_present:
                            self._LOGGER.warning('%s Can not set Thermal Cleanse Cycle: %s', self,
                                            good_values[self._PARAM_THERMAL_CLEANSE_CYCLE])
                            bad_values[self._PARAM_THERMAL_CLEANSE_CYCLE] = \
                                good_values[self._PARAM_THERMAL_CLEANSE_CYCLE]
                    except KeyError:
                        self._LOGGER.warning('%s Unknown or unsupported Thermal Cleanse Cycle or key error: %s', self,
                                        good_values[self._PARAM_THERMAL_CLEANSE_CYCLE])
                        bad_values[self._PARAM_THERMAL_CLEANSE_CYCLE] = good_values[self._PARAM_THERMAL_CLEANSE_CYCLE]

                # check cleanse function
                if self._PARAM_THERMAL_CLEANSE_FUNCTION in good_values:
                    try:
                        item_present = False
                        for param_item in self._ariston_other_data:
                            if param_item["id"] == self._ARISTON_THERMAL_CLEANSE_FUNCTION:
                                self._set_param[self._PARAM_THERMAL_CLEANSE_FUNCTION] = \
                                    self._PARAM_STRING_TO_VALUE[good_values[self._PARAM_THERMAL_CLEANSE_FUNCTION]]
                                item_present = True
                                self._LOGGER.info('%s New Thermal Cleanse Function is %s', self,
                                             good_values[self._PARAM_THERMAL_CLEANSE_FUNCTION])
                                break
                        if not item_present:
                            self._LOGGER.warning('%s Can not set Thermal Cleanse Function: %s', self,
                                            good_values[self._PARAM_THERMAL_CLEANSE_FUNCTION])
                            bad_values[self._PARAM_THERMAL_CLEANSE_FUNCTION] = \
                                good_values[self._PARAM_THERMAL_CLEANSE_FUNCTION]
                    except KeyError:
                        self._LOGGER.warning('%s Unknown or unsupported Thermal Cleanse Function or key error: %s', self,
                                        good_values[self._PARAM_THERMAL_CLEANSE_FUNCTION])
                        bad_values[self._PARAM_THERMAL_CLEANSE_FUNCTION] = \
                            good_values[self._PARAM_THERMAL_CLEANSE_FUNCTION]

                # check CH auto function
                if self._PARAM_CH_AUTO_FUNCTION in good_values:
                    try:
                        self._set_param[self._PARAM_CH_AUTO_FUNCTION] = \
                            self._PARAM_STRING_TO_VALUE[good_values[self._PARAM_CH_AUTO_FUNCTION]]
                        self._LOGGER.info('%s New Internet weather is %s', self,
                                     good_values[self._PARAM_CH_AUTO_FUNCTION])
                    except KeyError:
                        self._LOGGER.warning('%s Unknown or unsupported Internet weather or key error: %s', self,
                                        good_values[self._PARAM_CH_AUTO_FUNCTION])
                        bad_values[self._PARAM_CH_AUTO_FUNCTION] = good_values[self._PARAM_CH_AUTO_FUNCTION]

                # check units of measurement
                if self._PARAM_UNITS in good_values:
                    try:
                        self._set_param[self._PARAM_UNITS] = self._UNIT_TO_VALUE[good_values[self._PARAM_UNITS]]
                        self._LOGGER.info('%s New units of measurement is %s', self, good_values[self._PARAM_UNITS])
                    except KeyError:
                        self._LOGGER.warning('%s Unknown or unsupported units of measurement or key error: %s', self,
                                        good_values[self._PARAM_UNITS])
                        bad_values[self._PARAM_UNITS] = good_values[self._PARAM_UNITS]

                # show data as changed
                self._set_visible_data()

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

    def start(self) -> None:
        """Start communication with the server."""
        self._timer_periodic_read = threading.Timer(1, self._queue_get_data)
        self._timer_periodic_read.start()
        self._started = True

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
        self._login = False
