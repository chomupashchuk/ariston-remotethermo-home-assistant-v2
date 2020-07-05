"""Support for Ariston water heaters."""
import logging
from datetime import timedelta

from homeassistant.components.water_heater import (
    SUPPORT_OPERATION_MODE,
    SUPPORT_TARGET_TEMPERATURE,
    WaterHeaterEntity,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_NAME,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)

from .const import (
    DATA_ARISTON,
    DEVICES,
    PARAM_DHW_MODE,
    PARAM_DHW_STORAGE_TEMPERATURE,
    PARAM_DHW_SET_TEMPERATURE,
    PARAM_DHW_FLAME,
    PARAM_MODE,
    PARAM_UNITS,
    VAL_SUMMER,
    VAL_WINTER,
    VAL_OFFLINE,
    VAL_IMPERIAL,
    VAL_METRIC,
    VALUE,
)

ACTION_IDLE = "idle"
ACTION_HEATING = "heating"
UNKNOWN_TEMP = 0.

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
        self._api = device.api.Ariston

    @property
    def name(self):
        """Return the name of the Climate device."""
        return self._name

    @property
    def icon(self):
        """Return the name of the Water Heater device."""
        current_mode = VAL_OFFLINE
        try:
            if self._api.ch_available:
                current_mode = self._api.sensor_values[PARAM_MODE][VALUE]
        except:
            current_mode = VAL_OFFLINE
        finally:
            if current_mode in [VAL_WINTER, VAL_SUMMER]:
                return "mdi:water-pump"
            else:
                return "mdi:water-pump-off"

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this thermostat."""
        return '_'.join([self._name, 'water_heater'])

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
        features = SUPPORT_TARGET_TEMPERATURE
        try:
            if self._api.supported_sensors_set_values[PARAM_DHW_MODE]:
                features = features | SUPPORT_OPERATION_MODE
        except:
            features = SUPPORT_TARGET_TEMPERATURE
        return features

    @property
    def current_temperature(self):
        """Return the temperature"""
        current_temp = None
        try:
            current_temp = self._api.sensor_values[PARAM_DHW_STORAGE_TEMPERATURE][VALUE]
            if current_temp == 0:
                # Not supported
                current_temp = None
        except:
            current_temp = None
        finally:
            return current_temp

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        units = VAL_METRIC
        try:
            units = self._api.sensor_values[PARAM_UNITS][VALUE]
        except:
            units = VAL_METRIC
        finally:
            if units == VAL_IMPERIAL:
                return TEMP_FAHRENHEIT
            else:
                return TEMP_CELSIUS

    @property
    def min_temp(self):
        """Return minimum temperature."""
        minimum_temp = UNKNOWN_TEMP
        try:
            minimum_temp = self._api.supported_sensors_set_values[PARAM_DHW_SET_TEMPERATURE]["min"]
        except:
            minimum_temp = UNKNOWN_TEMP
        finally:
            return minimum_temp

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        maximum_temp = UNKNOWN_TEMP
        try:
            maximum_temp = self._api.supported_sensors_set_values[PARAM_DHW_SET_TEMPERATURE]["max"]
        except:
            maximum_temp = UNKNOWN_TEMP
        finally:
            return maximum_temp

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        target_temp = UNKNOWN_TEMP
        try:
            target_temp = self._api.sensor_values[PARAM_DHW_SET_TEMPERATURE][VALUE]
        except:
            target_temp = UNKNOWN_TEMP
        finally:
            return target_temp

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        step = 1.
        try:
            step = self._api.supported_sensors_set_values[PARAM_DHW_SET_TEMPERATURE]["step"]
        except:
            step = 1.
        finally:
            return step

    @property
    def device_state_attributes(self):
        """Return the supported step of target temperature."""
        try:
            step = self._api.supported_sensors_set_values[PARAM_DHW_SET_TEMPERATURE]["step"]
        except:
            step = 1.
            pass
        try:
            if self._api.sensor_values[PARAM_DHW_FLAME][VALUE]:
                action = ACTION_HEATING
            else:
                action = ACTION_IDLE
        except:
            action = ACTION_IDLE
            pass
        data = {"target_temp_step": step, "hvac_action": action}
        return data

    @property
    def operation_list(self):
        """List of available operation modes."""
        op_list = []
        try:
            op_list = self._api.supported_sensors_set_values[PARAM_DHW_MODE]
        except:
            op_list = []
        finally:
            return op_list

    @property
    def current_operation(self):
        """Return current operation"""
        current_op = VAL_OFFLINE
        try:
            current_op = self._api.sensor_values[PARAM_DHW_MODE][VALUE]
        except:
            current_op = VAL_OFFLINE
        finally:
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
