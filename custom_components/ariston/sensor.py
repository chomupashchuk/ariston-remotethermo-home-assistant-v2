"""Suppoort for Ariston sensors."""
import logging
from datetime import timedelta
from copy import deepcopy

from homeassistant.const import CONF_NAME, CONF_SENSORS
from homeassistant.helpers.entity import Entity
from homeassistant.const import (
    UnitOfEnergy,
)

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)

from .const import param_zoned
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
    PARAM_CH_ENERGY_LAST_7_DAYS,
    PARAM_DHW_ENERGY_LAST_7_DAYS,
    PARAM_CH_ENERGY_THIS_MONTH,
    PARAM_CH_ENERGY_LAST_MONTH,
    PARAM_DHW_ENERGY_THIS_MONTH,
    PARAM_DHW_ENERGY_LAST_MONTH,
    PARAM_CH_ENERGY_THIS_YEAR,
    PARAM_CH_ENERGY_LAST_YEAR,
    PARAM_DHW_ENERGY_THIS_YEAR,
    PARAM_DHW_ENERGY_LAST_YEAR,
    PARAM_CH_ENERGY2_TODAY,
    PARAM_CH_ENERGY2_YESTERDAY,
    PARAM_DHW_ENERGY2_TODAY,
    PARAM_DHW_ENERGY2_YESTERDAY,
    PARAM_CH_ENERGY2_LAST_7_DAYS,
    PARAM_DHW_ENERGY2_LAST_7_DAYS,
    PARAM_CH_ENERGY2_THIS_MONTH,
    PARAM_CH_ENERGY2_LAST_MONTH,
    PARAM_DHW_ENERGY2_THIS_MONTH,
    PARAM_DHW_ENERGY2_LAST_MONTH,
    PARAM_CH_ENERGY2_THIS_YEAR,
    PARAM_CH_ENERGY2_LAST_YEAR,
    PARAM_DHW_ENERGY2_THIS_YEAR,
    PARAM_DHW_ENERGY2_LAST_YEAR,
    PARAM_CH_ENERGY_DELTA_TODAY,
    PARAM_CH_ENERGY_DELTA_YESTERDAY,
    PARAM_DHW_ENERGY_DELTA_TODAY,
    PARAM_DHW_ENERGY_DELTA_YESTERDAY,
    PARAM_CH_ENERGY_DELTA_LAST_7_DAYS,
    PARAM_DHW_ENERGY_DELTA_LAST_7_DAYS,
    PARAM_CH_ENERGY_DELTA_THIS_MONTH,
    PARAM_CH_ENERGY_DELTA_LAST_MONTH,
    PARAM_DHW_ENERGY_DELTA_THIS_MONTH,
    PARAM_DHW_ENERGY_DELTA_LAST_MONTH,
    PARAM_CH_ENERGY_DELTA_THIS_YEAR,
    PARAM_CH_ENERGY_DELTA_LAST_YEAR,
    PARAM_DHW_ENERGY_DELTA_THIS_YEAR,
    PARAM_DHW_ENERGY_DELTA_LAST_YEAR,
    PARAM_VERSION,
    VALUE,
    UNITS,
    ATTRIBUTES,
    MIN,
    MAX,
    STEP,
    OPTIONS_TXT,
    ZONED_PARAMS
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
SENSOR_CH_ENERGY_LAST_7_DAYS = 'CH energy last 7 days'
SENSOR_DHW_ENERGY_LAST_7_DAYS = 'DHW energy last 7 days'
SENSOR_CH_ENERGY_THIS_MONTH = 'CH energy this month'
SENSOR_CH_ENERGY_LAST_MONTH = 'CH energy last month'
SENSOR_DHW_ENERGY_THIS_MONTH = 'DHW energy this month'
SENSOR_DHW_ENERGY_LAST_MONTH = 'DHW energy last month'
SENSOR_CH_ENERGY_THIS_YEAR = 'CH energy this year'
SENSOR_CH_ENERGY_LAST_YEAR = 'CH energy last year'
SENSOR_DHW_ENERGY_THIS_YEAR = 'DHW energy this year'
SENSOR_DHW_ENERGY_LAST_YEAR = 'DHW energy last year'
SENSOR_CH_ENERGY2_TODAY = 'CH energy 2 today'
SENSOR_CH_ENERGY2_YESTERDAY = 'CH energy 2 yesterday'
SENSOR_DHW_ENERGY2_TODAY = 'DHW energy 2 today'
SENSOR_DHW_ENERGY2_YESTERDAY = 'DHW energy 2 yesterday'
SENSOR_CH_ENERGY2_LAST_7_DAYS = 'CH energy 2 last 7 days'
SENSOR_DHW_ENERGY2_LAST_7_DAYS = 'DHW energy 2 last 7 days'
SENSOR_CH_ENERGY2_THIS_MONTH = 'CH energy 2 this month'
SENSOR_CH_ENERGY2_LAST_MONTH = 'CH energy 2 last month'
SENSOR_DHW_ENERGY2_THIS_MONTH = 'DHW energy 2 this month'
SENSOR_DHW_ENERGY2_LAST_MONTH = 'DHW energy 2 last month'
SENSOR_CH_ENERGY2_THIS_YEAR = 'CH energy 2 this year'
SENSOR_CH_ENERGY2_LAST_YEAR = 'CH energy 2 last year'
SENSOR_DHW_ENERGY2_THIS_YEAR = 'DHW energy 2 this year'
SENSOR_DHW_ENERGY2_LAST_YEAR = 'DHW energy 2 last year'
SENSOR_CH_ENERGY_DELTA_TODAY = 'CH energy 2 today'
SENSOR_CH_ENERGY_DELTA_YESTERDAY = 'CH energy 2 yesterday'
SENSOR_DHW_ENERGY_DELTA_TODAY = 'DHW energy 2 today'
SENSOR_DHW_ENERGY_DELTA_YESTERDAY = 'DHW energy 2 yesterday'
SENSOR_CH_ENERGY_DELTA_LAST_7_DAYS = 'CH energy 2 last 7 days'
SENSOR_DHW_ENERGY_DELTA_LAST_7_DAYS = 'DHW energy 2 last 7 days'
SENSOR_CH_ENERGY_DELTA_THIS_MONTH = 'CH energy 2 this month'
SENSOR_CH_ENERGY_DELTA_LAST_MONTH = 'CH energy 2 last month'
SENSOR_DHW_ENERGY_DELTA_THIS_MONTH = 'DHW energy 2 this month'
SENSOR_DHW_ENERGY_DELTA_LAST_MONTH = 'DHW energy 2 last month'
SENSOR_CH_ENERGY_DELTA_THIS_YEAR = 'CH energy 2 this year'
SENSOR_CH_ENERGY_DELTA_LAST_YEAR = 'CH energy 2 last year'
SENSOR_DHW_ENERGY_DELTA_THIS_YEAR = 'DHW energy 2 this year'
SENSOR_DHW_ENERGY_DELTA_LAST_YEAR = 'DHW energy 2 last year'
SENSOR_VERSION = 'Integration local version'

_LOGGER = logging.getLogger(__name__)

# Sensor types are defined like: Name, units, icon
sensors_default = {
    PARAM_CH_ANTIFREEZE_TEMPERATURE: [SENSOR_CH_ANTIFREEZE_TEMPERATURE, SensorDeviceClass.TEMPERATURE, "mdi:radiator", None],
    PARAM_CH_DETECTED_TEMPERATURE: [SENSOR_CH_DETECTED_TEMPERATURE, SensorDeviceClass.TEMPERATURE, "mdi:thermometer", None],
    PARAM_CH_MODE: [SENSOR_CH_MODE, None, "mdi:radiator", None],
    PARAM_CH_SET_TEMPERATURE: [SENSOR_CH_SET_TEMPERATURE, SensorDeviceClass.TEMPERATURE, "mdi:radiator", None],
    PARAM_CH_PROGRAM: [SENSOR_CH_PROGRAM, None, "mdi:calendar-month", None],
    PARAM_CH_COMFORT_TEMPERATURE: [SENSOR_CH_COMFORT_TEMPERATURE, SensorDeviceClass.TEMPERATURE, "mdi:radiator", None],
    PARAM_CH_ECONOMY_TEMPERATURE: [SENSOR_CH_ECONOMY_TEMPERATURE, SensorDeviceClass.TEMPERATURE, "mdi:radiator", None],
    PARAM_CH_WATER_TEMPERATURE: [SENSOR_CH_WATER_TEMPERATURE, SensorDeviceClass.TEMPERATURE, "mdi:radiator", None],
    PARAM_CH_FLOW_TEMP: [SENSOR_CH_FLOW_SETPOINT_TEMPERATURE, SensorDeviceClass.TEMPERATURE, "mdi:radiator", None],
    PARAM_CH_FIXED_TEMP: [SENSOR_CH_FIXED_TEMPERATURE, SensorDeviceClass.TEMPERATURE, "mdi:radiator", None],
    PARAM_DHW_PROGRAM: [SENSOR_DHW_PROGRAM, None, "mdi:calendar-month", None],
    PARAM_DHW_COMFORT_FUNCTION: [SENSOR_DHW_COMFORT_FUNCTION, None, "mdi:water-pump", None],
    PARAM_DHW_SET_TEMPERATURE: [SENSOR_DHW_SET_TEMPERATURE, SensorDeviceClass.TEMPERATURE, "mdi:water-pump", None],
    PARAM_DHW_STORAGE_TEMPERATURE: [SENSOR_DHW_STORAGE_TEMPERATURE, SensorDeviceClass.TEMPERATURE, "mdi:water-pump", None],
    PARAM_DHW_COMFORT_TEMPERATURE: [SENSOR_DHW_COMFORT_TEMPERATURE, SensorDeviceClass.TEMPERATURE, "mdi:water-pump", None],
    PARAM_DHW_ECONOMY_TEMPERATURE: [SENSOR_DHW_ECONOMY_TEMPERATURE, SensorDeviceClass.TEMPERATURE, "mdi:water-pump", None],
    PARAM_DHW_MODE: [SENSOR_DHW_MODE, None, "mdi:water-pump", None],
    PARAM_ERRORS_COUNT: [SENSOR_ERRORS, None, "mdi:alert-outline", None],
    PARAM_MODE: [SENSOR_MODE, None, "mdi:water-boiler", None],
    PARAM_OUTSIDE_TEMPERATURE: [SENSOR_OUTSIDE_TEMPERATURE, SensorDeviceClass.TEMPERATURE, "mdi:thermometer", None],
    PARAM_SIGNAL_STRENGTH: [SENSOR_SIGNAL_STRENGTH, SensorDeviceClass.SIGNAL_STRENGTH, "mdi:signal", None],
    PARAM_UNITS: [SENSOR_UNITS, None, "mdi:scale-balance", None],
    PARAM_THERMAL_CLEANSE_CYCLE: [SENSOR_THERMAL_CLEANSE_CYCLE, None, "mdi:update", None],
    PARAM_PRESSURE: [SENSOR_PRESSURE, SensorDeviceClass.PRESSURE, "mdi:gauge", None],
    PARAM_CH_LAST_MONTH_ELECTRICITY: [SENSOR_CH_LAST_MONTH_ELECTRICITY, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_CH_LAST_MONTH_GAS: [SENSOR_CH_LAST_MONTH_GAS, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_DHW_LAST_MONTH_ELECTRICITY: [SENSOR_DHW_LAST_MONTH_ELECTRICITY, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_DHW_LAST_MONTH_GAS: [SENSOR_DHW_LAST_MONTH_GAS, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_CH_ENERGY_TODAY: [SENSOR_CH_ENERGY_TODAY, SensorDeviceClass.ENERGY, "mdi:cash", SensorStateClass.TOTAL_INCREASING],
    PARAM_DHW_ENERGY_TODAY: [SENSOR_DHW_ENERGY_TODAY, SensorDeviceClass.ENERGY, "mdi:cash", SensorStateClass.TOTAL_INCREASING],
    PARAM_CH_ENERGY_YESTERDAY: [SENSOR_CH_ENERGY_YESTERDAY, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_DHW_ENERGY_YESTERDAY: [SENSOR_DHW_ENERGY_YESTERDAY, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_CH_ENERGY_LAST_7_DAYS: [SENSOR_CH_ENERGY_LAST_7_DAYS, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_DHW_ENERGY_LAST_7_DAYS: [SENSOR_DHW_ENERGY_LAST_7_DAYS, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_CH_ENERGY_THIS_MONTH: [SENSOR_CH_ENERGY_THIS_MONTH, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_CH_ENERGY_LAST_MONTH: [SENSOR_CH_ENERGY_LAST_MONTH, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_DHW_ENERGY_THIS_MONTH: [SENSOR_DHW_ENERGY_THIS_MONTH, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_DHW_ENERGY_LAST_MONTH: [SENSOR_DHW_ENERGY_LAST_MONTH, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_CH_ENERGY_THIS_YEAR: [SENSOR_CH_ENERGY_THIS_YEAR, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_CH_ENERGY_LAST_YEAR: [SENSOR_CH_ENERGY_LAST_YEAR, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_DHW_ENERGY_THIS_YEAR: [SENSOR_DHW_ENERGY_THIS_YEAR, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_DHW_ENERGY_LAST_YEAR: [SENSOR_DHW_ENERGY_LAST_YEAR, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_CH_ENERGY2_TODAY: [SENSOR_CH_ENERGY2_TODAY, SensorDeviceClass.ENERGY, "mdi:cash", SensorStateClass.TOTAL_INCREASING],
    PARAM_DHW_ENERGY2_TODAY: [SENSOR_DHW_ENERGY2_TODAY, SensorDeviceClass.ENERGY, "mdi:cash", SensorStateClass.TOTAL_INCREASING],
    PARAM_CH_ENERGY2_YESTERDAY: [SENSOR_CH_ENERGY2_YESTERDAY, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_DHW_ENERGY2_YESTERDAY: [SENSOR_DHW_ENERGY2_YESTERDAY, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_CH_ENERGY2_LAST_7_DAYS: [SENSOR_CH_ENERGY2_LAST_7_DAYS, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_DHW_ENERGY2_LAST_7_DAYS: [SENSOR_DHW_ENERGY2_LAST_7_DAYS, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_CH_ENERGY2_THIS_MONTH: [SENSOR_CH_ENERGY2_THIS_MONTH, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_CH_ENERGY2_LAST_MONTH: [SENSOR_CH_ENERGY2_LAST_MONTH, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_DHW_ENERGY2_THIS_MONTH: [SENSOR_DHW_ENERGY2_THIS_MONTH, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_DHW_ENERGY2_LAST_MONTH: [SENSOR_DHW_ENERGY2_LAST_MONTH, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_CH_ENERGY2_THIS_YEAR: [SENSOR_CH_ENERGY2_THIS_YEAR, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_CH_ENERGY2_LAST_YEAR: [SENSOR_CH_ENERGY2_LAST_YEAR, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_DHW_ENERGY2_THIS_YEAR: [SENSOR_DHW_ENERGY2_THIS_YEAR, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_DHW_ENERGY2_LAST_YEAR: [SENSOR_DHW_ENERGY2_LAST_YEAR, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_CH_ENERGY_DELTA_TODAY: [SENSOR_CH_ENERGY_DELTA_TODAY, SensorDeviceClass.ENERGY, "mdi:cash", SensorStateClass.TOTAL_INCREASING],
    PARAM_DHW_ENERGY_DELTA_TODAY: [SENSOR_DHW_ENERGY_DELTA_TODAY, SensorDeviceClass.ENERGY, "mdi:cash", SensorStateClass.TOTAL_INCREASING],
    PARAM_CH_ENERGY_DELTA_YESTERDAY: [SENSOR_CH_ENERGY_DELTA_YESTERDAY, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_DHW_ENERGY_DELTA_YESTERDAY: [SENSOR_DHW_ENERGY_DELTA_YESTERDAY, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_CH_ENERGY_DELTA_LAST_7_DAYS: [SENSOR_CH_ENERGY_DELTA_LAST_7_DAYS, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_DHW_ENERGY_DELTA_LAST_7_DAYS: [SENSOR_DHW_ENERGY_DELTA_LAST_7_DAYS, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_CH_ENERGY_DELTA_THIS_MONTH: [SENSOR_CH_ENERGY_DELTA_THIS_MONTH, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_CH_ENERGY_DELTA_LAST_MONTH: [SENSOR_CH_ENERGY_DELTA_LAST_MONTH, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_DHW_ENERGY_DELTA_THIS_MONTH: [SENSOR_DHW_ENERGY_DELTA_THIS_MONTH, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_DHW_ENERGY_DELTA_LAST_MONTH: [SENSOR_DHW_ENERGY_DELTA_LAST_MONTH, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_CH_ENERGY_DELTA_THIS_YEAR: [SENSOR_CH_ENERGY_DELTA_THIS_YEAR, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_CH_ENERGY_DELTA_LAST_YEAR: [SENSOR_CH_ENERGY_DELTA_LAST_YEAR, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_DHW_ENERGY_DELTA_THIS_YEAR: [SENSOR_DHW_ENERGY_DELTA_THIS_YEAR, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_DHW_ENERGY_DELTA_LAST_YEAR: [SENSOR_DHW_ENERGY_DELTA_LAST_YEAR, SensorDeviceClass.ENERGY, "mdi:cash", None],
    PARAM_VERSION: [SENSOR_VERSION, None, "mdi:package-down", None],
}
SENSORS = deepcopy(sensors_default)
for param in sensors_default:
    if param in ZONED_PARAMS:
        for zone in range (1, 7):
            SENSORS[param_zoned(param, zone)] = (
                SENSORS[param][0] + f' Zone{zone}',
                SENSORS[param][1],
                SENSORS[param][2],
                SENSORS[param][3],
            )
        del SENSORS[param]


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
