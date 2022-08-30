"""Suppoort for Ariston seletion."""
import logging
from datetime import timedelta
from copy import deepcopy

from homeassistant.components.select import SelectEntity
from homeassistant.const import CONF_SELECTOR, CONF_NAME

from .const import param_zoned
from .const import (
    DATA_ARISTON,
    DEVICES,
    PARAM_DHW_COMFORT_TEMPERATURE,
    PARAM_DHW_ECONOMY_TEMPERATURE,
    PARAM_MODE,
    PARAM_CH_MODE,
    PARAM_DHW_MODE,
    PARAM_DHW_COMFORT_FUNCTION,
    PARAM_UNITS,
    VALUE,
    OPTIONS_TXT,
    MIN,
    MAX,
    STEP,
    PARAM_CH_SET_TEMPERATURE,
    PARAM_CH_COMFORT_TEMPERATURE,
    PARAM_CH_ECONOMY_TEMPERATURE,
    PARAM_CH_WATER_TEMPERATURE,
    PARAM_CH_FIXED_TEMP,
    PARAM_DHW_SET_TEMPERATURE,
    ZONED_PARAMS
)

SELECT_MODE = "Boiler Mode"
SELECT_CH_MODE = "CH Mode"
SELECT_DHW_MODE = "DHW Mode"
SELECT_DHW_COMFORT = "DHW Comfort Function"
SELECT_UNITS = "Units"
SELECT_CH_SET_TEMPERATURE = "CH Set Temperature"
SELECT_CH_COMFORT_TEMPERATURE = "CH Comfort Temperature"
SELECT_CH_ECONOMY_TEMPERATURE = "CH Economy Temperature"
SELECT_CH_WATER_TEMPERATURE = "CH Water Temperature"
SELECT_CH_FIXED_TEMP = "CH Fixed Temperature"
SELECT_DHW_SET_TEMPERATURE = "DHW Set Temperature"
SELECT_DHW_COMFORT_TEMPERATURE = "DHW Comfort Temperature"
SELECT_DHW_ECONOMY_TEMPERATURE = "DHW Economy Temperature"

SCAN_INTERVAL = timedelta(seconds=2)

selects_deafult = {
    PARAM_MODE: (SELECT_MODE, "mdi:water-boiler"),
    PARAM_CH_MODE: (SELECT_CH_MODE, "mdi:radiator"),
    PARAM_DHW_MODE: (SELECT_DHW_MODE, "mdi:water-pump"),
    PARAM_DHW_COMFORT_FUNCTION: (SELECT_DHW_COMFORT, "mdi:water-pump"),
    PARAM_CH_FIXED_TEMP: (SELECT_CH_FIXED_TEMP, "mdi:radiator"),
    PARAM_CH_SET_TEMPERATURE: (SELECT_CH_SET_TEMPERATURE, "mdi:radiator"),
    PARAM_CH_COMFORT_TEMPERATURE: (SELECT_CH_COMFORT_TEMPERATURE, "mdi:radiator"),
    PARAM_CH_ECONOMY_TEMPERATURE: (SELECT_CH_ECONOMY_TEMPERATURE, "mdi:radiator"),
    PARAM_CH_WATER_TEMPERATURE: (SELECT_CH_WATER_TEMPERATURE, "mdi:water-pump"),
    PARAM_DHW_SET_TEMPERATURE: (SELECT_DHW_SET_TEMPERATURE, "mdi:water-pump"),
    PARAM_DHW_COMFORT_TEMPERATURE: (SELECT_DHW_COMFORT_TEMPERATURE, "mdi:water-pump"),
    PARAM_DHW_ECONOMY_TEMPERATURE: (SELECT_DHW_ECONOMY_TEMPERATURE, "mdi:water-pump"),
}
SELECTS = deepcopy(selects_deafult)
for param in selects_deafult:
    if param in ZONED_PARAMS:
        for zone in range (1, 7):
            SELECTS[param_zoned(param, zone)] = (
                SELECTS[param][0] + f' Zone{zone}',
                SELECTS[param][1]
            )
        del SELECTS[param]

_LOGGER = logging.getLogger(__name__)

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
                and self._api.sensor_values[self._select_type][VALUE] is not None
            )
        except KeyError:
            return False

    @property
    def current_option(self):
        """Return current option."""
        try:
            return str(self._api.sensor_values[self._select_type][VALUE])
        except KeyError:
            return None

    @property
    def options(self):
        """Return options."""
        try:
            if self._api.sensor_values[self._select_type][VALUE] is not None and \
                self._api.sensor_values[self._select_type][OPTIONS_TXT] is not None:
                return self._api.sensor_values[self._select_type][OPTIONS_TXT]
            elif self._api.sensor_values[self._select_type][VALUE] is not None:
                min_val = self._api.sensor_values[self._select_type][MIN]
                max_val = self._api.sensor_values[self._select_type][MAX]
                step_val = self._api.sensor_values[self._select_type][STEP]
                values = list()
                value = min_val
                while value < max_val + .1:
                    values.append(str(value))
                    value += step_val
                return values
            else:
                return []
        except:
            return []

    def select_option(self, option):
        """Change the selected option."""
        self._api.set_http_data(**{self._select_type: option})

    def update(self):
        """Update data"""
        return
