"""Suppoort for Ariston binary sensors."""
import logging
from datetime import timedelta
from copy import deepcopy
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import CONF_BINARY_SENSORS, CONF_NAME

from .const import param_zoned
from .const import (
    DATA_ARISTON,
    DEVICES,
    PARAM_HOLIDAY_MODE,
    PARAM_ONLINE,
    PARAM_FLAME,
    PARAM_HEAT_PUMP,
    PARAM_CHANGING_DATA,
    PARAM_INTERNET_TIME,
    PARAM_INTERNET_WEATHER,
    PARAM_CH_AUTO_FUNCTION,
    PARAM_CH_FLAME,
    PARAM_DHW_FLAME,
    PARAM_THERMAL_CLEANSE_FUNCTION,
    PARAM_CH_PILOT,
    VALUE,
    VAL_ON,
    ZONED_PARAMS
)

BINARY_SENSOR_CH_FLAME = "CH Flame"
BINARY_SENSOR_DHW_FLAME = "DHW Flame"
BINARY_SENSOR_CH_AUTO_FUNCTION = "CH Auto Function"
BINARY_SENSOR_HOLIDAY_MODE = "Holiday Mode"
BINARY_SENSOR_ONLINE = "Online"
BINARY_SENSOR_FLAME = "Flame"
BINARY_SENSOR_HEAT_PUMP = "Heat Pump"
BINARY_SENSOR_CHANGING_DATA = "Changing Data"
BINARY_SENSOR_INTERNET_TIME = "Internet Time"
BINARY_SENSOR_INTERNET_WEATHER = "Internet Weather"
BINARY_SENSOR_THERMAL_CLEANSE_FUNCTION = "Thermal Cleanse Function"
BINARY_SENSOR_CH_PILOT = "CH Pilot"

SCAN_INTERVAL = timedelta(seconds=2)

_LOGGER = logging.getLogger(__name__)

# Binary sensor types are defined like: Name, device class
binary_sensors_default = {
    PARAM_CH_AUTO_FUNCTION: (BINARY_SENSOR_CH_AUTO_FUNCTION, None, "mdi:radiator"),
    PARAM_CH_FLAME: (BINARY_SENSOR_CH_FLAME, None, "mdi:fire"),
    PARAM_DHW_FLAME: (BINARY_SENSOR_DHW_FLAME, None, "mdi:fire"),
    PARAM_HOLIDAY_MODE: (BINARY_SENSOR_HOLIDAY_MODE, None, "mdi:island"),
    PARAM_ONLINE: (BINARY_SENSOR_ONLINE, BinarySensorDeviceClass.CONNECTIVITY, None),
    PARAM_FLAME: (BINARY_SENSOR_FLAME, None, "mdi:fire"),
    PARAM_HEAT_PUMP: (BINARY_SENSOR_HEAT_PUMP, None, "mdi:fan"),
    PARAM_CHANGING_DATA: (BINARY_SENSOR_CHANGING_DATA, None, "mdi:cogs"),
    PARAM_INTERNET_TIME: (BINARY_SENSOR_INTERNET_TIME, None, "mdi:update"),
    PARAM_INTERNET_WEATHER: (
        BINARY_SENSOR_INTERNET_WEATHER,
        None,
        "mdi:weather-partly-cloudy",
    ),
    PARAM_THERMAL_CLEANSE_FUNCTION: (
        BINARY_SENSOR_THERMAL_CLEANSE_FUNCTION,
        None,
        "mdi:allergy",
    ),
    PARAM_CH_PILOT: (BINARY_SENSOR_CH_PILOT, None, "mdi:head-cog-outline"),
}
BINARY_SENSORS = deepcopy(binary_sensors_default)
for param in binary_sensors_default:
    if param in ZONED_PARAMS:
        for zone in range (1, 7):
            BINARY_SENSORS[param_zoned(param, zone)] = (
                BINARY_SENSORS[param][0] + f' Zone{zone}',
                BINARY_SENSORS[param][1],
                BINARY_SENSORS[param][2]
            )
        del BINARY_SENSORS[param]


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up a binary sensor for Ariston."""
    if discovery_info is None:
        return

    name = discovery_info[CONF_NAME]
    device = hass.data[DATA_ARISTON][DEVICES][name]
    add_entities(
        [
            AristonBinarySensor(name, device, sensor_type)
            for sensor_type in discovery_info[CONF_BINARY_SENSORS]
        ],
        True,
    )


class AristonBinarySensor(BinarySensorEntity):
    """Binary sensor for Ariston."""

    def __init__(self, name, device, sensor_type):
        """Initialize entity."""
        self._api = device.api.ariston_api
        self._attrs = {}
        self._device_class = BINARY_SENSORS[sensor_type][1]
        self._icon = BINARY_SENSORS[sensor_type][2]
        self._name = "{} {}".format(name, BINARY_SENSORS[sensor_type][0])
        self._sensor_type = sensor_type
        self._state = None

    @property
    def unique_id(self):
        """Return the unique id."""
        return f"{self._name}-{self._sensor_type}"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attrs

    @property
    def should_poll(self):
        """Return True if entity has to be polled for state."""
        return True

    @property
    def name(self):
        """Return entity name."""
        return self._name

    @property
    def is_on(self):
        """Return if entity is on."""
        return self._state

    @property
    def device_class(self):
        """Return device class."""
        return self._device_class

    @property
    def available(self):
        """Return True if entity is available."""
        if self._sensor_type == PARAM_ONLINE:
            return True
        elif self._sensor_type == PARAM_CHANGING_DATA:
            return self._api.available
        else:
            return (
                self._api.available
                and not self._api.sensor_values[self._sensor_type][VALUE] is None
            )

    @property
    def icon(self):
        """Return the state attributes."""
        return self._icon

    def update(self):
        """Update entity."""
        try:
            if self._sensor_type == PARAM_ONLINE:
                self._state = self._api.available
            elif self._sensor_type == PARAM_CHANGING_DATA:
                self._state = self._api.setting_data
            else:
                if not self._api.available:
                    return
                if self._api.sensor_values[self._sensor_type][VALUE] == VAL_ON:
                    self._state = True
                else:
                    self._state = False
        except KeyError:
            _LOGGER.warning("Problem updating binary_sensors for Ariston")
