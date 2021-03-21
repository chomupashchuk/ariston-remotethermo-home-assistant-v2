"""Suppoort for Ariston binary sensors."""

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_CONNECTIVITY,
    DEVICE_CLASS_HEAT,
    BinarySensorEntity,
)
from homeassistant.const import CONF_BINARY_SENSORS, CONF_NAME

import logging
from datetime import timedelta

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
    PARAM_UPDATE,
    PARAM_ONLINE_VERSION,
    VALUE,
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
BINARY_SENSOR_UPDATE = "Update Available"

SCAN_INTERVAL = timedelta(seconds=2)

_LOGGER = logging.getLogger(__name__)

# Binary sensor types are defined like: Name, device class
BINARY_SENSORS = {
    PARAM_CH_AUTO_FUNCTION: (BINARY_SENSOR_CH_AUTO_FUNCTION, None, "mdi:radiator"),
    PARAM_CH_FLAME: (BINARY_SENSOR_CH_FLAME, None, "mdi:fire"),
    PARAM_DHW_FLAME: (BINARY_SENSOR_DHW_FLAME, None, "mdi:fire"),
    PARAM_HOLIDAY_MODE: (BINARY_SENSOR_HOLIDAY_MODE, None, "mdi:island"),
    PARAM_ONLINE: (BINARY_SENSOR_ONLINE, DEVICE_CLASS_CONNECTIVITY, None),
    PARAM_FLAME: (BINARY_SENSOR_FLAME, None, "mdi:fire"),
    PARAM_HEAT_PUMP: (BINARY_SENSOR_HEAT_PUMP, DEVICE_CLASS_HEAT, None),
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
    PARAM_UPDATE: (BINARY_SENSOR_UPDATE, None, "mdi:package-down"),
}


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
    def device_state_attributes(self):
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
            elif self._sensor_type == PARAM_UPDATE:
                self._attrs["Installed"] = self._api.version
                self._state = self._api.sensor_values[self._sensor_type][VALUE]
                self._attrs["Online"] = self._api.sensor_values[PARAM_ONLINE_VERSION][
                    VALUE
                ]
            else:
                if not self._api.available:
                    return
                if not self._api.sensor_values[self._sensor_type][VALUE] is None:
                    self._state = self._api.sensor_values[self._sensor_type][VALUE]
                else:
                    self._state = False
        except KeyError:
            _LOGGER.warning("Problem updating binary_sensors for Ariston")
