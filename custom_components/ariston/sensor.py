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
    OPTIONS,
    PARAM_CH_ANTIFREEZE_TEMPERATURE,
    PARAM_CH_MODE,
    PARAM_CH_SET_TEMPERATURE,
    PARAM_CH_COMFORT_TEMPERATURE,
    PARAM_CH_ECONOMY_TEMPERATURE,
    PARAM_CH_DETECTED_TEMPERATURE,
    PARAM_CH_PROGRAM,
    PARAM_CH_WATER_TEMPERATURE,
    PARAM_ERRORS_COUNT,
    PARAM_DHW_COMFORT_FUNCTION,
    PARAM_DHW_MODE,
    PARAM_DHW_SET_TEMPERATURE,
    PARAM_DHW_STORAGE_TEMPERATURE,
    PARAM_DHW_COMFORT_TEMPERATURE,
    PARAM_DHW_ECONOMY_TEMPERATURE,
    PARAM_MODE,
    PARAM_OUTSIDE_TEMPERATURE,
    PARAM_SIGNAL_STRENGTH,
    PARAM_UNITS,
    PARAM_THERMAL_CLEANSE_CYCLE,
    PARAM_DHW_PROGRAM,
    PARAM_CH_FLOW_TEMP,
    PARAM_PRESSURE,
    PARAM_CH_FIXED_TEMP,
    PARAM_CH_LAST_MONTH_ELECTRICITY,
    PARAM_CH_LAST_MONTH_GAS,
    PARAM_DHW_LAST_MONTH_ELECTRICITY,
    PARAM_DHW_LAST_MONTH_GAS,
    PARAM_CH_ENERGY_TODAY,
    PARAM_CH_ENERGY_YESTERDAY,
    PARAM_DHW_ENERGY_TODAY,
    PARAM_DHW_ENERGY_YESTERDAY,
    PARAM_CH_ENERGY_THIS_WEEK,
    PARAM_CH_ENERGY_LAST_WEEK,
    PARAM_DHW_ENERGY_THIS_WEEK,
    PARAM_DHW_ENERGY_LAST_WEEK,
    PARAM_CH_ENERGY_THIS_MONTH,
    PARAM_CH_ENERGY_LAST_MONTH,
    PARAM_DHW_ENERGY_THIS_MONTH,
    PARAM_DHW_ENERGY_LAST_MONTH,
    PARAM_CH_ENERGY_THIS_YEAR,
    PARAM_CH_ENERGY_LAST_YEAR,
    PARAM_DHW_ENERGY_THIS_YEAR,
    PARAM_DHW_ENERGY_LAST_YEAR,
    PARAM_VERSION,
    VALUE,
    UNITS,
    ATTRIBUTES,
    MIN,
    MAX,
    STEP,
    OPTIONS_TXT,
)

SCAN_INTERVAL = timedelta(seconds=2)

STATE_AVAILABLE = "available"

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
SENSOR_DHW_COMFORT_FUNCTION = "DHW Comfort Function"
SENSOR_DHW_PROGRAM = "DHW Time Program"
SENSOR_DHW_SET_TEMPERATURE = "DHW Set Temperature"
SENSOR_DHW_STORAGE_TEMPERATURE = "DHW Storage Temperature"
SENSOR_DHW_COMFORT_TEMPERATURE = "DHW Comfort Temperature"
SENSOR_DHW_ECONOMY_TEMPERATURE = "DHW Economy Temperature"
SENSOR_DHW_MODE = "DHW Mode"
SENSOR_ERRORS = "Active Errors"
SENSOR_MODE = "Mode"
SENSOR_OUTSIDE_TEMPERATURE = "Outside Temperature"
SENSOR_SIGNAL_STRENGTH = "Signal Strength"
SENSOR_UNITS = "Units of Measurement"
SENSOR_THERMAL_CLEANSE_CYCLE = "Thermal Cleanse Cycle"
SENSOR_GAS_TYPE = "Gas Type"
SENSOR_GAS_COST = "Gas Cost"
SENSOR_ELECTRICITY_COST = "Electricity Cost"
SENSOR_PRESSURE = "Water Pressure"
SENSOR_CH_LAST_MONTH_ELECTRICITY = "Electricity use for CH Last Month"
SENSOR_CH_LAST_MONTH_GAS = "Gas use for CH Last Month"
SENSOR_DHW_LAST_MONTH_ELECTRICITY = "Electricity use for DHW Last Month"
SENSOR_DHW_LAST_MONTH_GAS = "Gas use for DHW Last Month"
SENSOR_CH_ENERGY_TODAY = 'CH energy today'
SENSOR_CH_ENERGY_YESTERDAY = 'CH energy yesterday'
SENSOR_DHW_ENERGY_TODAY = 'DHW energy today'
SENSOR_DHW_ENERGY_YESTERDAY = 'DHW energy yesterday'
SENSOR_CH_ENERGY_THIS_WEEK = 'CH energy this week'
SENSOR_CH_ENERGY_LAST_WEEK = 'CH energy last week'
SENSOR_DHW_ENERGY_THIS_WEEK = 'DHW energy this week'
SENSOR_DHW_ENERGY_LAST_WEEK = 'DHW energy last week'
SENSOR_CH_ENERGY_THIS_MONTH = 'CH energy this month'
SENSOR_CH_ENERGY_LAST_MONTH = 'CH energy last month'
SENSOR_DHW_ENERGY_THIS_MONTH = 'DHW energy this month'
SENSOR_DHW_ENERGY_LAST_MONTH = 'DHW energy last month'
SENSOR_CH_ENERGY_THIS_YEAR = 'CH energy this year'
SENSOR_CH_ENERGY_LAST_YEAR = 'CH energy last year'
SENSOR_DHW_ENERGY_THIS_YEAR = 'DHW energy this year'
SENSOR_DHW_ENERGY_LAST_YEAR = 'DHW energy last year'
SENSOR_VERSION = 'Integration local version'

_LOGGER = logging.getLogger(__name__)

# Sensor types are defined like: Name, units, icon
SENSORS = {
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
    PARAM_DHW_PROGRAM: [SENSOR_DHW_PROGRAM, None, "mdi:calendar-month", None],
    PARAM_DHW_COMFORT_FUNCTION: [SENSOR_DHW_COMFORT_FUNCTION, None, "mdi:water-pump", None],
    PARAM_DHW_SET_TEMPERATURE: [SENSOR_DHW_SET_TEMPERATURE, DEVICE_CLASS_TEMPERATURE, "mdi:water-pump", None],
    PARAM_DHW_STORAGE_TEMPERATURE: [SENSOR_DHW_STORAGE_TEMPERATURE, DEVICE_CLASS_TEMPERATURE, "mdi:water-pump", None],
    PARAM_DHW_COMFORT_TEMPERATURE: [SENSOR_DHW_COMFORT_TEMPERATURE, DEVICE_CLASS_TEMPERATURE, "mdi:water-pump", None],
    PARAM_DHW_ECONOMY_TEMPERATURE: [SENSOR_DHW_ECONOMY_TEMPERATURE, DEVICE_CLASS_TEMPERATURE, "mdi:water-pump", None],
    PARAM_DHW_MODE: [SENSOR_DHW_MODE, None, "mdi:water-pump", None],
    PARAM_ERRORS_COUNT: [SENSOR_ERRORS, None, "mdi:alert-outline", None],
    PARAM_MODE: [SENSOR_MODE, None, "mdi:water-boiler", None],
    PARAM_OUTSIDE_TEMPERATURE: [SENSOR_OUTSIDE_TEMPERATURE, DEVICE_CLASS_TEMPERATURE, "mdi:thermometer", None],
    PARAM_SIGNAL_STRENGTH: [SENSOR_SIGNAL_STRENGTH, DEVICE_CLASS_SIGNAL_STRENGTH, "mdi:signal", None],
    PARAM_UNITS: [SENSOR_UNITS, None, "mdi:scale-balance", None],
    PARAM_THERMAL_CLEANSE_CYCLE: [SENSOR_THERMAL_CLEANSE_CYCLE, None, "mdi:update", None],
    PARAM_PRESSURE: [SENSOR_PRESSURE, DEVICE_CLASS_PRESSURE, "mdi:gauge", None],
    PARAM_CH_LAST_MONTH_ELECTRICITY: [SENSOR_CH_LAST_MONTH_ELECTRICITY, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_CH_LAST_MONTH_GAS: [SENSOR_CH_LAST_MONTH_GAS, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_DHW_LAST_MONTH_ELECTRICITY: [SENSOR_DHW_LAST_MONTH_ELECTRICITY, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_DHW_LAST_MONTH_GAS: [SENSOR_DHW_LAST_MONTH_GAS, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_CH_ENERGY_TODAY: [SENSOR_CH_ENERGY_TODAY, DEVICE_CLASS_ENERGY, "mdi:cash", STATE_CLASS_TOTAL_INCREASING],
    PARAM_DHW_ENERGY_TODAY: [SENSOR_DHW_ENERGY_TODAY, DEVICE_CLASS_ENERGY, "mdi:cash", STATE_CLASS_TOTAL_INCREASING],
    PARAM_CH_ENERGY_YESTERDAY: [SENSOR_CH_ENERGY_YESTERDAY, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_DHW_ENERGY_YESTERDAY: [SENSOR_DHW_ENERGY_YESTERDAY, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_CH_ENERGY_THIS_WEEK: [SENSOR_CH_ENERGY_THIS_WEEK, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_CH_ENERGY_LAST_WEEK: [SENSOR_CH_ENERGY_LAST_WEEK, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_DHW_ENERGY_THIS_WEEK: [SENSOR_DHW_ENERGY_THIS_WEEK, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_DHW_ENERGY_LAST_WEEK: [SENSOR_DHW_ENERGY_LAST_WEEK, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_CH_ENERGY_THIS_MONTH: [SENSOR_CH_ENERGY_THIS_MONTH, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_CH_ENERGY_LAST_MONTH: [SENSOR_CH_ENERGY_LAST_MONTH, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_DHW_ENERGY_THIS_MONTH: [SENSOR_DHW_ENERGY_THIS_MONTH, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_DHW_ENERGY_LAST_MONTH: [SENSOR_DHW_ENERGY_LAST_MONTH, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_CH_ENERGY_THIS_YEAR: [SENSOR_CH_ENERGY_THIS_YEAR, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_CH_ENERGY_LAST_YEAR: [SENSOR_CH_ENERGY_LAST_YEAR, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_DHW_ENERGY_THIS_YEAR: [SENSOR_DHW_ENERGY_THIS_YEAR, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_DHW_ENERGY_LAST_YEAR: [SENSOR_DHW_ENERGY_LAST_YEAR, DEVICE_CLASS_ENERGY, "mdi:cash", None],
    PARAM_VERSION: [SENSOR_VERSION, None, "mdi:package-down", None],
}


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
        if self._sensor_type == PARAM_VERSION:
            return True
        return (
            self._api.available
            and not self._api.sensor_values[self._sensor_type][VALUE] is None
        )


    def update(self):
        """Get the latest data and updates the state."""
        try:
            if self._sensor_type == PARAM_VERSION:
                self._state = self._api.version
                return
            if not self._api.available:
                return
            self._state = self._api.sensor_values[self._sensor_type][VALUE]
            self._attrs = self._api.sensor_values[self._sensor_type][ATTRIBUTES]
            if not self._attrs:
                if self._api.sensor_values[self._sensor_type][OPTIONS_TXT]:
                    self._attrs[OPTIONS_TXT] = self._api.sensor_values[self._sensor_type][OPTIONS_TXT]
                    self._attrs[OPTIONS] = self._api.sensor_values[self._sensor_type][OPTIONS]
                elif self._api.sensor_values[self._sensor_type][MIN] and \
                    self._api.sensor_values[self._sensor_type][MAX] and \
                    self._api.sensor_values[self._sensor_type][STEP]:
                    self._attrs[MIN] = self._api.sensor_values[self._sensor_type][MIN]
                    self._attrs[MAX] = self._api.sensor_values[self._sensor_type][MAX]
                    self._attrs[STEP] = self._api.sensor_values[self._sensor_type][STEP]
            if self._state_class:
                self._attrs["state_class"] = self._state_class

        except KeyError:
            _LOGGER.warning("Problem updating sensors for Ariston")
