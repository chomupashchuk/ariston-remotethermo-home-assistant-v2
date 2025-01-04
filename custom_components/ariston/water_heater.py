"""Support for Ariston water heaters."""
import logging
from datetime import timedelta

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature
)

from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_NAME,
    UnitOfTemperature,
)

from .const import (
    DATA_ARISTON,
    DEVICES,
    DOMAIN,
    PARAM_DHW_MODE,
    PARAM_DHW_STORAGE_TEMPERATURE,
    PARAM_DHW_SET_TEMPERATURE,
    PARAM_DHW_FLAME,
    PARAM_MODE,
    VAL_COOLING,
    VAL_SUMMER,
    VAL_WINTER,
    VAL_OFFLINE,
    VAL_DISABLED,
    VALUE,
    UNITS,
    MIN,
    MAX,
    STEP,
    OPTIONS_TXT,
    VAL_ON
)

ACTION_IDLE = "idle"
ACTION_HEATING = "heating"
UNKNOWN_TEMP = 0.0

SCAN_INTERVAL = timedelta(seconds=2)

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Ariston water heater devices."""
    if discovery_info is None:
        return

    name = discovery_info[CONF_NAME]
    device = hass.data[DATA_ARISTON][DEVICES][name]

    add_entities([AristonWaterHeater(name, device)])


class AristonWaterHeater(WaterHeaterEntity):
    """Ariston Water Heater Device."""

    def __init__(self, name, device):
        """Initialize the thermostat."""
        self._name = name
        self._api = device.api.ariston_api

    @property
    def unique_id(self):
        """Return the unique id."""
        return f"{self._name}-water_heater"

    @property
    def name(self):
        """Return the name of the Climate device."""
        return self._name

    @property
    def icon(self):
        """Return the name of the Water Heater device."""
        try:
            if self._api.dhw_available:
                current_mode = self._api.sensor_values[PARAM_MODE][VALUE]
            else:
                current_mode = VAL_OFFLINE
        except KeyError:
            return "mdi:water-pump-off"
        if current_mode in [VAL_WINTER, VAL_SUMMER, VAL_COOLING]:
            return "mdi:water-pump"
        else:
            return "mdi:water-pump-off"

    @property
    def should_poll(self):
        """Polling is required."""
        return True

    @property
    def available(self):
        """Return True if entity is available."""
        return self._api.dhw_available

    @property
    def supported_features(self):
        """Return the list of supported features."""
        try:
            if self._api.sensor_values[PARAM_DHW_MODE][OPTIONS_TXT]:
                features = WaterHeaterEntityFeature.OPERATION_MODE | WaterHeaterEntityFeature.TARGET_TEMPERATURE
            else:
                features = WaterHeaterEntityFeature.TARGET_TEMPERATURE
        except KeyError:
            return WaterHeaterEntityFeature.TARGET_TEMPERATURE
        return features

    @property
    def current_temperature(self):
        """Return the temperature"""
        try:
            current_temp = self._api.sensor_values[PARAM_DHW_STORAGE_TEMPERATURE][VALUE]
            if current_temp == 0:
                # Not supported
                current_temp = None
        except KeyError:
            return None
        return current_temp

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        try:
            units = self._api.sensor_values[PARAM_DHW_SET_TEMPERATURE][UNITS]
        except KeyError:
            return UnitOfTemperature.CELSIUS
        return units

    @property
    def min_temp(self):
        """Return minimum temperature."""
        try:
            minimum_temp = self._api.sensor_values[PARAM_DHW_SET_TEMPERATURE][MIN]
        except KeyError:
            return UNKNOWN_TEMP
        return minimum_temp

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        try:
            maximum_temp = self._api.sensor_values[PARAM_DHW_SET_TEMPERATURE][MAX]
        except KeyError:
            return UNKNOWN_TEMP
        return maximum_temp

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        try:
            target_temp = self._api.sensor_values[PARAM_DHW_SET_TEMPERATURE][VALUE]
        except KeyError:
            return UNKNOWN_TEMP
        return target_temp

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        try:
            step = self._api.sensor_values[PARAM_DHW_SET_TEMPERATURE][STEP]
        except KeyError:
            return 1.0
        return step

    @property
    def extra_state_attributes(self):
        """Return the supported step of target temperature."""
        try:
            step = self._api.sensor_values[PARAM_DHW_SET_TEMPERATURE][STEP]
        except KeyError:
            step = 1.0
        try:
            if self._api.sensor_values[PARAM_DHW_FLAME][VALUE] == VAL_ON:
                action = ACTION_HEATING
            else:
                action = ACTION_IDLE
        except KeyError:
            action = ACTION_IDLE
        return {"target_temp_step": step, "hvac_action": action}

    @property
    def operation_list(self):
        """List of available operation modes."""
        try:
            op_list = self._api.sensor_values[PARAM_DHW_MODE][OPTIONS_TXT]
        except KeyError:
            return []
        return op_list

    @property
    def current_operation(self):
        """Return current operation"""
        try:
            current_op = self._api.sensor_values[PARAM_DHW_MODE][VALUE]
        except KeyError:
            if self._api.dhw_available:
                return VAL_DISABLED
            else:
                return VAL_OFFLINE
        return current_op

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        new_temperature = kwargs.get(ATTR_TEMPERATURE)
        if new_temperature is not None:
            self._api.set_http_data(**{PARAM_DHW_SET_TEMPERATURE: new_temperature})

    def set_operation_mode(self, operation_mode):
        """Set operation mode."""
        self._api.set_http_data(**{PARAM_DHW_MODE: operation_mode})

    def update(self):
        """Update all Node data from Hive."""
        return

