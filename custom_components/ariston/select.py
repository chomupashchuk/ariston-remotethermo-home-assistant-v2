"""Suppoort for Ariston seletion."""
from datetime import timedelta
from copy import deepcopy

from homeassistant.components.select import SelectEntity
from homeassistant.const import CONF_SELECTOR, CONF_NAME

from .const import (
    DATA_ARISTON,
    DEVICES,
    PARAM_MODE,
    PARAM_CH_MODE,
    PARAM_DHW_MODE,
    PARAM_DHW_COMFORT_FUNCTION,
    VALUE,
    ZONE_PARAMETERS,
    ZONE_TEMPLATE, 
    ZONE_NAME_TEMPLATE
)

SELECT_MODE = "Boiler Mode"
SELECT_CH_MODE = "CH Mode"
SELECT_DHW_MODE = "DHW Mode"
SELECT_DHW_COMFORT = "DHW Comfort Function"

SCAN_INTERVAL = timedelta(seconds=2)

SELECTS = {
    PARAM_MODE: (SELECT_MODE, "mdi:water-boiler"),
    PARAM_CH_MODE: (SELECT_CH_MODE, "mdi:radiator"),
    PARAM_DHW_MODE: (SELECT_DHW_MODE, "mdi:water-pump"),
    PARAM_DHW_COMFORT_FUNCTION: (SELECT_DHW_COMFORT, "mdi:water-pump"),
}
for param in ZONE_PARAMETERS:
    if param in SELECTS:
        for zone in range(2, 4):
            SELECTS[ZONE_TEMPLATE.format(param, zone)] = (
                ZONE_NAME_TEMPLATE.format(SELECTS[param][0], zone),
                SELECTS[param][1]
            )


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up a select for Ariston."""
    if discovery_info is None:
        return

    name = discovery_info[CONF_NAME]
    device = hass.data[DATA_ARISTON][DEVICES][name]
    add_entities(
        [
            AristonSelect(name, device, select_type)
            for select_type in discovery_info[CONF_SELECTOR]
        ],
        True,
    )


class AristonSelect(SelectEntity):
    """Select for Ariston."""

    def __init__(self, name, device, select_type):
        """Initialize entity."""
        self._api = device.api.ariston_api
        self._icon = SELECTS[select_type][1]
        self._name = "{} {}".format(name, SELECTS[select_type][0])
        self._select_type = select_type
        self._state = None
        self._device = device.device

    @property
    def unique_id(self):
        """Return the unique id."""
        return f"{self._name}-SELECT-{self._select_type}"

    @property
    def should_poll(self):
        """Return True if entity has to be polled for state."""
        return True

    @property
    def name(self):
        """Return the name of this select device if any."""
        return self._name

    @property
    def icon(self):
        """Return the state attributes."""
        return self._icon

    @property
    def available(self):
        """Return True if entity is available."""
        try:
            return (
                self._api.available
                and not self._api.sensor_values[self._select_type][VALUE] is None
            )
        except KeyError:
            return False

    @property
    def current_option(self):
        """Return current option."""
        try:
            return self._api.sensor_values[self._select_type][VALUE]
        except KeyError:
            return None

    @property
    def options(self):
        """Return options."""
        try:
            return list(self._api.supported_sensors_set_values[self._select_type])
        except:
            return []

    def select_option(self, option):
        """Change the selected option."""
        self._api.set_http_data(**{self._select_type: option})

    def update(self):
        """Update data"""
        return
