"""Suppoort for Ariston sensors."""
import logging
from datetime import timedelta
from copy import deepcopy

from homeassistant.const import CONF_NAME, CONF_SENSORS
from homeassistant.helpers.entity import Entity
from homeassistant.const import (
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_CURRENT,
    DEVICE_CLASS_ENERGY,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_ILLUMINANCE,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_POWER_FACTOR,
    DEVICE_CLASS_PRESSURE,
    DEVICE_CLASS_SIGNAL_STRENGTH,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_TIMESTAMP,
    DEVICE_CLASS_VOLTAGE,
    ENERGY_KILO_WATT_HOUR
)

from homeassistant.components.sensor import (
    STATE_CLASS_TOTAL_INCREASING
)

from .const import (
    DATA_ARISTON,
    DEVICES,
    PARAM_ACCOUNT_CH_GAS,
    PARAM_ACCOUNT_CH_ELECTRICITY,
    PARAM_ACCOUNT_DHW_GAS,
    PARAM_ACCOUNT_DHW_ELECTRICITY,
    PARAM_CH_ANTIFREEZE_TEMPERATURE,
    PARAM_CH_MODE,
    PARAM_CH_SET_TEMPERATURE,
    PARAM_CH_COMFORT_TEMPERATURE,
    PARAM_CH_ECONOMY_TEMPERATURE,
    PARAM_CH_DETECTED_TEMPERATURE,
    PARAM_CH_PROGRAM,
    PARAM_CH_WATER_TEMPERATURE,
    PARAM_COOLING_LAST_24H,
    PARAM_COOLING_LAST_7D,
    PARAM_COOLING_LAST_30D,
    PARAM_COOLING_LAST_365D,
    PARAM_COOLING_TODAY,
    PARAM_ERRORS,
    PARAM_ERRORS_COUNT,
    PARAM_DHW_COMFORT_FUNCTION,
    PARAM_DHW_MODE,
    PARAM_DHW_SET_TEMPERATURE,
    PARAM_DHW_STORAGE_TEMPERATURE,
    PARAM_DHW_COMFORT_TEMPERATURE,
    PARAM_DHW_ECONOMY_TEMPERATURE,
    PARAM_MODE,
    PARAM_OUTSIDE_TEMPERATURE,
    PARAM_HEATING_LAST_24H,
    PARAM_HEATING_LAST_7D,
    PARAM_HEATING_LAST_30D,
    PARAM_HEATING_LAST_365D,
    PARAM_HEATING_TODAY,
    PARAM_SIGNAL_STRENGTH,
    PARAM_WATER_LAST_24H,
    PARAM_WATER_LAST_7D,
    PARAM_WATER_LAST_30D,
    PARAM_WATER_LAST_365D,
    PARAM_WATER_TODAY,
    PARAM_UNITS,
    PARAM_THERMAL_CLEANSE_CYCLE,
    PARAM_DHW_PROGRAM,
    PARAM_GAS_TYPE,
    PARAM_GAS_COST,
    PARAM_ELECTRICITY_COST,
    PARAM_CH_FLOW_TEMP,
    PARAM_PRESSURE,
    PARAM_CH_FIXED_TEMP,
    VALUE,
    UNITS,
    ZONE_PARAMETERS,
    ZONE_TEMPLATE, 
    ZONE_NAME_TEMPLATE
)

SCAN_INTERVAL = timedelta(seconds=2)

STATE_AVAILABLE = "available"

SENSOR_ACCOUNT_CH_GAS = "Account CH Gas Use"
SENSOR_ACCOUNT_CH_ELECTRICITY = "Account CH Electricity Use"
SENSOR_ACCOUNT_DHW_GAS = "Account DHW Gas Use"
SENSOR_ACCOUNT_DHW_ELECTRICITY = "Account DHW Electricity Use"
SENSOR_CH_ANTIFREEZE_TEMPERATURE = "CH Antifreeze Temperature"
SENSOR_CH_DETECTED_TEMPERATURE = "CH Detected Temperature"
SENSOR_CH_MODE = "CH Mode"
SENSOR_CH_SET_TEMPERATURE = "CH Set Temperature"
SENSOR_CH_PROGRAM = "CH Time Program"
SENSOR_CH_COMFORT_TEMPERATURE = "CH Comfort Temperature"
SENSOR_CH_ECONOMY_TEMPERATURE = "CH Economy Temperature"
SENSOR_CH_WATER_TEMPERATURE = "CH Water Temperature"
SENSOR_CH_FLOW_SETPOINT_TEMPERATURE = "CH Flow Setpoint Temperature"
SENSOR_CH_FIXED_TEMPERATURE = "CH Fixed Temperature"
SENSOR_COOLING_LAST_24H = "Energy use for Cooling in last 24 hours"
SENSOR_COOLING_LAST_7D = "Energy use for Cooling in last 7 days"
SENSOR_COOLING_LAST_30D = "Energy use for Cooling in last 30 days"
SENSOR_COOLING_LAST_365D = "Energy use for Cooling in last 365 days"
SENSOR_DHW_COMFORT_FUNCTION = "DHW Comfort Function"
SENSOR_DHW_PROGRAM = "DHW Time Program"
SENSOR_DHW_SET_TEMPERATURE = "DHW Set Temperature"
SENSOR_DHW_STORAGE_TEMPERATURE = "DHW Storage Temperature"
SENSOR_DHW_COMFORT_TEMPERATURE = "DHW Comfort Temperature"
SENSOR_DHW_ECONOMY_TEMPERATURE = "DHW Economy Temperature"
SENSOR_DHW_MODE = "DHW Mode"
SENSOR_ERRORS = "Active Errors"
SENSOR_HEATING_LAST_24H = "Energy use for Heating in last 24 hours"
SENSOR_HEATING_LAST_7D = "Energy use for Heating in last 7 days"
SENSOR_HEATING_LAST_30D = "Energy use for Heating in last 30 days"
SENSOR_HEATING_LAST_365D = "Energy use for Heating in last 365 days"
SENSOR_MODE = "Mode"
SENSOR_OUTSIDE_TEMPERATURE = "Outside Temperature"
SENSOR_SIGNAL_STRENGTH = "Signal Strength"
SENSOR_WATER_LAST_24H = "Energy use for Water in last 24 hours"
SENSOR_WATER_LAST_7D = "Energy use for Water in last 7 days"
SENSOR_WATER_LAST_30D = "Energy use for Water in last 30 days"
SENSOR_WATER_LAST_365D = "Energy use for Water in last 365 days"
SENSOR_UNITS = "Units of Measurement"
SENSOR_THERMAL_CLEANSE_CYCLE = "Thermal Cleanse Cycle"
SENSOR_GAS_TYPE = "Gas Type"
SENSOR_GAS_COST = "Gas Cost"
SENSOR_ELECTRICITY_COST = "Electricity Cost"
SENSOR_COOLING_TODAY = "Energy use for Cooling today"
SENSOR_HETING_TODAY = "Energy use for Heating today"
SENSOR_WATER_TODAY = "Energy use for Water today"
SENSOR_PRESSURE = "Water Pressure"

_LOGGER = logging.getLogger(__name__)

# Sensor types are defined like: Name, units, icon
SENSORS = {
    PARAM_ACCOUNT_CH_GAS: [SENSOR_ACCOUNT_CH_GAS, None, "mdi:cash", None],
    PARAM_ACCOUNT_DHW_GAS: [SENSOR_ACCOUNT_DHW_GAS, None, "mdi:cash", None],
    PARAM_ACCOUNT_CH_ELECTRICITY: [SENSOR_ACCOUNT_CH_ELECTRICITY, None, "mdi:cash", None],
    PARAM_ACCOUNT_DHW_ELECTRICITY: [SENSOR_ACCOUNT_DHW_ELECTRICITY, None, "mdi:cash", None],
    PARAM_CH_ANTIFREEZE_TEMPERATURE: [SENSOR_CH_ANTIFREEZE_TEMPERATURE, DEVICE_CLASS_TEMPERATURE, "mdi:radiator", None],
    PARAM_CH_DETECTED_TEMPERATURE: [SENSOR_CH_DETECTED_TEMPERATURE, DEVICE_CLASS_TEMPERATURE, "mdi:thermometer", None],
    PARAM_CH_MODE: [SENSOR_CH_MODE, None, "mdi:radiator", None],
    PARAM_CH_SET_TEMPERATURE: [SENSOR_CH_SET_TEMPERATURE, DEVICE_CLASS_TEMPERATURE, "mdi:radiator", None],
    PARAM_CH_PROGRAM: [SENSOR_CH_PROGRAM, None, "mdi:calendar-month", None],
    PARAM_CH_COMFORT_TEMPERATURE: [SENSOR_CH_COMFORT_TEMPERATURE, DEVICE_CLASS_TEMPERATURE, "mdi:radiator", None],
    PARAM_CH_ECONOMY_TEMPERATURE: [SENSOR_CH_ECONOMY_TEMPERATURE, DEVICE_CLASS_TEMPERATURE, "mdi:radiator", None],
    PARAM_CH_WATER_TEMPERATURE: [SENSOR_CH_WATER_TEMPERATURE, DEVICE_CLASS_TEMPERATURE, "mdi:radiator", None],
    PARAM_CH_FLOW_TEMP: [SENSOR_CH_FLOW_SETPOINT_TEMPERATURE, DEVICE_CLASS_TEMPERATURE, "mdi:radiator", None],
    PARAM_CH_FIXED_TEMP: [SENSOR_CH_FIXED_TEMPERATURE, DEVICE_CLASS_TEMPERATURE, "mdi:radiator", None],
    PARAM_COOLING_LAST_24H: [SENSOR_COOLING_LAST_24H, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_COOLING_LAST_7D: [SENSOR_COOLING_LAST_7D, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_COOLING_LAST_30D: [SENSOR_COOLING_LAST_30D, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_COOLING_LAST_365D: [SENSOR_COOLING_LAST_365D, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_DHW_PROGRAM: [SENSOR_DHW_PROGRAM, None, "mdi:calendar-month", None],
    PARAM_DHW_COMFORT_FUNCTION: [SENSOR_DHW_COMFORT_FUNCTION, None, "mdi:water-pump", None],
    PARAM_DHW_SET_TEMPERATURE: [SENSOR_DHW_SET_TEMPERATURE, DEVICE_CLASS_TEMPERATURE, "mdi:water-pump", None],
    PARAM_DHW_STORAGE_TEMPERATURE: [SENSOR_DHW_STORAGE_TEMPERATURE, DEVICE_CLASS_TEMPERATURE, "mdi:water-pump", None],
    PARAM_DHW_COMFORT_TEMPERATURE: [SENSOR_DHW_COMFORT_TEMPERATURE, DEVICE_CLASS_TEMPERATURE, "mdi:water-pump", None],
    PARAM_DHW_ECONOMY_TEMPERATURE: [SENSOR_DHW_ECONOMY_TEMPERATURE, DEVICE_CLASS_TEMPERATURE, "mdi:water-pump", None],
    PARAM_DHW_MODE: [SENSOR_DHW_MODE, None, "mdi:water-pump", None],
    PARAM_ERRORS_COUNT: [SENSOR_ERRORS, None, "mdi:alert-outline", None],
    PARAM_HEATING_LAST_24H: [SENSOR_HEATING_LAST_24H, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_HEATING_LAST_7D: [SENSOR_HEATING_LAST_7D, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_HEATING_LAST_30D: [SENSOR_HEATING_LAST_30D, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_HEATING_LAST_365D: [SENSOR_HEATING_LAST_365D, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_MODE: [SENSOR_MODE, None, "mdi:water-boiler", None],
    PARAM_OUTSIDE_TEMPERATURE: [SENSOR_OUTSIDE_TEMPERATURE, DEVICE_CLASS_TEMPERATURE, "mdi:thermometer", None],
    PARAM_SIGNAL_STRENGTH: [SENSOR_SIGNAL_STRENGTH, DEVICE_CLASS_SIGNAL_STRENGTH, "mdi:signal", None],
    PARAM_WATER_LAST_24H: [SENSOR_WATER_LAST_24H, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_WATER_LAST_7D: [SENSOR_WATER_LAST_7D, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_WATER_LAST_30D: [SENSOR_WATER_LAST_30D, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_WATER_LAST_365D: [SENSOR_WATER_LAST_365D, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_UNITS: [SENSOR_UNITS, None, "mdi:scale-balance", None],
    PARAM_THERMAL_CLEANSE_CYCLE: [SENSOR_THERMAL_CLEANSE_CYCLE, None, "mdi:update", None],
    PARAM_GAS_TYPE: [SENSOR_GAS_TYPE, None, "mdi:gas-cylinder", None],
    PARAM_GAS_COST: [SENSOR_GAS_COST, None, "mdi:cash", None],
    PARAM_ELECTRICITY_COST: [SENSOR_ELECTRICITY_COST, None, "mdi:cash", None],
    PARAM_COOLING_TODAY: [SENSOR_COOLING_TODAY, DEVICE_CLASS_ENERGY, "mdi:cash", STATE_CLASS_TOTAL_INCREASING],
    PARAM_HEATING_TODAY: [SENSOR_HETING_TODAY, DEVICE_CLASS_ENERGY, "mdi:cash", STATE_CLASS_TOTAL_INCREASING],
    PARAM_WATER_TODAY: [SENSOR_WATER_TODAY, DEVICE_CLASS_ENERGY, "mdi:cash", STATE_CLASS_TOTAL_INCREASING],
    PARAM_PRESSURE: [SENSOR_PRESSURE, DEVICE_CLASS_PRESSURE, "mdi:gauge", None],
}
for param in ZONE_PARAMETERS:
    if param in SENSORS:
        for zone in range(2, 4):
            SENSORS[ZONE_TEMPLATE.format(param, zone)] = (
                ZONE_NAME_TEMPLATE.format(SENSORS[param][0], zone),
                SENSORS[param][1],
                SENSORS[param][2],
                SENSORS[param][3]
            )
            

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up a sensor for Ariston."""
    if discovery_info is None:
        return

    name = discovery_info[CONF_NAME]
    device = hass.data[DATA_ARISTON][DEVICES][name]
    add_entities(
        [
            AristonSensor(name, device, sensor_type)
            for sensor_type in discovery_info[CONF_SENSORS]
        ],
        True,
    )


class AristonSensor(Entity):
    """A sensor implementation for Ariston."""

    def __init__(self, name, device, sensor_type):
        """Initialize a sensor for Ariston."""
        self._name = "{} {}".format(name, SENSORS[sensor_type][0])
        self._signal_name = name
        self._api = device.api.ariston_api
        self._sensor_type = sensor_type
        self._state = None
        self._attrs = {}
        self._icon = SENSORS[sensor_type][2]
        self._device_class = SENSORS[sensor_type][1]
        self._state_class = SENSORS[sensor_type][3]

    @property
    def unique_id(self):
        """Return the unique id."""
        return f"{self._name}-{self._sensor_type}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def native_value(self):
        """Return value of sensor."""
        return self._state

    @property
    def state_class(self):
        """State class of sensor."""
        return self._state_class

    @property
    def native_unit_of_measurement(self):
        """Return unit of sensor."""
        try:
            return self._api.sensor_values[self._sensor_type][UNITS]
        except KeyError:
            return None

    @property
    def device_class(self):
        """Return device class."""
        return self._device_class
        
    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attrs

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        if self._sensor_type == PARAM_ERRORS_COUNT:
            try:
                if self._api.sensor_values[PARAM_ERRORS_COUNT][VALUE] == 0:
                    return "mdi:shield"
            except KeyError:
                pass
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return the units of measurement."""
        try:
            return self._api.sensor_values[self._sensor_type][UNITS]
        except KeyError:
            return None

    @property
    def available(self):
        """Return True if entity is available."""
        return (
            self._api.available
            and not self._api.sensor_values[self._sensor_type][VALUE] is None
        )

    def _original_sensor(self, sensor):
        for param in ZONE_PARAMETERS:
            if sensor in {
                ZONE_TEMPLATE.format(param, 2),
                ZONE_TEMPLATE.format(param, 3)
                }:
                return param
        return sensor


    def update(self):
        """Get the latest data and updates the state."""
        try:
            if not self._api.available:
                return
            if not self._api.sensor_values[self._sensor_type][VALUE] is None:
                if self._original_sensor(self._sensor_type) in {PARAM_CH_PROGRAM, PARAM_DHW_PROGRAM}:
                    if self._api.sensor_values[self._sensor_type][VALUE] != {}:
                        self._state = STATE_AVAILABLE
                    else:
                        self._state = None
                else:
                    self._state = self._api.sensor_values[self._sensor_type][VALUE]
            else:
                self._state = None

            self._attrs = {}
            if self._original_sensor(self._sensor_type) in {
                PARAM_CH_SET_TEMPERATURE,
                PARAM_DHW_SET_TEMPERATURE,
                PARAM_CH_WATER_TEMPERATURE
            }:
                try:
                    self._attrs["Min"] = self._api.supported_sensors_set_values[
                        self._sensor_type
                    ]["min"]
                    self._attrs["Max"] = self._api.supported_sensors_set_values[
                        self._sensor_type
                    ]["max"]
                except KeyError:
                    self._attrs["Min"] = None
                    self._attrs["Max"] = None

            elif self._original_sensor(self._sensor_type) in {
                PARAM_ERRORS_COUNT
            }:
                self._attrs = self._api.sensor_values[PARAM_ERRORS][VALUE]

            elif self._original_sensor(self._sensor_type) in {
                PARAM_HEATING_LAST_24H,
                PARAM_WATER_LAST_24H,
                PARAM_COOLING_LAST_24H,
                PARAM_HEATING_LAST_7D,
                PARAM_WATER_LAST_7D,
                PARAM_COOLING_LAST_7D,
                PARAM_HEATING_LAST_30D,
                PARAM_WATER_LAST_30D,
                PARAM_COOLING_LAST_30D,
                PARAM_HEATING_LAST_365D,
                PARAM_WATER_LAST_365D,
                PARAM_COOLING_LAST_365D,
            }:
                list_param = self._sensor_type + "_list"
                self._attrs = self._api.sensor_values[list_param][VALUE]

            elif self._original_sensor(self._sensor_type) in {
                PARAM_CH_PROGRAM,
                PARAM_DHW_PROGRAM
            }:
                if self._state:
                    self._attrs = self._api.sensor_values[self._sensor_type][VALUE]

            elif self._original_sensor(self._sensor_type) in {
                PARAM_WATER_TODAY,
                PARAM_HEATING_TODAY,
                PARAM_COOLING_TODAY
            }:
                self._attrs["state_class"] = self._state_class

        except KeyError:
            _LOGGER.warning("Problem updating sensors for Ariston")
