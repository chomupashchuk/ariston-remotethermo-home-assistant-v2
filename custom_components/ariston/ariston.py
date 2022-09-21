"""Suppoort for Ariston."""
import calendar
import copy
import datetime
import logging
import re
import threading
from typing import Union
import requests


class AristonHandler:
    """
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Ariston NET Remotethermo API

    'username' - mandatory username;

    'password' - mandatory password;

    'sensors' - list of wanted sensors to be monitored. Check class method api_data or method supported_sensors_get

    'period_request' - period to send requests (minimum is 30 seconds)

    'polling' - defines multiplication factor for waiting periods to get or set the data;

    'logging_level' - defines level of logging - allowed values [CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET=(default)]
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    """

    _VERSION = "2.0.14"

    _ARISTON_URL = "https://www.ariston-net.remotethermo.com"

    # API configuration
    _MAX_RETRIES = 5
    _GET_SENSORS_PERIOD_SECONDS = 30
    _SET_SENSORS_PERIOD_SECONDS = 30
    _MAX_ERRORS = 5
    _WAIT_PERIOD_MULTIPLYER = 5
    _TIMEOUT_MIN = 5
    _TIMEOUT_AV = 15
    _TIMEOUT_MAX = 25
    _TIME_SPLIT = 0.1

    # Log levels
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

    # All sensors names
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
    _PARAM_CH_DEROGA_TEMPERATURE = "ch_deroga_temperature"
    _PARAM_CH_PROGRAM = "ch_program"
    _PARAM_CH_WATER_TEMPERATURE = "ch_water_temperature"
    _PARAM_ERRORS_COUNT = "errors_count"
    _PARAM_DHW_COMFORT_FUNCTION = "dhw_comfort_function"
    _PARAM_DHW_MODE = "dhw_mode"
    _PARAM_DHW_PROGRAM = "dhw_program"
    _PARAM_DHW_SET_TEMPERATURE = "dhw_set_temperature"
    _PARAM_DHW_STORAGE_TEMPERATURE = "dhw_storage_temperature"
    _PARAM_DHW_COMFORT_TEMPERATURE = "dhw_comfort_temperature"
    _PARAM_DHW_ECONOMY_TEMPERATURE = "dhw_economy_temperature"
    _PARAM_MODE = "mode"
    _PARAM_OUTSIDE_TEMPERATURE = "outside_temperature"
    _PARAM_SIGNAL_STRENGTH = "signal_strength"
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
    _PARAM_WEATHER = 'weather'
    _PARAM_THERMAL_CLEANSE_FUNCTION = "dhw_thermal_cleanse_function"
    _PARAM_CH_PILOT = "ch_pilot"
    _PARAM_UPDATE = "update"
    _PARAM_ONLINE_VERSION = "online_version"
    _PARAM_PRESSURE = "pressure"
    _PARAM_CH_FLOW_TEMP = 'ch_flow_temperature'
    _PARAM_CH_FIXED_TEMP = 'ch_fixed_temperature'
    _PARAM_CH_LAST_MONTH_GAS = 'ch_gas_last_month'
    _PARAM_CH_LAST_MONTH_ELECTRICITY = 'ch_electricity_last_month'
    _PARAM_DHW_LAST_MONTH_GAS = 'dhw_gas_last_month'
    _PARAM_DHW_LAST_MONTH_ELECTRICITY = 'dhw_electricity_last_month'
    _PARAM_CH_ENERGY_TODAY = 'ch_energy_today'
    _PARAM_CH_ENERGY_YESTERDAY = 'ch_energy_yesterday'
    _PARAM_DHW_ENERGY_TODAY = 'dhw_energy_today'
    _PARAM_DHW_ENERGY_YESTERDAY = 'dhw_energy_yesterday'
    _PARAM_CH_ENERGY_LAST_7_DAYS = 'ch_energy_last_7_days'
    _PARAM_DHW_ENERGY_LAST_7_DAYS = 'dhw_energy_last_7_days'
    _PARAM_CH_ENERGY_THIS_MONTH = 'ch_energy_this_month'
    _PARAM_CH_ENERGY_LAST_MONTH = 'ch_energy_last_month'
    _PARAM_DHW_ENERGY_THIS_MONTH = 'dhw_energy_this_month'
    _PARAM_DHW_ENERGY_LAST_MONTH = 'dhw_energy_last_month'
    _PARAM_CH_ENERGY_THIS_YEAR = 'ch_energy_this_year'
    _PARAM_CH_ENERGY_LAST_YEAR = 'ch_energy_last_year'
    _PARAM_DHW_ENERGY_THIS_YEAR = 'dhw_energy_this_year'
    _PARAM_DHW_ENERGY_LAST_YEAR = 'dhw_energy_last_year'
    _PARAM_CH_ENERGY2_TODAY = 'ch_energy2_today'
    _PARAM_CH_ENERGY2_YESTERDAY = 'ch_energy2_yesterday'
    _PARAM_DHW_ENERGY2_TODAY = 'dhw_energy2_today'
    _PARAM_DHW_ENERGY2_YESTERDAY = 'dhw_energy2_yesterday'
    _PARAM_CH_ENERGY2_LAST_7_DAYS = 'ch_energy2_last_7_days'
    _PARAM_DHW_ENERGY2_LAST_7_DAYS = 'dhw_energy2_last_7_days'
    _PARAM_CH_ENERGY2_THIS_MONTH = 'ch_energy2_this_month'
    _PARAM_CH_ENERGY2_LAST_MONTH = 'ch_energy2_last_month'
    _PARAM_DHW_ENERGY2_THIS_MONTH = 'dhw_energy2_this_month'
    _PARAM_DHW_ENERGY2_LAST_MONTH = 'dhw_energy2_last_month'
    _PARAM_CH_ENERGY2_THIS_YEAR = 'ch_energy2_this_year'
    _PARAM_CH_ENERGY2_LAST_YEAR = 'ch_energy2_last_year'
    _PARAM_DHW_ENERGY2_THIS_YEAR = 'dhw_energy2_this_year'
    _PARAM_DHW_ENERGY2_LAST_YEAR = 'dhw_energy2_last_year'
    _PARAM_CH_ENERGY_DELTA_TODAY = 'ch_energy_delta_today'
    _PARAM_CH_ENERGY_DELTA_YESTERDAY = 'ch_energy_delta_yesterday'
    _PARAM_DHW_ENERGY_DELTA_TODAY = 'dhw_energy_delta_today'
    _PARAM_DHW_ENERGY_DELTA_YESTERDAY = 'dhw_energy_delta_yesterday'
    _PARAM_CH_ENERGY_DELTA_LAST_7_DAYS = 'ch_energy_delta_last_7_days'
    _PARAM_DHW_ENERGY_DELTA_LAST_7_DAYS = 'dhw_energy_delta_last_7_days'
    _PARAM_CH_ENERGY_DELTA_THIS_MONTH = 'ch_energy_delta_this_month'
    _PARAM_CH_ENERGY_DELTA_LAST_MONTH = 'ch_energy_delta_last_month'
    _PARAM_DHW_ENERGY_DELTA_THIS_MONTH = 'dhw_energy_delta_this_month'
    _PARAM_DHW_ENERGY_DELTA_LAST_MONTH = 'dhw_energy_delta_last_month'
    _PARAM_CH_ENERGY_DELTA_THIS_YEAR = 'ch_energy_delta_this_year'
    _PARAM_CH_ENERGY_DELTA_LAST_YEAR = 'ch_energy_delta_last_year'
    _PARAM_DHW_ENERGY_DELTA_THIS_YEAR = 'dhw_energy_delta_this_year'
    _PARAM_DHW_ENERGY_DELTA_LAST_YEAR = 'dhw_energy_delta_last_year'
    _PARAM_HEATING_FLOW_TEMP = "ch_heating_flow_temp"
    _PARAM_HEATING_FLOW_OFFSET = "ch_heating_flow_offset"
    _PARAM_COOLING_FLOW_TEMP = "ch_cooling_flow_temp"
    _PARAM_COOLING_FLOW_OFFSET = "ch_cooling_flow_offset"

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

    # Ariston parameters in Android api
    _ARISTON_PAR_PRESSURE = 'HeatingCircuitPressure'
    _ARISTON_PAR_CH_FLOW_TEMP = 'ChFlowSetpointTemp'
    _ARISTON_PAR_OUTSIDE_TEMP = 'OutsideTemp'
    _ARISTON_PAR_WEATHER = 'Weather'
    _ARISTON_PAR_PLANT_MODE = 'PlantMode'
    _ARISTON_PAR_HOLIDAY = 'Holiday'
    _ARISTON_PAR_FLAME = 'IsFlameOn'
    _ARISTON_PAR_DHW_TEMP = 'DhwTemp'
    _ARISTON_PAR_ZONE_HEAT_REQUEST = 'ZoneHeatRequest'
    _ARIZTON_PAR_ZONE_MODE = 'ZoneMode'
    _ARISTON_PAR_ZONE_DESIRED_TEMP = 'ZoneDesiredTemp'
    _ARISTON_PAR_ZONE_MEAS_TEMP = 'ZoneMeasuredTemp'
    _ARISTON_PAR_ZONE_DEROGA_TEMP = 'ZoneDeroga'
    _ARISTON_PAR_ZONE_CONFORT_TEMP = 'ZoneComfortTemp'
    _ARISTON_PAR_ZONE_PILOT = 'IsZonePilotOn'
    _ARISTON_PAR_ZONE_ECONOMY_TEMP = 'ZoneEconomyTemp'
    _ARISTON_PAR_AUTO_HEATING = "AutomaticThermoregulation"
    _ARISTON_PAR_HEATING_FLOW_TEMP = "HeatingFlowTemp"
    _ARISTON_PAR_HEATING_FLOW_OFFSET = "HeatingFlowOffset"
    _ARISTON_PAR_COOLING_FLOW_TEMP = "CoolingFlowTemp"
    _ARISTON_PAR_COOLING_FLOW_OFFSET = "CoolingFlowOffset"
    _ARISTON_PAR_DHW_MODE = "DhwMode"
    _ARISTON_PAR_DHW_STORAGE_TEMP = "DhwStorageTemperature"
    _ARISTON_PAR_DHW_COMFORT_TEMP = "DhwTimeProgComfortTemp"
    _ARISTON_PAR_DHW_ECONOMY_TEMP = "DhwTimeProgEconomyTemp"
    _ARISTON_PAR_HEAT_PUMP = 'IsHeatingPumpOn'

    # Parameters in Android api within zone 0, mapping to parameter names
    _MAP_ARISTON_ZONE_0_PARAMS = {
        _PARAM_CH_FLOW_TEMP: _ARISTON_PAR_CH_FLOW_TEMP,
        _PARAM_PRESSURE: _ARISTON_PAR_PRESSURE,
        _PARAM_OUTSIDE_TEMPERATURE: _ARISTON_PAR_OUTSIDE_TEMP,
        _PARAM_WEATHER: _ARISTON_PAR_WEATHER,
        _PARAM_MODE: _ARISTON_PAR_PLANT_MODE,
        _PARAM_HOLIDAY_MODE: _ARISTON_PAR_HOLIDAY,
        _PARAM_FLAME: _ARISTON_PAR_FLAME,
        _PARAM_DHW_SET_TEMPERATURE: _ARISTON_PAR_DHW_TEMP,
        _PARAM_DHW_MODE: _ARISTON_PAR_DHW_MODE,
        _PARAM_DHW_COMFORT_TEMPERATURE: _ARISTON_PAR_DHW_COMFORT_TEMP,
        _PARAM_DHW_ECONOMY_TEMPERATURE: _ARISTON_PAR_DHW_ECONOMY_TEMP,
        _PARAM_DHW_STORAGE_TEMPERATURE: _ARISTON_PAR_DHW_STORAGE_TEMP,
        _PARAM_HEAT_PUMP: _ARISTON_PAR_HEAT_PUMP,
    }
    # Parameters in Android api within zone 1, mapping to parameter names
    _MAP_ARISTON_MULTIZONE_PARAMS = {
        _PARAM_CH_FLAME: _ARISTON_PAR_ZONE_HEAT_REQUEST,
        _PARAM_CH_MODE: _ARIZTON_PAR_ZONE_MODE,
        _PARAM_CH_SET_TEMPERATURE: _ARISTON_PAR_ZONE_DESIRED_TEMP,
        _PARAM_CH_DETECTED_TEMPERATURE: _ARISTON_PAR_ZONE_MEAS_TEMP,
        _PARAM_CH_DEROGA_TEMPERATURE: _ARISTON_PAR_ZONE_DEROGA_TEMP,
        _PARAM_CH_COMFORT_TEMPERATURE: _ARISTON_PAR_ZONE_CONFORT_TEMP,
        _PARAM_CH_PILOT: _ARISTON_PAR_ZONE_PILOT,
        _PARAM_CH_ECONOMY_TEMPERATURE: _ARISTON_PAR_ZONE_ECONOMY_TEMP,
        _PARAM_HEATING_FLOW_TEMP: _ARISTON_PAR_HEATING_FLOW_TEMP,
        _PARAM_HEATING_FLOW_OFFSET: _ARISTON_PAR_HEATING_FLOW_OFFSET,
        _PARAM_COOLING_FLOW_TEMP: _ARISTON_PAR_COOLING_FLOW_TEMP,
        _PARAM_COOLING_FLOW_OFFSET: _ARISTON_PAR_COOLING_FLOW_OFFSET,
    }
    # Parameters in Web menu, mapping to parameter names
    _MAP_ARISTON_WEB_MENU_PARAMS = {
        _PARAM_INTERNET_TIME: _ARISTON_INTERNET_TIME,
        _PARAM_INTERNET_WEATHER: _ARISTON_INTERNET_WEATHER,
        _PARAM_THERMAL_CLEANSE_FUNCTION: _ARISTON_THERMAL_CLEANSE_FUNCTION,
        _PARAM_CH_AUTO_FUNCTION: _ARISTON_CH_AUTO_FUNCTION,
        _PARAM_DHW_COMFORT_FUNCTION: _ARISTON_DHW_COMFORT_FUNCTION,
        _PARAM_SIGNAL_STRENGTH: _ARISTON_SIGNAL_STRENGHT,
        _PARAM_THERMAL_CLEANSE_CYCLE: _ARISTON_THERMAL_CLEANSE_CYCLE,
        _PARAM_CH_WATER_TEMPERATURE: _ARISTON_CH_WATER_TEMPERATURE,
        # _PARAM_DHW_COMFORT_TEMPERATURE: _ARISTON_DHW_TIME_PROG_COMFORT,
        # _PARAM_DHW_ECONOMY_TEMPERATURE: _ARISTON_DHW_TIME_PROG_ECONOMY,
        _PARAM_CH_FIXED_TEMP: _ARISTON_CH_FIXED_TEMP,
    }
    _LIST_ARISTON_API_PARAMS = [
        *_MAP_ARISTON_ZONE_0_PARAMS.keys(),
        *_MAP_ARISTON_MULTIZONE_PARAMS.keys(),
        _PARAM_DHW_FLAME,
    ]
    _LIST_ARISTON_WEB_PARAMS = [
        *_MAP_ARISTON_WEB_MENU_PARAMS.keys(),
    ]
    # Sensors in error request
    _LIST_ERROR_PARAMS = [
        _PARAM_ERRORS_COUNT
    ]
    # Sensors in CH schedule program
    _LIST_CH_PROGRAM_PARAMS = [
        _PARAM_CH_PROGRAM
    ]
    # Sensors in DHW schedule program
    _LIST_DHW_PROGRAM_PARAMS = [
        _PARAM_DHW_PROGRAM
    ]
    # Sensors in last month energy
    _LIST_LAST_MONTH = [
        _PARAM_CH_LAST_MONTH_GAS,
        _PARAM_CH_LAST_MONTH_ELECTRICITY,
        _PARAM_DHW_LAST_MONTH_GAS,
        _PARAM_DHW_LAST_MONTH_ELECTRICITY,
    ]
    # Energy data
    _LIST_ENERGY = [
        _PARAM_CH_ENERGY_TODAY,
        _PARAM_CH_ENERGY_YESTERDAY,
        _PARAM_DHW_ENERGY_TODAY,
        _PARAM_DHW_ENERGY_YESTERDAY,
        _PARAM_CH_ENERGY_LAST_7_DAYS,
        _PARAM_DHW_ENERGY_LAST_7_DAYS,
        _PARAM_CH_ENERGY_THIS_MONTH,
        _PARAM_CH_ENERGY_LAST_MONTH,
        _PARAM_DHW_ENERGY_THIS_MONTH,
        _PARAM_DHW_ENERGY_LAST_MONTH,
        _PARAM_CH_ENERGY_THIS_YEAR,
        _PARAM_CH_ENERGY_LAST_YEAR,
        _PARAM_DHW_ENERGY_THIS_YEAR,
        _PARAM_DHW_ENERGY_LAST_YEAR,
        _PARAM_CH_ENERGY2_TODAY,
        _PARAM_CH_ENERGY2_YESTERDAY,
        _PARAM_DHW_ENERGY2_TODAY,
        _PARAM_DHW_ENERGY2_YESTERDAY,
        _PARAM_CH_ENERGY2_LAST_7_DAYS,
        _PARAM_DHW_ENERGY2_LAST_7_DAYS,
        _PARAM_CH_ENERGY2_THIS_MONTH,
        _PARAM_CH_ENERGY2_LAST_MONTH,
        _PARAM_DHW_ENERGY2_THIS_MONTH,
        _PARAM_DHW_ENERGY2_LAST_MONTH,
        _PARAM_CH_ENERGY2_THIS_YEAR,
        _PARAM_CH_ENERGY2_LAST_YEAR,
        _PARAM_DHW_ENERGY2_THIS_YEAR,
        _PARAM_DHW_ENERGY2_LAST_YEAR,
        _PARAM_CH_ENERGY_DELTA_TODAY,
        _PARAM_CH_ENERGY_DELTA_YESTERDAY,
        _PARAM_DHW_ENERGY_DELTA_TODAY,
        _PARAM_DHW_ENERGY_DELTA_YESTERDAY,
        _PARAM_CH_ENERGY_DELTA_LAST_7_DAYS,
        _PARAM_DHW_ENERGY_DELTA_LAST_7_DAYS,
        _PARAM_CH_ENERGY_DELTA_THIS_MONTH,
        _PARAM_CH_ENERGY_DELTA_LAST_MONTH,
        _PARAM_DHW_ENERGY_DELTA_THIS_MONTH,
        _PARAM_DHW_ENERGY_DELTA_LAST_MONTH,
        _PARAM_CH_ENERGY_DELTA_THIS_YEAR,
        _PARAM_CH_ENERGY_DELTA_LAST_YEAR,
        _PARAM_DHW_ENERGY_DELTA_THIS_YEAR,
        _PARAM_DHW_ENERGY_DELTA_LAST_YEAR,
    ]

    # reverse mapping of Android api to sensor names
    _MAP_ARISTON_API_TO_PARAM = {value:key for key, value in _MAP_ARISTON_ZONE_0_PARAMS.items()}
    for key, value in _MAP_ARISTON_MULTIZONE_PARAMS.items():
        _MAP_ARISTON_API_TO_PARAM[value] = key
    # reverse mapping of Web menu items to sensor names
    _MAP_ARISTON_WEB_TO_PARAM = {value:key for key, value in _MAP_ARISTON_WEB_MENU_PARAMS.items()}

    # List of all sensors
    _SENSOR_LIST = [
        *_LIST_ARISTON_API_PARAMS,
        *_LIST_ARISTON_WEB_PARAMS,
        *_LIST_ERROR_PARAMS,
        *_LIST_CH_PROGRAM_PARAMS,
        *_LIST_DHW_PROGRAM_PARAMS,
        *_LIST_LAST_MONTH,
        *_LIST_ENERGY,
        ]
    
    # List of sensors allowed to be changed
    _SENSOR_SET_LIST_TEMP = [
        _PARAM_MODE,
        _PARAM_CH_MODE,
        _PARAM_CH_SET_TEMPERATURE,
        _PARAM_CH_COMFORT_TEMPERATURE,
        _PARAM_CH_ECONOMY_TEMPERATURE,
        _PARAM_CH_AUTO_FUNCTION,
        _PARAM_CH_WATER_TEMPERATURE,
        _PARAM_CH_FIXED_TEMP,
        _PARAM_DHW_SET_TEMPERATURE,
        _PARAM_DHW_COMFORT_TEMPERATURE,
        _PARAM_DHW_ECONOMY_TEMPERATURE,
        _PARAM_DHW_COMFORT_FUNCTION,
        _PARAM_THERMAL_CLEANSE_CYCLE,
        _PARAM_THERMAL_CLEANSE_FUNCTION,
        _PARAM_INTERNET_TIME,
        _PARAM_INTERNET_WEATHER,
        _PARAM_DHW_MODE,
    ]

    @staticmethod
    def append_param(sensor, multizone_map, final_list):
        if sensor in multizone_map:
            for zone in range(1, 7):
                final_list.append(f'{sensor}_zone{zone}')
        else:
            final_list.append(sensor)

    _SENSOR_SET_LIST = []
    for sensor in _SENSOR_SET_LIST_TEMP:
        append_param(sensor, _MAP_ARISTON_MULTIZONE_PARAMS, _SENSOR_SET_LIST)

    # Requests
    _REQUEST_MAIN = "main"
    _REQUEST_CH_SCHEDULE = "ch_schedule"
    _REQUEST_DHW_SCHEDULE = "dhw_schedule"
    _REQUEST_ERRORS = "errors"
    _REQUEST_ADDITIONAL = "additional_params"
    _REQUEST_LAST_MONTH = "last_month"
    _REQUEST_ENERGY = "energy"

    maim_sensors_list = []
    for sensor in _LIST_ARISTON_API_PARAMS:
        append_param(sensor, _MAP_ARISTON_MULTIZONE_PARAMS, maim_sensors_list)
    
    # Mapping of sensors to requests
    _MAP_REQUEST = {
        _REQUEST_MAIN: maim_sensors_list,
        _REQUEST_ADDITIONAL: _LIST_ARISTON_WEB_PARAMS,
        _REQUEST_CH_SCHEDULE: _LIST_CH_PROGRAM_PARAMS,
        _REQUEST_DHW_SCHEDULE: _LIST_DHW_PROGRAM_PARAMS,
        _REQUEST_ERRORS: _LIST_ERROR_PARAMS,
        _REQUEST_ENERGY: _LIST_ENERGY,
        _REQUEST_LAST_MONTH: _LIST_LAST_MONTH,
    }

    _MAP_SENSOR_TO_REQUEST = {}
    for request, sensor_list in _MAP_REQUEST.items():
        for sensor in sensor_list:
            _MAP_SENSOR_TO_REQUEST[sensor] = request

    # Priority lists of requests (first list is High prio and second is Low prio)
    _REQUESTS_SEQUENCE = [
        [
            _REQUEST_MAIN,
            _REQUEST_ADDITIONAL,
            _REQUEST_ERRORS
        ],
        [
            _REQUEST_CH_SCHEDULE,
            _REQUEST_DHW_SCHEDULE,
            _REQUEST_LAST_MONTH,
            _REQUEST_ENERGY
        ]
    ]

    # Keys used in structures
    _VALUE = 'value'
    _SET_VALUE = "set_value"
    _UNITS = 'units'
    _MIN = 'min'
    _MAX = 'max'
    _STEP = 'step'
    _OPTIONS = 'options'
    _OPTIONS_TXT = 'options_text'
    _ATTRIBUTES = "attributes"
    _ATTEMPT = "attempt"

    # Values data for data mapping from received data to readable format
    _WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    _ON = "ON"
    _OFF = "OFF"
    _OFF_ON_NUMERAL = [0, 1]
    _OFF_ON_TEXT = [_OFF, _ON]
    _UNIT_KWH = 'kWh'

    _LOGGER = logging.getLogger(__name__)


    def _get_request_for_parameter(self, sensor):
        return self._MAP_SENSOR_TO_REQUEST[sensor]

    def _zone_sensor_name(self, sensor, zone):
        if sensor in self._MAP_ARISTON_MULTIZONE_PARAMS:
            return f'{sensor}_zone{zone}'
        else:
            return sensor

    def _zone_sensor_split(self, sensor):
        match = re.search('_zone[1-9]$', sensor)
        if match:
            origial = re.sub('_zone[1-9]$', '', sensor)
            if origial in self._MAP_ARISTON_MULTIZONE_PARAMS:
                return origial, int(sensor[-1])
        return sensor, 0

    def _reset_sensor(self, sensor):
        self._ariston_sensors[sensor] = dict()
        self._ariston_sensors[sensor][self._VALUE] = None
        self._ariston_sensors[sensor][self._UNITS] = None
        self._ariston_sensors[sensor][self._MIN] = None
        self._ariston_sensors[sensor][self._MAX] = None
        self._ariston_sensors[sensor][self._STEP] = None
        self._ariston_sensors[sensor][self._OPTIONS] = None
        self._ariston_sensors[sensor][self._OPTIONS_TXT] = None
        self._ariston_sensors[sensor][self._ATTRIBUTES] = {}


    def __init__(self,
                 username: str,
                 password: str,
                 sensors: list = None,
                 logging_level: str = _LEVEL_NOTSET,
                 period_get_request: int = _GET_SENSORS_PERIOD_SECONDS,
                 period_set_request: int = _SET_SENSORS_PERIOD_SECONDS,
                 set_max_retries: int = _MAX_RETRIES,
                 gw: str = "",
                 ) -> None:
        """
        Initialize API.
        """
        if sensors is None:
            sensors = list()

        if not isinstance(sensors, list):
            raise Exception("Invalid sensors type")

        if logging_level not in self._LOGGING_LEVELS:
            raise Exception("Invalid logging_level")

        if not isinstance(period_get_request, (int, float)) or period_get_request < self._GET_SENSORS_PERIOD_SECONDS:
            raise Exception(f"Period to get sensors must be a number higher than {self._GET_SENSORS_PERIOD_SECONDS}")

        if not isinstance(period_set_request, (int, float)) or period_set_request < self._SET_SENSORS_PERIOD_SECONDS:
            raise Exception(f"Period to set sensors must be a number higher than {self._SET_SENSORS_PERIOD_SECONDS}")

        if not isinstance(set_max_retries, int) or set_max_retries < 1:
            raise Exception(f"At least 1 retry to set data is expected")

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

        if sensors:
            for sensor in sensors:
                if sensor not in self._SENSOR_LIST:
                    self._LOGGER.warning(f"Unsupported sensor {sensor}")
                    sensors.remove(sensor)

        self._default_gw = gw
        self._user = username
        self._password = password
        self._get_period_time = period_get_request
        self._set_period_time = period_set_request
        self._max_set_retries = set_max_retries

        # clear read sensor values
        self._ariston_sensors = dict()
        self._subscribed_sensors_old_value = dict()
        for sensor in self._SENSOR_LIST:
            if sensor in self._MAP_ARISTON_MULTIZONE_PARAMS:
                for zone in range(1, 7):
                    ch_sensor = self._zone_sensor_name(sensor, zone=zone)
                    self._reset_sensor(ch_sensor)
                    self._subscribed_sensors_old_value[ch_sensor] = None
            else:
                self._reset_sensor(sensor)
                self._subscribed_sensors_old_value[sensor] = None
        
        # clear configuration data
        self._set_param = {}
        self._features = {}
        self._main_data = {}
        self._additional_data = {}
        self._error_data = {}
        self._ch_schedule_data = {}
        self._dhw_schedule_data = {}
        self._last_month_data = {}
        self._energy_use_data = {}
        self._zones = []

        self._last_dhw_storage_temp = None
        self._reset_set_requests()

        # initiate all other data
        self._errors = 0
        self._data_lock = threading.Lock()
        self._lock = threading.Lock()
        self._plant_id_lock = threading.Lock()
        self._session = requests.Session()
        self._login = False
        self._plant_id = ""
        self._started = False
        self._available = False
        self._ch_available = False
        self._dhw_available = False
        self._changing_data = False
        self._timer_periodic_read = threading.Timer(0, self._queue_get_data)
        self._timer_queue_delay = threading.Timer(0, self._control_availability_state, [self._REQUEST_MAIN])
        self._timer_set_delay = threading.Timer(0, self._preparing_setting_http_data)

        self._other_parameters = []
        for sensor in self._LIST_ARISTON_WEB_PARAMS:
            if sensor in sensors:
                self._other_parameters.append(self._MAP_ARISTON_WEB_MENU_PARAMS[sensor])
        
        # List of requests. First list is high priority requests and second list is low priority requests.
        # It affects frequency of the requests
        self._requests_lists = copy.deepcopy(self._REQUESTS_SEQUENCE)

        # If no sensors specified then no need to send the requests thus increasing frequency of fetching data for wanted sensors
        for request, sensor_list in self._MAP_REQUEST.items():
            if request != self._REQUEST_MAIN:
                # Main requests cannot be removed
                if not any(item in sensors for item in sensor_list):
                    if request in self._requests_lists[0]:
                        self._requests_lists[0].remove(request)
                    if request in self._requests_lists[1]:
                        self._requests_lists[1].remove(request)

        # At least 1 main request is present
        self._last_request = self._requests_lists[0][-1]
        if self._requests_lists[1]:
            # there are requests in low prio
            self._last_request_low_prio = self._requests_lists[1][-1]
        else:
            # no requests in low prio
            self._last_request_low_prio = None

        self._subscribed = list()
        self._subscribed_args = list()
        self._subscribed_kwargs = list()
        self._subscribed_thread = None

        self._subscribed2 = list()
        self._subscribed2_args = list()
        self._subscribed2_kwargs = list()
        self._subscribed2_thread = None

        self._LOGGER.info("API initiated")


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

        for sensor in self._ariston_sensors:
            if self._ariston_sensors[sensor][self._VALUE] != self._subscribed_sensors_old_value[sensor]:
                self._subscribed_sensors_old_value[sensor] = self._ariston_sensors[sensor][self._VALUE]
                changed_data[sensor] = copy.deepcopy(self._ariston_sensors[sensor])

        if changed_data:
            for iteration in range(len(self._subscribed)):
                self._subscribed_thread = threading.Timer(
                    self._TIME_SPLIT, self._subscribed[iteration], args=(changed_data, *self._subscribed_args[iteration]), kwargs=self._subscribed_kwargs[iteration])
                self._subscribed_thread.start()


    def _subscribers_statuses_inform(self):
        """Inform subscribers about changed API statuses"""
        old_available = self._available
        old_ch_available = self._ch_available
        old_dhw_available = self._dhw_available
        old_changing = self._changing_data

        changed_data = dict()

        self._available = self._errors <= self._MAX_ERRORS and self._login and self._plant_id != "" and self._main_data != {}

        if self._available and self._main_data != {} and \
            self._ariston_sensors[self._zone_sensor_name(self._PARAM_CH_SET_TEMPERATURE, 1)][self._VALUE] != None:
            self._ch_available = True
        else:
            self._ch_available = False

        if self._available and self._main_data != {} and \
            self._ariston_sensors[self._PARAM_DHW_SET_TEMPERATURE][self._VALUE] != None:
            self._dhw_available = True
        else:
            self._dhw_available = False

        if self._set_param != {}:
            self._changing_data = True
        else:
            self._changing_data = False

        if old_available != self._available:
            changed_data['available'] = self._available

        if old_ch_available != self._ch_available:
            changed_data['ch_available'] = self._ch_available

        if old_dhw_available != self._dhw_available:
            changed_data['dhw_available'] = self._dhw_available

        if old_changing != self._changing_data:
            changed_data['setting_data'] = self._changing_data

        if changed_data:
            for iteration in range(len(self._subscribed2)):
                self._subscribed2_thread = threading.Timer(
                    self._TIME_SPLIT, self._subscribed2[iteration], args=(changed_data, *self._subscribed2_args[iteration]), kwargs=self._subscribed2_kwargs[iteration])
                self._subscribed2_thread.start()


    def _json_validator(self, data, request_type):
        json_data = data.json()
        try:
            if isinstance(json_data, dict):
                if json_data == {}:
                    return False
                else:
                    return True
            if isinstance(json_data, list):
                if not json_data:
                    if request_type in (self._REQUEST_ERRORS):
                        return True
                    else:
                        return False
                else:
                    for item in json_data:
                        if not isinstance(item, dict):
                            return False
                    return True
            else:
                return False
        except KeyError:
            return False


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
        return copy.deepcopy(self._ariston_sensors)


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
        return copy.deepcopy(self._SENSOR_LIST)


    @property
    def supported_sensors_set(self) -> set:
        """
        Return set of all parameters that potentially can be set by API.
        Note that it is parameters supported by API, not the server, so some might be impossible to be set.
        use property 'supported_sensors_set_values' to find allowed values to be set.
        """
        return copy.deepcopy(self._SENSOR_SET_LIST)


    @property
    def supported_sensors_set_values(self) -> dict:
        """
        Return dictionary of sensors/parameters to be set and allowed values.
        Allowed values can be returned as:
            - dictionary with following keys:
                - 'min' is used to indicate minimum value in the range;
                - 'max' is used to indicate maximum value in the range;
                - 'step' is used to indicate step;
                - 'options' is list of options numeric;
                - 'options_text' is list of options literal;

        data from this property is used for 'set_http_data' method.
        """
        sensors_dictionary = copy.deepcopy(self._ariston_sensors)
        for parameter in self._ariston_sensors:
            if parameter in self._SENSOR_SET_LIST:
                del sensors_dictionary[parameter][self._VALUE]
                del sensors_dictionary[parameter][self._UNITS]
                del sensors_dictionary[parameter][self._ATTRIBUTES]
            else:
                del sensors_dictionary[parameter]
        return sensors_dictionary


    def _request_post(self, url, json_data, timeout=_TIMEOUT_MIN, error_msg=''):
        """ post request """
        try:
            resp = self._session.post(
                url,
                timeout=timeout,
                json=json_data,
                verify=True)
        except requests.exceptions.RequestException as ex:
            self._LOGGER.warning(f'{error_msg} exception: {ex}')
            raise Exception(f'{error_msg} exception: {ex}')
        if not resp.ok:
            self._LOGGER.warning(f'{error_msg} reply code: {resp.status_code}')
            self._LOGGER.warning(f'{resp.text}')
            raise Exception(f'{error_msg} reply code: {resp.status_code}')
        return resp


    def _request_get(self, url, timeout=_TIMEOUT_MIN, error_msg='', ignore_errors=False):
        try:
            resp = self._session.get(
                url,
                timeout=timeout,
                verify=True)
        except requests.exceptions.RequestException as ex:
            self._LOGGER.warning(f'{error_msg} exception: {ex}')
            if not ignore_errors:
                raise Exception(f'{error_msg} exception: {ex}')
        if not resp.ok:
            log_text = True
            if resp.status_code == 500:
                # Unsupported additional parameters are visible in the HTML reply, remove them if available
                for re_string in re.findall('Violated Postcondition.*menu', resp.text):
                    for sensor, menu_item in self._MAP_ARISTON_WEB_MENU_PARAMS.items():
                        html_item = menu_item.replace('U','').replace('_','.')
                        check_menu = f"&quot;{html_item}&quot;"
                        if check_menu in re_string:
                            self._LOGGER.error(f'Unsupported sensor {sensor} detected with menu item {menu_item}')
                            self._other_parameters.remove(menu_item)
                            if not self._other_parameters:
                                self._requests_lists[0].remove(self._REQUEST_ADDITIONAL)
                            log_text = False
            self._LOGGER.warning(f'{error_msg} reply code: {resp.status_code}')
            if log_text:
                self._LOGGER.warning(f'{resp.text}')
            if not ignore_errors:
                raise Exception(f'{error_msg} reply code: {resp.status_code}')
        return resp


    def _login_session(self):
        """Login to fetch Ariston Plant ID and confirm login"""
        if not self._login and self._started:
            # First login
            login_data = {
                "email": self._user,
                "password": self._password,
                "rememberMe": False,
                "language": "English_Us"
                }
            self._request_post(
                url=f'{self._ARISTON_URL}/R2/Account/Login?returnUrl=%2FR2%2FHome',
                json_data=login_data,
                error_msg='Login'
            )

            # Fetch plant IDs
            resp = self._request_get(
                url=f'{self._ARISTON_URL}/api/v2/remote/plants/lite',
                error_msg='Gateways'
            )
            gateways = [item['gwId'] for item in resp.json()]
            if self._default_gw:
                if self._default_gw not in gateways:
                    self._LOGGER.error(f'Specified gateway {self._default_gw} not found in {gateways}')
                    raise Exception(f'Specified gateway {self._default_gw} not found in {gateways}')
                else:
                    plant_id = self._default_gw
            else:
                if len(gateways) == 0:
                    self._LOGGER.error(f'At least one gateway is expected to be found')
                    raise Exception(f'At least one gateway is expected to be found')
                # Use first plant plant id
                plant_id = gateways[0]
            resp = self._request_get(
                url=f'{self._ARISTON_URL}/api/v2/remote/plants/{plant_id}/features?eagerMode=True',
                error_msg='Features'
            )
            features = resp.json()
            if plant_id:
                with self._plant_id_lock:
                    self._features = copy.deepcopy(features)
                    if self._features["zones"]:
                        self._zones = [item["num"] for item in self._features["zones"]]
                    self._plant_id = plant_id
                    self._gw_name = plant_id + '_'
                    self._login = True
                    self._LOGGER.info(f'Plant ID is {self._plant_id}')
        return


    def _get_visible_sensor_value(self, sensor):
        value = self._get_sensor_value(sensor)
        if sensor in self._set_param:
            if value == self._set_param[sensor][self._VALUE]:
                # Value is assumed to be set
                del self._set_param[sensor]
                self._subscribers_statuses_inform()
                self._reset_set_requests()
                self._LOGGER.debug(f'Sensor {sensor} value {value} matches expected set value')
            else:
                self._LOGGER.debug(f'Sensor {sensor} expected value {self._set_param[sensor][self._VALUE]} but actual value is {value}')
                value = self._set_param[sensor][self._VALUE]
        return value


    def _get_sensor_value(self, sensor):
        value = None
        request_type = self._get_request_for_parameter(sensor)
        if request_type == self._REQUEST_MAIN:
            original_sensor, zone = self._zone_sensor_split(sensor)
            for item in self._main_data["items"]:
                if original_sensor == self._MAP_ARISTON_API_TO_PARAM[item["id"]] and zone == item["zone"]:
                    value = item["value"]
                    if "options" in item:
                        use_index = item["options"].index(int(item["value"]))
                        if "optTexts" in item:
                            value = item["optTexts"][use_index]
                        elif item["options"] == self._OFF_ON_NUMERAL:
                            value = self._OFF_ON_TEXT[use_index]
                    break
        elif request_type == self._REQUEST_ADDITIONAL:
            for item in self._additional_data["data"]:
                if sensor == self._MAP_ARISTON_WEB_TO_PARAM[item["id"]]:
                    value = item["value"]
                    if "dropDownOptions" in item and item["dropDownOptions"]:
                        for option in item["dropDownOptions"]:
                            if option["value"] == item["value"]:
                                value = option["text"]
                                break
                    break
        if sensor == self._PARAM_DHW_FLAME:
            value = None
            try:
                increase_dhw_temp = None
                new_value = self._ariston_sensors[self._PARAM_DHW_STORAGE_TEMPERATURE][self._VALUE]
                if new_value:
                    increase_dhw_temp = False
                    if self._last_dhw_storage_temp is not None and \
                        self._last_dhw_storage_temp > 0 and \
                        new_value > 0:
                        if new_value > self._last_dhw_storage_temp:
                            increase_dhw_temp = True
                    elif self._last_dhw_storage_temp is not None and\
                        new_value > 0:
                        self._last_dhw_storage_temp = new_value
            except Exception:
                increase_dhw_temp = None
            ch_flame = None
            for zone in self._zones:
                ch_flame_zone = self._ariston_sensors[self._zone_sensor_name(self._PARAM_FLAME, zone)][self._VALUE]
                if ch_flame_zone in self._OFF_ON_TEXT:
                    if ch_flame is None or ch_flame == self._OFF:
                        ch_flame = ch_flame_zone
            if self._ariston_sensors[self._PARAM_FLAME][self._VALUE] in self._OFF_ON_TEXT and ch_flame in self._OFF_ON_TEXT:
                if self._ariston_sensors[self._PARAM_FLAME][self._VALUE] == self._OFF:
                    value = self._OFF
                elif ch_flame == self._OFF:
                    value = self._ON
                else:
                    # Unknown state of DHW
                    value = increase_dhw_temp
        return value


    def _schedule_attributes(self, scan_dictionary):
        attributes = {key: None for key in self._WEEKDAYS}
        for item in scan_dictionary:
            time_slices = []
            for slice in item["slices"]:
                if slice['temp'] == 0:
                    temp_name = "Economy"
                else:
                    temp_name = "Comfort"
                time_slices.append(f'From {slice["from"]//60:02}:{slice["from"]%60:02} {temp_name}')
            for day_num in item["days"]:
                attributes[self._WEEKDAYS[day_num]] = time_slices
        return attributes


    def _store_data(self, resp, request_type=""):
        """Store received dictionary"""
        if not self._json_validator(resp, request_type):
            self._LOGGER.warning(f"JSON did not pass validation for the request {request_type}")
            raise Exception(f"JSON did not pass validation for the request {request_type}")

        if request_type == self._REQUEST_MAIN:

            self._main_data = copy.deepcopy(resp.json())
            for item in self._main_data["items"]:
                try:
                    original_sensor = self._MAP_ARISTON_API_TO_PARAM[item["id"]]
                    zone = item["zone"]
                    sensor = self._zone_sensor_name(original_sensor, zone=zone)
                    self._ariston_sensors[sensor]
                    try:
                        self._ariston_sensors[sensor][self._VALUE] = self._get_visible_sensor_value(sensor)
                        if "min" in item:
                            self._ariston_sensors[sensor][self._MIN] = item["min"]
                        if "max" in item:
                            self._ariston_sensors[sensor][self._MAX] = item["max"]
                        if "step" in item:
                            self._ariston_sensors[sensor][self._STEP] = item["step"]
                        if "unit" in item and item["unit"]:
                            self._ariston_sensors[sensor][self._UNITS] = item["unit"]
                        if "options" in item:
                            self._ariston_sensors[sensor][self._OPTIONS] = copy.deepcopy(item["options"])
                            if "optTexts" in item:
                                self._ariston_sensors[sensor][self._OPTIONS_TXT] = copy.deepcopy(item["optTexts"])
                            elif item["options"] == self._OFF_ON_NUMERAL:
                                self._ariston_sensors[sensor][self._OPTIONS_TXT] = self._OFF_ON_TEXT
                    except Exception as ex:
                        self._LOGGER.warn(f"Issue reading {request_type} {sensor} {ex}")
                        self._reset_sensor(sensor)
                        continue
                except Exception as ex:
                    self._LOGGER.warn(f'Issue reading {request_type} {item["id"]}, {ex}')
                    continue

            # Extrapolate DHW Flame
            sensor = self._PARAM_DHW_FLAME
            dhw_flame = self._get_visible_sensor_value(sensor)
            self._ariston_sensors[sensor][self._VALUE] = dhw_flame
            if dhw_flame:
                self._ariston_sensors[sensor][self._OPTIONS] = self._OFF_ON_NUMERAL
                self._ariston_sensors[sensor][self._OPTIONS_TXT] = self._OFF_ON_TEXT
            else:
                self._ariston_sensors[sensor][self._OPTIONS] = None
                self._ariston_sensors[sensor][self._OPTIONS_TXT] = None

            # Fix min and Max for CH set temperature
            for zone in self._zones:
                self._ariston_sensors[self._zone_sensor_name(self._PARAM_CH_SET_TEMPERATURE, zone)][self._MIN] = \
                    self._ariston_sensors[self._zone_sensor_name(self._PARAM_CH_COMFORT_TEMPERATURE, zone)][self._MIN]
                self._ariston_sensors[self._zone_sensor_name(self._PARAM_CH_SET_TEMPERATURE, zone)][self._MAX] = \
                    self._ariston_sensors[self._zone_sensor_name(self._PARAM_CH_COMFORT_TEMPERATURE, zone)][self._MAX]
                self._ariston_sensors[self._zone_sensor_name(self._PARAM_CH_SET_TEMPERATURE, zone)][self._STEP] = \
                    self._ariston_sensors[self._zone_sensor_name(self._PARAM_CH_COMFORT_TEMPERATURE, zone)][self._STEP]

        elif request_type == self._REQUEST_ERRORS:

            self._error_data = copy.deepcopy(resp.json())
            sensor = self._PARAM_ERRORS_COUNT
            try:
                # TEST DATA BELOW FOR PARSING PURPOSES
                # self._error_data = [{"gw":"F0AD4E0590BD","timestamp":"2022-07-14T10:55:04","fault":45,"mult":0,"code":"501","pri":1053500,"errDex":"No flame detected","res":False,"blk":True}]
                self._ariston_sensors[sensor][self._VALUE] = len(self._error_data)
                attributes = {}
                for index, item in enumerate(self._error_data):
                    attributes[f'Error_{index+1}'] = f'{item["timestamp"]}, {item["errDex"]}'
                self._ariston_sensors[sensor][self._ATTRIBUTES] = attributes
            except Exception as ex:
                self._LOGGER.warn(f'Issue reading {request_type} {sensor}, {ex}')
                self._reset_sensor(sensor)

        elif request_type == self._REQUEST_CH_SCHEDULE:

            self._ch_schedule_data = copy.deepcopy(resp.json())
            sensor = self._PARAM_CH_PROGRAM
            try:
                self._ariston_sensors[sensor][self._VALUE] = "Available"
                self._ariston_sensors[sensor][self._ATTRIBUTES] = self._schedule_attributes(self._ch_schedule_data["ChZn1"]["plans"])
            except Exception as ex:
                self._LOGGER.warn(f'Issue reading {request_type} {sensor}, {ex}')
                self._reset_sensor(sensor)

        elif request_type == self._REQUEST_DHW_SCHEDULE:

            self._dhw_schedule_data = copy.deepcopy(resp.json())
            sensor = self._PARAM_DHW_PROGRAM
            try:
                self._ariston_sensors[sensor][self._VALUE] = "Available"
                self._ariston_sensors[sensor][self._ATTRIBUTES] = self._schedule_attributes(self._dhw_schedule_data["Dhw"]["plans"])
            except Exception as ex:
                self._LOGGER.warn(f'Issue reading {request_type} {sensor}, {ex}')
                self._reset_sensor(sensor)

        elif request_type == self._REQUEST_ADDITIONAL:
            
            self._additional_data = copy.deepcopy(resp.json())
            for item in self._additional_data["data"]:
                try:
                    sensor = self._MAP_ARISTON_WEB_TO_PARAM[item["id"]]
                    self._ariston_sensors[sensor]
                    try:
                        self._ariston_sensors[sensor][self._VALUE] = self._get_visible_sensor_value(sensor)
                        if "min" in item:
                            self._ariston_sensors[sensor][self._MIN] = item["min"]
                        if "max" in item:
                            self._ariston_sensors[sensor][self._MAX] = item["max"]
                        if "increment" in item:
                            self._ariston_sensors[sensor][self._STEP] = item["increment"]
                        if "unitLabel" in item and item["unitLabel"]:
                            self._ariston_sensors[sensor][self._UNITS] = item["unitLabel"]
                        if "dropDownOptions" in item and item["dropDownOptions"]:
                            self._ariston_sensors[sensor][self._OPTIONS] = [option["value"] for option in item["dropDownOptions"]]
                            self._ariston_sensors[sensor][self._OPTIONS_TXT] = [option["text"] for option in item["dropDownOptions"]]
                    except Exception as ex:
                        self._LOGGER.warn(f"Issue reading {request_type} {sensor} {ex}")
                        self._reset_sensor(sensor)
                        continue
                except Exception as ex:
                    self._LOGGER.warn(f'Issue reading {request_type} {item["id"]}, {ex}')
                    continue

        elif request_type == self._REQUEST_LAST_MONTH:

            self._last_month_data = copy.deepcopy(resp.json())
            self._reset_sensor(self._PARAM_CH_LAST_MONTH_GAS)
            self._reset_sensor(self._PARAM_CH_LAST_MONTH_ELECTRICITY)
            self._reset_sensor(self._PARAM_DHW_LAST_MONTH_GAS)
            self._reset_sensor(self._PARAM_DHW_LAST_MONTH_ELECTRICITY)
            for item in self._last_month_data["LastMonth"]:
                try:
                    if item["use"] == 1:
                        if "gas" in item:
                            sensor = self._PARAM_CH_LAST_MONTH_GAS
                            self._ariston_sensors[sensor][self._VALUE] = item["gas"]
                            self._ariston_sensors[sensor][self._UNITS] = self._UNIT_KWH
                        if "elect" in item:
                            sensor = self._PARAM_CH_LAST_MONTH_ELECTRICITY
                            self._ariston_sensors[sensor][self._VALUE] = item["elect"]
                            self._ariston_sensors[sensor][self._UNITS] = self._UNIT_KWH
                    if item["use"] == 2:
                        if "gas" in item:
                            sensor = self._PARAM_DHW_LAST_MONTH_GAS
                            self._ariston_sensors[sensor][self._VALUE] = item["gas"]
                            self._ariston_sensors[sensor][self._UNITS] = self._UNIT_KWH
                        if "elect" in item:
                            sensor = self._PARAM_DHW_LAST_MONTH_ELECTRICITY
                            self._ariston_sensors[sensor][self._VALUE] = item["elect"]
                            self._ariston_sensors[sensor][self._UNITS] = self._UNIT_KWH
                except Exception as ex:
                    self._LOGGER.warn(f'Issue reading {request_type} {item["use"]} for last month, {ex}')
                    continue

        elif request_type == self._REQUEST_ENERGY:

            if self._energy_use_data:
                # old values are available
                sum_energy_old = 0
                sum_energy_new = 0
                for item in self._energy_use_data:
                    sum_energy_old += sum(item['v'])
                for item in resp.json():
                    sum_energy_new += sum(item['v'])
                if sum_energy_old > 0 and sum_energy_new == 0:
                    # if non-zero values are present and new value is zero - ignore it 
                    return

            self._energy_use_data = copy.deepcopy(resp.json())
            this_month = datetime.date.today().month
            this_year = datetime.date.today().year
            this_day = datetime.date.today().day
            this_day_week = datetime.date.today().weekday()
            this_hour = datetime.datetime.now().hour
            CH_ENERGY = 7
            DHW_ENERGY = 10
            CH_ENERGY2 = 1
            DHW_ENERGY2 = 2
            CH_ENERGY_DELTA = 20
            DHW_ENERGY_DELTA = 21
            # 2hour during scanning is decreased by 2 at the beginning
            if this_hour % 2 == 1:
                # odd value means we calculate even value and add 2 hours due to following decrease
                this_2hour = (this_hour // 2) * 2 + 2
            else:
                # we assume that previous 2 hours would be used
                this_2hour = this_hour + 2
            try:
                (
                    self._ariston_sensors[self._PARAM_CH_ENERGY_TODAY][self._VALUE],
                    self._ariston_sensors[self._PARAM_CH_ENERGY_YESTERDAY][self._VALUE],
                    self._ariston_sensors[self._PARAM_CH_ENERGY_LAST_7_DAYS][self._VALUE],
                    self._ariston_sensors[self._PARAM_CH_ENERGY_THIS_MONTH][self._VALUE],
                    self._ariston_sensors[self._PARAM_CH_ENERGY_LAST_MONTH][self._VALUE],
                    self._ariston_sensors[self._PARAM_CH_ENERGY_THIS_YEAR][self._VALUE],
                    self._ariston_sensors[self._PARAM_CH_ENERGY_LAST_YEAR][self._VALUE],
                    self._ariston_sensors[self._PARAM_CH_ENERGY_TODAY][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_CH_ENERGY_YESTERDAY][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_CH_ENERGY_LAST_7_DAYS][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_CH_ENERGY_THIS_MONTH][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_CH_ENERGY_LAST_MONTH][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_CH_ENERGY_THIS_YEAR][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_CH_ENERGY_LAST_YEAR][self._ATTRIBUTES],
                    found_key,
                ) = self._get_energy_data(
                    CH_ENERGY,
                    this_year=this_year,
                    this_month=this_month,
                    this_day=this_day,
                    this_day_week=this_day_week,
                    this_2hour=this_2hour)
                if found_key:
                    self._ariston_sensors[self._PARAM_CH_ENERGY_TODAY][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_CH_ENERGY_YESTERDAY][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_CH_ENERGY_LAST_7_DAYS][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_CH_ENERGY_THIS_MONTH][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_CH_ENERGY_LAST_MONTH][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_CH_ENERGY_THIS_YEAR][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_CH_ENERGY_LAST_YEAR][self._UNITS] = self._UNIT_KWH
            except Exception as ex:
                self._LOGGER.warn(f'Issue handling energy used for CH, {ex}')
                self._reset_sensor(self._PARAM_CH_ENERGY_TODAY)
                self._reset_sensor(self._PARAM_CH_ENERGY_YESTERDAY)
                self._reset_sensor(self._PARAM_CH_ENERGY_LAST_7_DAYS)
                self._reset_sensor(self._PARAM_CH_ENERGY_THIS_MONTH)
                self._reset_sensor(self._PARAM_CH_ENERGY_LAST_MONTH)
                self._reset_sensor(self._PARAM_CH_ENERGY_THIS_YEAR)
                self._reset_sensor(self._PARAM_CH_ENERGY_LAST_YEAR)
            try:
                (
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_TODAY][self._VALUE],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_YESTERDAY][self._VALUE],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_LAST_7_DAYS][self._VALUE],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_THIS_MONTH][self._VALUE],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_LAST_MONTH][self._VALUE],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_THIS_YEAR][self._VALUE],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_LAST_YEAR][self._VALUE],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_TODAY][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_YESTERDAY][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_LAST_7_DAYS][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_THIS_MONTH][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_LAST_MONTH][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_THIS_YEAR][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_LAST_YEAR][self._ATTRIBUTES],
                    found_key,
                ) = self._get_energy_data(
                    DHW_ENERGY,
                    this_year=this_year,
                    this_month=this_month,
                    this_day=this_day,
                    this_day_week=this_day_week,
                    this_2hour=this_2hour)
                if found_key:
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_TODAY][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_YESTERDAY][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_LAST_7_DAYS][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_THIS_MONTH][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_LAST_MONTH][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_THIS_YEAR][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_LAST_YEAR][self._UNITS] = self._UNIT_KWH
            except Exception as ex:
                self._LOGGER.warn(f'Issue handling energy used for DHW, {ex}')
                self._reset_sensor(self._PARAM_DHW_ENERGY_TODAY)
                self._reset_sensor(self._PARAM_DHW_ENERGY_YESTERDAY)
                self._reset_sensor(self._PARAM_DHW_ENERGY_LAST_7_DAYS)
                self._reset_sensor(self._PARAM_DHW_ENERGY_THIS_MONTH)
                self._reset_sensor(self._PARAM_DHW_ENERGY_LAST_MONTH)
                self._reset_sensor(self._PARAM_DHW_ENERGY_THIS_YEAR)
                self._reset_sensor(self._PARAM_DHW_ENERGY_LAST_YEAR)
            try:
                (
                    self._ariston_sensors[self._PARAM_CH_ENERGY2_TODAY][self._VALUE],
                    self._ariston_sensors[self._PARAM_CH_ENERGY2_YESTERDAY][self._VALUE],
                    self._ariston_sensors[self._PARAM_CH_ENERGY2_LAST_7_DAYS][self._VALUE],
                    self._ariston_sensors[self._PARAM_CH_ENERGY2_THIS_MONTH][self._VALUE],
                    self._ariston_sensors[self._PARAM_CH_ENERGY2_LAST_MONTH][self._VALUE],
                    self._ariston_sensors[self._PARAM_CH_ENERGY2_THIS_YEAR][self._VALUE],
                    self._ariston_sensors[self._PARAM_CH_ENERGY2_LAST_YEAR][self._VALUE],
                    self._ariston_sensors[self._PARAM_CH_ENERGY2_TODAY][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_CH_ENERGY2_YESTERDAY][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_CH_ENERGY2_LAST_7_DAYS][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_CH_ENERGY2_THIS_MONTH][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_CH_ENERGY2_LAST_MONTH][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_CH_ENERGY2_THIS_YEAR][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_CH_ENERGY2_LAST_YEAR][self._ATTRIBUTES],
                    found_key,
                ) = self._get_energy_data(
                    CH_ENERGY2,
                    this_year=this_year,
                    this_month=this_month,
                    this_day=this_day,
                    this_day_week=this_day_week,
                    this_2hour=this_2hour)
                if found_key:
                    self._ariston_sensors[self._PARAM_CH_ENERGY2_TODAY][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_CH_ENERGY2_YESTERDAY][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_CH_ENERGY2_LAST_7_DAYS][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_CH_ENERGY2_THIS_MONTH][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_CH_ENERGY2_LAST_MONTH][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_CH_ENERGY2_THIS_YEAR][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_CH_ENERGY2_LAST_YEAR][self._UNITS] = self._UNIT_KWH
            except Exception as ex:
                self._LOGGER.warn(f'Issue handling energy used for CH 2, {ex}')
                self._reset_sensor(self._PARAM_CH_ENERGY2_TODAY)
                self._reset_sensor(self._PARAM_CH_ENERGY2_YESTERDAY)
                self._reset_sensor(self._PARAM_CH_ENERGY2_LAST_7_DAYS)
                self._reset_sensor(self._PARAM_CH_ENERGY2_THIS_MONTH)
                self._reset_sensor(self._PARAM_CH_ENERGY2_LAST_MONTH)
                self._reset_sensor(self._PARAM_CH_ENERGY2_THIS_YEAR)
                self._reset_sensor(self._PARAM_CH_ENERGY2_LAST_YEAR)
            try:
                (
                    self._ariston_sensors[self._PARAM_DHW_ENERGY2_TODAY][self._VALUE],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY2_YESTERDAY][self._VALUE],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY2_LAST_7_DAYS][self._VALUE],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY2_THIS_MONTH][self._VALUE],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY2_LAST_MONTH][self._VALUE],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY2_THIS_YEAR][self._VALUE],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY2_LAST_YEAR][self._VALUE],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY2_TODAY][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY2_YESTERDAY][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY2_LAST_7_DAYS][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY2_THIS_MONTH][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY2_LAST_MONTH][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY2_THIS_YEAR][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY2_LAST_YEAR][self._ATTRIBUTES],
                    found_key,
                ) = self._get_energy_data(
                    DHW_ENERGY2,
                    this_year=this_year,
                    this_month=this_month,
                    this_day=this_day,
                    this_day_week=this_day_week,
                    this_2hour=this_2hour)
                if found_key:
                    self._ariston_sensors[self._PARAM_DHW_ENERGY2_TODAY][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_DHW_ENERGY2_YESTERDAY][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_DHW_ENERGY2_LAST_7_DAYS][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_DHW_ENERGY2_THIS_MONTH][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_DHW_ENERGY2_LAST_MONTH][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_DHW_ENERGY2_THIS_YEAR][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_DHW_ENERGY2_LAST_YEAR][self._UNITS] = self._UNIT_KWH
            except Exception as ex:
                self._LOGGER.warn(f'Issue handling energy used for DHW 2, {ex}')
                self._reset_sensor(self._PARAM_DHW_ENERGY2_TODAY)
                self._reset_sensor(self._PARAM_DHW_ENERGY2_YESTERDAY)
                self._reset_sensor(self._PARAM_DHW_ENERGY2_LAST_7_DAYS)
                self._reset_sensor(self._PARAM_DHW_ENERGY2_THIS_MONTH)
                self._reset_sensor(self._PARAM_DHW_ENERGY2_LAST_MONTH)
                self._reset_sensor(self._PARAM_DHW_ENERGY2_THIS_YEAR)
                self._reset_sensor(self._PARAM_DHW_ENERGY2_LAST_YEAR)
            try:
                (
                    self._ariston_sensors[self._PARAM_CH_ENERGY_DELTA_TODAY][self._VALUE],
                    self._ariston_sensors[self._PARAM_CH_ENERGY_DELTA_YESTERDAY][self._VALUE],
                    self._ariston_sensors[self._PARAM_CH_ENERGY_DELTA_LAST_7_DAYS][self._VALUE],
                    self._ariston_sensors[self._PARAM_CH_ENERGY_DELTA_THIS_MONTH][self._VALUE],
                    self._ariston_sensors[self._PARAM_CH_ENERGY_DELTA_LAST_MONTH][self._VALUE],
                    self._ariston_sensors[self._PARAM_CH_ENERGY_DELTA_THIS_YEAR][self._VALUE],
                    self._ariston_sensors[self._PARAM_CH_ENERGY_DELTA_LAST_YEAR][self._VALUE],
                    self._ariston_sensors[self._PARAM_CH_ENERGY_DELTA_TODAY][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_CH_ENERGY_DELTA_YESTERDAY][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_CH_ENERGY_DELTA_LAST_7_DAYS][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_CH_ENERGY_DELTA_THIS_MONTH][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_CH_ENERGY_DELTA_LAST_MONTH][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_CH_ENERGY_DELTA_THIS_YEAR][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_CH_ENERGY_DELTA_LAST_YEAR][self._ATTRIBUTES],
                    found_key,
                ) = self._get_energy_data(
                    CH_ENERGY_DELTA,
                    this_year=this_year,
                    this_month=this_month,
                    this_day=this_day,
                    this_day_week=this_day_week,
                    this_2hour=this_2hour)
                if found_key:
                    self._ariston_sensors[self._PARAM_CH_ENERGY_DELTA_TODAY][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_CH_ENERGY_DELTA_YESTERDAY][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_CH_ENERGY_DELTA_LAST_7_DAYS][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_CH_ENERGY_DELTA_THIS_MONTH][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_CH_ENERGY_DELTA_LAST_MONTH][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_CH_ENERGY_DELTA_THIS_YEAR][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_CH_ENERGY_DELTA_LAST_YEAR][self._UNITS] = self._UNIT_KWH
            except Exception as ex:
                self._LOGGER.warn(f'Issue handling energy used for CH 2, {ex}')
                self._reset_sensor(self._PARAM_CH_ENERGY_DELTA_TODAY)
                self._reset_sensor(self._PARAM_CH_ENERGY_DELTA_YESTERDAY)
                self._reset_sensor(self._PARAM_CH_ENERGY_DELTA_LAST_7_DAYS)
                self._reset_sensor(self._PARAM_CH_ENERGY_DELTA_THIS_MONTH)
                self._reset_sensor(self._PARAM_CH_ENERGY_DELTA_LAST_MONTH)
                self._reset_sensor(self._PARAM_CH_ENERGY_DELTA_THIS_YEAR)
                self._reset_sensor(self._PARAM_CH_ENERGY_DELTA_LAST_YEAR)
            try:
                (
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_DELTA_TODAY][self._VALUE],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_DELTA_YESTERDAY][self._VALUE],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_DELTA_LAST_7_DAYS][self._VALUE],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_DELTA_THIS_MONTH][self._VALUE],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_DELTA_LAST_MONTH][self._VALUE],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_DELTA_THIS_YEAR][self._VALUE],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_DELTA_LAST_YEAR][self._VALUE],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_DELTA_TODAY][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_DELTA_YESTERDAY][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_DELTA_LAST_7_DAYS][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_DELTA_THIS_MONTH][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_DELTA_LAST_MONTH][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_DELTA_THIS_YEAR][self._ATTRIBUTES],
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_DELTA_LAST_YEAR][self._ATTRIBUTES],
                    found_key,
                ) = self._get_energy_data(
                    DHW_ENERGY_DELTA,
                    this_year=this_year,
                    this_month=this_month,
                    this_day=this_day,
                    this_day_week=this_day_week,
                    this_2hour=this_2hour)
                if found_key:
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_DELTA_TODAY][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_DELTA_YESTERDAY][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_DELTA_LAST_7_DAYS][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_DELTA_THIS_MONTH][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_DELTA_LAST_MONTH][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_DELTA_THIS_YEAR][self._UNITS] = self._UNIT_KWH
                    self._ariston_sensors[self._PARAM_DHW_ENERGY_DELTA_LAST_YEAR][self._UNITS] = self._UNIT_KWH
            except Exception as ex:
                self._LOGGER.warn(f'Issue handling energy used for DHW 2, {ex}')
                self._reset_sensor(self._PARAM_DHW_ENERGY_DELTA_TODAY)
                self._reset_sensor(self._PARAM_DHW_ENERGY_DELTA_YESTERDAY)
                self._reset_sensor(self._PARAM_DHW_ENERGY_DELTA_LAST_7_DAYS)
                self._reset_sensor(self._PARAM_DHW_ENERGY_DELTA_THIS_MONTH)
                self._reset_sensor(self._PARAM_DHW_ENERGY_DELTA_LAST_MONTH)
                self._reset_sensor(self._PARAM_DHW_ENERGY_DELTA_THIS_YEAR)
                self._reset_sensor(self._PARAM_DHW_ENERGY_DELTA_LAST_YEAR)

        self._subscribers_sensors_inform()


    def _get_energy_data(self, k_num, this_year, this_month, this_day, this_day_week, this_2hour):
        energy_today = 0
        energy_yesterday = 0
        energy_last_7_days = 0
        energy_this_month = 0
        energy_last_month = 0
        energy_this_year = 0
        energy_last_year = 0
        energy_today_attr = {}
        energy_yesterday_attr = {}
        energy_last_7_days_attr = {}
        energy_this_month_attr = {}
        energy_last_month_attr = {}
        energy_this_year_attr = {}
        energy_last_year_attr = {}
        hour_text = "{}_{}_{:02}_{:02}"
        weekday_text = "{}_{}_{:02}_{}"
        month_text = "{}_{}_{:02}"
        year_text = "{}_{}"
        found_key = False
        for item in self._energy_use_data:
            if item["k"] == k_num:
                found_key = True
                scan_month = this_month
                scan_year = this_year
                scan_day = this_day
                scan_day_week = this_day_week
                scan_2hour = this_2hour
                scan_break = 0
                if item['p'] == 1:
                    prev_day, prev_month, prev_year, _ = self._get_prev_day(day=this_day, month=this_month, year=this_year, scan_break=0)
                    prev_day_2, prev_month_2, prev_year_2, _ = self._get_prev_day(day=prev_day, month=prev_month, year=prev_year, scan_break=0)
                    use_day, use_month, use_year = this_day, this_month, this_year
                    if this_2hour == 2:
                        midnight = True
                    else:
                        midnight = False
                    for value in reversed(item['v']):
                        scan_2hour, scan_break = self._get_prev_hour(hour=scan_2hour, scan_break=scan_break)
                        if midnight and scan_break == 1:
                            # ignore first break
                            scan_break = 0
                            use_day, use_month, use_year = prev_day, prev_month, prev_year
                            prev_day, prev_month, prev_year = prev_day_2, prev_month_2, prev_year_2
                            midnight = False
                        if scan_break == 0:
                            energy_today_attr[hour_text.format(use_year, calendar.month_abbr[use_month], use_day, scan_2hour)] = value
                            energy_today += value
                        elif scan_break == 1:
                            energy_yesterday_attr[hour_text.format(prev_year, calendar.month_abbr[prev_month], prev_day, scan_2hour)] = value
                            energy_yesterday += value
                if item['p'] == 2:
                    for value in reversed(item['v']):
                        scan_day, scan_month, scan_year, _ = self._get_prev_day(day=scan_day, month=scan_month, year=scan_year, scan_break=0)
                        scan_day_week = self._get_prev_day_week(day=scan_day_week)
                        energy_last_7_days_attr[weekday_text.format(scan_year, calendar.month_abbr[scan_month], scan_day, calendar.day_abbr[scan_day_week])] = value
                        energy_last_7_days += value
                if item['p'] == 3:
                    energy_this_month_attr[month_text.format(this_year, calendar.month_abbr[this_month], this_day)] = energy_today
                    energy_this_month += energy_today
                    for value in reversed(item['v']):
                        scan_day, scan_month, scan_year, scan_break = self._get_prev_day(day=scan_day, month=scan_month, year=scan_year, scan_break=scan_break)
                        if scan_break == 0:
                            energy_this_month_attr[month_text.format(scan_year, calendar.month_abbr[scan_month], scan_day)] = value
                            energy_this_month += value
                        elif scan_break == 1:
                            energy_last_month_attr[month_text.format(scan_year, calendar.month_abbr[scan_month], scan_day)] = value
                            energy_last_month += value
                if item['p'] == 4:
                    energy_this_year_attr[year_text.format(this_year, calendar.month_abbr[this_month])] = energy_this_month
                    energy_this_year += energy_this_month
                    for value in reversed(item['v']):
                        scan_month, scan_year, scan_break = self._get_prev_month(month=scan_month, year=scan_year, scan_break=scan_break)
                        if scan_break == 0:
                            energy_this_year_attr[year_text.format(scan_year, calendar.month_abbr[scan_month])] = value
                            energy_this_year += value
                        elif scan_break == 1:
                            energy_last_year_attr[year_text.format(scan_year, calendar.month_abbr[scan_month])] = value
                            energy_last_year += value
        if not found_key:
            energy_today = None
            energy_yesterday = None
            energy_last_7_days = None
            energy_this_month = None
            energy_last_month = None
            energy_this_year = None
            energy_last_year = None
        return (
            energy_today,
            energy_yesterday,
            energy_last_7_days,
            energy_this_month,
            energy_last_month,
            energy_this_year,
            energy_last_year,
            energy_today_attr,
            energy_yesterday_attr,
            energy_last_7_days_attr,
            energy_this_month_attr,
            energy_last_month_attr,
            energy_this_year_attr,
            energy_last_year_attr,
            found_key
        )


    def _get_prev_month(self, month, year, scan_break):
        if month > 1:
            return month - 1, year, scan_break
        else:
            return 12, year - 1, scan_break + 1


    def _get_prev_day(self, day, month, year, scan_break):
        if day > 1:
            return day - 1, month, year, scan_break
        else:
            if month > 1:
                return calendar.monthrange(year=year, month=month - 1)[1], month - 1, year, scan_break + 1
            else:
                return calendar.monthrange(year=year, month=12)[1], 12, year - 1, scan_break + 1


    def _get_prev_day_week(self, day):
        if day > 0:
            return day - 1
        else:
            return 6


    def _get_prev_hour(self, hour, scan_break):
        if hour > 0:
            return hour - 2, scan_break
        else:
            return 22, scan_break + 1


    def _get_http_data(self, request_type=""):
        """Common fetching of http data"""
        self._login_session()
        if self._login and self._plant_id != "":

            if request_type == self._REQUEST_MAIN:

                request_data = {
                    "useCache": False,
                    "items": [],
                    "features": self._features
                    }
                for param in self._MAP_ARISTON_ZONE_0_PARAMS.values():
                    request_data['items'].append({"id": param, "zn":0})
                if self._zones:
                    for zone in self._zones:
                        for param in self._MAP_ARISTON_MULTIZONE_PARAMS.values():
                            request_data['items'].append({"id": param, "zn":zone})
                with self._data_lock:
                    resp = self._request_post(
                        url=f'{self._ARISTON_URL}/api/v2/remote/dataItems/{self._plant_id}/get?umsys=si',
                        json_data=request_data,
                        timeout=self._TIMEOUT_MAX,
                        error_msg="Main read"
                    )
                    self._store_data(resp, request_type)

            elif request_type == self._REQUEST_ERRORS:

                with self._data_lock:
                    resp = self._request_get(
                        url=f'{self._ARISTON_URL}/api/v2/busErrors?gatewayId={self._plant_id}&blockingOnly=False&culture=en-US',
                        timeout=self._TIMEOUT_AV,
                        error_msg="Errors read"
                    )
                    self._store_data(resp, request_type)

            elif request_type == self._REQUEST_CH_SCHEDULE:

                with self._data_lock:
                    resp = self._request_get(
                        url=f'{self._ARISTON_URL}/api/v2/remote/timeProgs/{self._plant_id}/ChZn1?umsys=si',
                        timeout=self._TIMEOUT_AV,
                        error_msg="CH Schedule read"
                    )
                    self._store_data(resp, request_type)

            elif request_type == self._REQUEST_DHW_SCHEDULE:

                with self._data_lock:
                    resp = self._request_get(
                        url=f'{self._ARISTON_URL}/api/v2/remote/timeProgs/{self._plant_id}/Dhw?umsys=si',
                        timeout=self._TIMEOUT_AV,
                        error_msg="DHW Schedule read"
                    )
                    self._store_data(resp, request_type)

            elif request_type == self._REQUEST_ADDITIONAL:

                with self._data_lock:
                    resp = self._request_get(
                        url=f'{self._ARISTON_URL}/R2/PlantMenu/Refresh?id={self._plant_id}&paramIds={",".join(self._other_parameters)}',
                        timeout=self._TIMEOUT_AV,
                        error_msg="Additional data read"
                    )
                    self._store_data(resp, request_type)

            elif request_type == self._REQUEST_LAST_MONTH:

                with self._data_lock:
                    resp = self._request_get(
                        url=f'{self._ARISTON_URL}/api/v2/remote/reports/{self._plant_id}/energyAccount',
                        timeout=self._TIMEOUT_AV,
                        error_msg="Last month data read"
                    )
                    self._store_data(resp, request_type)

            elif request_type == self._REQUEST_ENERGY:

                with self._data_lock:
                    resp = self._request_get(
                        url=f'{self._ARISTON_URL}/api/v2/remote/reports/{self._plant_id}/consSequencesApi8?usages=Ch%2CDhw&hasSlp=False',
                        timeout=self._TIMEOUT_AV,
                        error_msg="Energy data read"
                    )
                    self._store_data(resp, request_type)

        else:
            self._LOGGER.warning(f"Not properly logged in to read {request_type}")
            raise Exception(f"Not properly logged in to read {request_type}")
        self._LOGGER.info(f'Data read for {request_type}')
        return True


    def _queue_get_data(self):
        """Queue all request items"""
        with self._data_lock:
            # schedule next get request
            if self._errors >= self._MAX_ERRORS:
                # give a little rest to the system if too many errors
                retry_in = self._get_period_time * self._WAIT_PERIOD_MULTIPLYER
            else:
                # work as usual
                retry_in = self._get_period_time
            self._timer_periodic_read.cancel()
            if not self.available or self._errors > 0:
                # Initial or error situation, use main request
                if self.available and self._last_request == self._REQUEST_ADDITIONAL and self._last_request in self._requests_lists[0]:
                    # Potential error with parameters where they are removed 1 by 1 request
                    request_to_send = self._last_request
                else:
                    request_to_send = self._requests_lists[0][0]
            else:
                if self._set_requests[self._REQUEST_MAIN]:
                    # Changing parameters
                    request_to_send = self._REQUEST_MAIN
                elif self._set_requests[self._REQUEST_ADDITIONAL]:
                    # Changing parameters
                    request_to_send = self._REQUEST_ADDITIONAL
                elif self._last_request in self._requests_lists[0]:
                    # High prio more frequent (e.g. current temperatures, flame, errors)
                    last_index = self._requests_lists[0].index(self._last_request)
                    if len(self._requests_lists[0]) <= last_index + 1:
                        # Last request was the last item
                        if self._requests_lists[1]:
                            # There are requests
                            last_index_low_prio = self._requests_lists[1].index(self._last_request_low_prio)
                            if len(self._requests_lists[1]) <= last_index_low_prio + 1:
                                # Last request in low prio item
                                request_to_send = self._requests_lists[1][0]
                            else:
                                request_to_send = self._requests_lists[1][last_index_low_prio + 1]
                            self._last_request_low_prio = request_to_send
                        else:
                            # No low prio requests
                            request_to_send = self._requests_lists[0][0]
                    else:
                        request_to_send = self._requests_lists[0][last_index + 1]
                else:
                    # Low prio less frequent requests (e.g. energy use)
                    request_to_send = self._requests_lists[0][0]
            self._last_request = request_to_send

            if self._started:
                self._LOGGER.info(f'Shall send next request in {retry_in} seconds, current request is {request_to_send}')
                self._timer_queue_delay = threading.Timer(self._TIME_SPLIT, self._control_availability_state, [request_to_send])
                self._timer_queue_delay.start()
                self._timer_periodic_read = threading.Timer(retry_in, self._queue_get_data)
                self._timer_periodic_read.start()
                

    def _error_detected(self):
        """Error detected"""
        with self._lock:
            was_online = self.available
            self._errors += 1
            self._subscribers_statuses_inform()
            self._LOGGER.warning(f"Connection errors: {self._errors}")
            offline = not self.available
        if offline and was_online:
            self._clear_data()
            self._LOGGER.error("Ariston is offline: Too many errors")


    def _no_error_detected(self):
        """No errors detected"""
        with self._lock:
            was_offline = not self.available
            self._errors = 0
            self._subscribers_statuses_inform()
        if was_offline:
            self._LOGGER.info("No more errors")


    def _control_availability_state(self, request_type=""):
        """Control component availability"""
        try:
            result_ok = self._get_http_data(request_type)
            self._LOGGER.info(f"ariston action ok for {request_type}")
        except Exception as ex:
            self._error_detected()
            self._LOGGER.warning(f"ariston action nok for {request_type}: {ex}")
            return
        if result_ok:
            self._no_error_detected()
        return


    def _preparing_setting_http_data(self):
        """Preparing and setting http data"""
        self._login_session()
        with self._data_lock:
            if self._available and self._set_param:

                set_additional_params = []
                parameters = [key for key in self._set_param.keys()]

                for parameter in parameters:

                    try:

                        original_parameter, zone = self._zone_sensor_split(parameter)
                        set_value = self._set_param[parameter][self._SET_VALUE]
                        self._LOGGER.info(f'Setting {parameter} new value {self._set_param[parameter][self._VALUE]} [{set_value}]')
                        
                        if original_parameter == self._PARAM_MODE:

                            old_value = self._string_option_to_number(parameter, self._get_sensor_value(parameter))
                            self._request_post(
                                url=f'{self._ARISTON_URL}/api/v2/remote/plantData/{self._plant_id}/mode',
                                json_data={"new": set_value,"old": old_value},
                                error_msg='Set Mode',
                                timeout=self._TIMEOUT_AV
                            )
                            break

                        elif original_parameter == self._PARAM_CH_MODE:

                            old_value = self._string_option_to_number(parameter, self._get_sensor_value(parameter))
                            self._request_post(
                                url=f'{self._ARISTON_URL}/api/v2/remote/zones/{self._plant_id}/{zone}/mode',
                                json_data={"new": set_value,"old": old_value},
                                error_msg='Set CH Mode',
                                timeout=self._TIMEOUT_AV
                            )
                            break

                        elif original_parameter == self._PARAM_DHW_MODE:

                            old_value = self._string_option_to_number(parameter, self._get_sensor_value(parameter))
                            self._request_post(
                                url=f'{self._ARISTON_URL}/api/v2/remote/plantData/{self._plant_id}/dhwMode',
                                json_data={"new": set_value,"old": old_value},
                                error_msg='Set DHW Mode',
                                timeout=self._TIMEOUT_AV
                            )
                            break

                        elif original_parameter == self._PARAM_CH_SET_TEMPERATURE:
                            
                            comfort_old = self._get_sensor_value(self._zone_sensor_name(self._PARAM_CH_COMFORT_TEMPERATURE, zone))
                            comfort_new = self._ariston_sensors[self._zone_sensor_name(self._PARAM_CH_COMFORT_TEMPERATURE, zone)][self._VALUE]
                            economy_old= self._get_sensor_value(self._zone_sensor_name(self._PARAM_CH_ECONOMY_TEMPERATURE, zone)) 
                            economy_new = self._ariston_sensors[self._zone_sensor_name(self._PARAM_CH_ECONOMY_TEMPERATURE, zone)][self._VALUE]
                            set_temp = self._get_sensor_value(self._zone_sensor_name(self._PARAM_CH_SET_TEMPERATURE, zone))
                            if set_temp == economy_old and self._get_sensor_value(self._PARAM_CH_MODE) == "Time program":
                                economy_new = set_value
                            else:
                                comfort_new = set_value
                            self._request_post(
                                url=f'{self._ARISTON_URL}/api/v2/remote/zones/{self._plant_id}/{zone}/temperatures?umsys=si',
                                json_data={"new":{"comf": comfort_new, "econ": economy_new}, "old":{"comf": comfort_old, "econ": economy_old}},
                                error_msg='Set CH Temperature',
                                timeout=self._TIMEOUT_AV
                            )
                            break

                        elif original_parameter == self._PARAM_CH_COMFORT_TEMPERATURE:
                            
                            comfort_old = self._get_sensor_value(self._zone_sensor_name(self._PARAM_CH_COMFORT_TEMPERATURE, zone))
                            economy_old= self._get_sensor_value(self._zone_sensor_name(self._PARAM_CH_ECONOMY_TEMPERATURE, zone)) 
                            economy_new = self._ariston_sensors[self._zone_sensor_name(self._PARAM_CH_ECONOMY_TEMPERATURE, zone)][self._VALUE]
                            self._request_post(
                                url=f'{self._ARISTON_URL}/api/v2/remote/zones/{self._plant_id}/{zone}/temperatures?umsys=si',
                                json_data={"new":{"comf": set_value, "econ": economy_new}, "old":{"comf": comfort_old, "econ": economy_old}},
                                error_msg='Set CH Temperature',
                                timeout=self._TIMEOUT_AV
                            )
                            break

                        elif original_parameter == self._PARAM_CH_ECONOMY_TEMPERATURE:
                            
                            comfort_old = self._get_sensor_value(self._zone_sensor_name(self._PARAM_CH_COMFORT_TEMPERATURE, zone))
                            comfort_new = self._ariston_sensors[self._zone_sensor_name(self._PARAM_CH_COMFORT_TEMPERATURE, zone)][self._VALUE]
                            economy_old= self._get_sensor_value(self._zone_sensor_name(self._PARAM_CH_ECONOMY_TEMPERATURE, zone)) 
                            self._request_post(
                                url=f'{self._ARISTON_URL}/api/v2/remote/zones/{self._plant_id}/{zone}/temperatures?umsys=si',
                                json_data={"new":{"comf": comfort_new, "econ": set_value}, "old":{"comf": comfort_old, "econ": economy_old}},
                                error_msg='Set CH Temperature',
                                timeout=self._TIMEOUT_AV
                            )
                            break

                        elif original_parameter == self._PARAM_DHW_SET_TEMPERATURE:

                            old_value = self._get_sensor_value(parameter) 
                            self._request_post(
                                url=f'{self._ARISTON_URL}/api/v2/remote/plantData/{self._plant_id}/dhwTemp?umsys=si',
                                json_data={"new": set_value,"old": old_value},
                                error_msg='Set DHW Temperature',
                                timeout=self._TIMEOUT_AV
                            )
                            break

                        elif original_parameter == self._PARAM_DHW_COMFORT_TEMPERATURE:

                            comfort_old = self._get_sensor_value(self._PARAM_DHW_COMFORT_TEMPERATURE) 
                            economy_old= self._get_sensor_value(self._PARAM_DHW_ECONOMY_TEMPERATURE) 
                            economy_new = self._ariston_sensors[self._PARAM_DHW_ECONOMY_TEMPERATURE][self._VALUE]
                            self._request_post(
                                url=f'{self._ARISTON_URL}/api/v2/remote/plantData/{self._plant_id}/dhwTimeProgTemperatures?umsys=si',
                                json_data={"new":{"comf": set_value, "econ": economy_new}, "old":{"comf": comfort_old, "econ": economy_old}},
                                error_msg='Set DHW Comfort Temperature',
                                timeout=self._TIMEOUT_AV
                            )
                            break

                        elif original_parameter == self._PARAM_DHW_ECONOMY_TEMPERATURE:

                            comfort_old = self._get_sensor_value(self._PARAM_DHW_COMFORT_TEMPERATURE)
                            comfort_new = self._ariston_sensors[self._PARAM_DHW_COMFORT_TEMPERATURE][self._VALUE]
                            economy_old= self._get_sensor_value(self._PARAM_DHW_ECONOMY_TEMPERATURE) 
                            self._request_post(
                                url=f'{self._ARISTON_URL}/api/v2/remote/plantData/{self._plant_id}/dhwTimeProgTemperatures?umsys=si',
                                json_data={"new":{"comf": comfort_new, "econ": set_value}, "old":{"comf": comfort_old, "econ": economy_old}},
                                error_msg='Set DHW Economy Temperature',
                                timeout=self._TIMEOUT_AV
                            )
                            break

                        elif original_parameter in self._LIST_ARISTON_WEB_PARAMS:

                            # Many parameters in one request
                            
                            set_additional_params.append(
                                {
                                    "id": self._MAP_ARISTON_WEB_MENU_PARAMS[parameter],
                                    "value": set_value,
                                    "prevValue": self._string_option_to_number(parameter, self._get_sensor_value(parameter))
                                }
                            )

                        else:
                            self._LOGGER.error(f"Unsupported parameter to set {parameter}")
                            raise Exception(f"Unsupported parameter to set {parameter}")

                    except Exception as ex:
                        self._LOGGER.warning(f"Problem setting {parameter}: {ex}")
                        del self._set_param[parameter]
                        continue

                    self._set_param[parameter][self._ATTEMPT] += 1
                    if self._set_param[parameter][self._ATTEMPT] > self._max_set_retries:
                        del self._set_param[parameter]

                else:
                    try:
                        if set_additional_params:
                            self._request_post(
                                url=f'{self._ARISTON_URL}/R2/PlantMenu/Submit/{self._plant_id}',
                                json_data=set_additional_params,
                                error_msg='Set additional parameters',
                                timeout=self._TIMEOUT_AV
                            )
                    except Exception as ex:
                        self._LOGGER.warning(f"Problem setting multiple parameters: {ex}")

                self._subscribers_sensors_inform()
                self._subscribers_statuses_inform()
                self._reset_set_requests()

                if self._set_param:
                    self._timer_set_delay.cancel()
                    if self._started:
                        self._LOGGER.info(f"Attempting to set parameter values in {self._set_period_time} seconds")
                        self._timer_set_delay = threading.Timer(self._set_period_time, self._preparing_setting_http_data)
                        self._timer_set_delay.start()
                

    def _reset_set_requests(self):
        self._set_requests = {request: False for request in self._MAP_REQUEST}
        for parameter in self._set_param:
            self._set_requests[self._get_request_for_parameter(parameter)] = True


    def _is_digit_string(self, text):
        try:
            value = float(text)
            return value
        except ValueError:
            return None


    def _string_option_to_number(self, sensor, value):
        if self._ariston_sensors[sensor][self._OPTIONS_TXT]:
            index = self._ariston_sensors[sensor][self._OPTIONS_TXT].index(value)
            return self._ariston_sensors[sensor][self._OPTIONS][index]
        return self._ariston_sensors[sensor][self._VALUE]


    def set_http_data(self, **parameter_list: Union[str, int, float, bool]) -> None:
        """
        Set data over http, where **parameter_list excepts parameters and wanted values.

        Supported parameters and their values are specified in supported_sensors_set_values method

        Supported values must be viewed in the property 'supported_sensors_set_values',
        which are generated dynamically based on reported values.

        Example:
            set_http_data(mode='OFF',internet_time="ON")
        """

        if self._main_data != {}:
            with self._data_lock:
                # First check values and pre-process the value
                bad_values = {}
                for parameter, value in parameter_list.items():
                    if parameter not in self._SENSOR_SET_LIST:
                        bad_values[parameter] = value
                        continue
                    if self._ariston_sensors[parameter][self._OPTIONS_TXT] != None:
                        if value in self._ariston_sensors[parameter][self._OPTIONS_TXT]:
                            set_value = self._string_option_to_number(parameter, value)
                            if value != self._ariston_sensors[parameter][self._VALUE]:
                                self._set_param[parameter] = {self._VALUE: value, self._SET_VALUE: set_value, self._ATTEMPT: 0}
                                self._ariston_sensors[parameter][self._VALUE] = value
                        else:
                            bad_values[parameter] = value
                    if self._is_digit_string(value) != None:
                        value = self._is_digit_string(value)
                        if self._ariston_sensors[parameter][self._MIN] != None and \
                            self._ariston_sensors[parameter][self._MAX] != None and \
                            self._ariston_sensors[parameter][self._STEP] != None and \
                            value >= self._ariston_sensors[parameter][self._MIN] and \
                            value <= self._ariston_sensors[parameter][self._MAX]:
                            if self._ariston_sensors[parameter][self._STEP] == 0.5:
                                value = round(value * 2.0) / 2.0
                            else:
                                value = round(value)
                            if value != self._ariston_sensors[parameter][self._VALUE]:
                                self._set_param[parameter] = {self._VALUE: value, self._SET_VALUE: value, self._ATTEMPT: 0}
                                self._ariston_sensors[parameter][self._VALUE] = value
                        else:
                            bad_values[parameter] = value

                self._timer_set_delay.cancel()
                if self._started:
                    self._timer_set_delay = threading.Timer(self._TIME_SPLIT, self._preparing_setting_http_data)
                    self._timer_set_delay.start()

                if bad_values:
                    self._LOGGER.error(f"Unsupported parameters to be set: {bad_values}")
                    raise Exception(f"Unsupported parameters to be set: {bad_values}")

        else:
            self._LOGGER.warning("Connection data error, problem to set data")
            raise Exception("Connection data error, problem to set data")

    def _clear_data(self):
        with self._plant_id_lock:
            self._login = False
        self._features = {}
        self._main_data = {}
        self._additional_data = {}
        self._error_data = {}
        self._ch_schedule_data = {}
        self._dhw_schedule_data = {}
        self._set_param = {}
        self._last_month_data = {}
        self._energy_use_data = {}
        self._last_dhw_storage_temp = None
        self._zones = []
        for sensor in self._ariston_sensors:
            self._reset_sensor(sensor)
        self._reset_set_requests()
        self._subscribers_sensors_inform()
        self._subscribers_statuses_inform()

    def start(self) -> None:
        """Start communication with the server."""
        self._started = True
        self._LOGGER.info("Connection started")
        self._timer_periodic_read = threading.Timer(self._TIME_SPLIT, self._queue_get_data)
        self._timer_periodic_read.start()


    def stop(self) -> None:
        """Stop communication with the server."""
        self._started = False
        self._timer_periodic_read.cancel()
        self._timer_queue_delay.cancel()

        if self._login and self.available:
            self._request_get(
                url=f'{self._ARISTON_URL}/R2/Account/Logout',
                error_msg="Logout",
                ignore_errors=True
            )
        self._session.close()
        self._clear_data()
        self._subscribers_statuses_inform()
        self._LOGGER.info("Connection stopped")
