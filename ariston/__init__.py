"""Suppoort for Ariston."""
import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR
from homeassistant.components.climate import DOMAIN as CLIMATE
from homeassistant.components.sensor import DOMAIN as SENSOR
from homeassistant.components.switch import DOMAIN as SWITCH
from homeassistant.components.water_heater import DOMAIN as WATER_HEATER
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_BINARY_SENSORS,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_SENSORS,
    CONF_SWITCHES,
    CONF_USERNAME,
)
from homeassistant.helpers import discovery

from .ariston import AristonHandler

from .binary_sensor import BINARY_SENSORS
from .const import (
    DOMAIN,
    DATA_ARISTON,
    DEVICES,
    SERVICE_SET_DATA,
    CLIMATES,
    WATER_HEATERS,
    CONF_HVAC_OFF,
    CONF_MAX_RETRIES,
    CONF_STORE_CONFIG_FILES,
    CONF_HVAC_OFF_PRESENT,
    CONF_UNITS,
    PARAM_ACCOUNT_CH_GAS,
    PARAM_ACCOUNT_CH_ELECTRICITY,
    PARAM_ACCOUNT_DHW_GAS,
    PARAM_ACCOUNT_DHW_ELECTRICITY,
    PARAM_CH_ANTIFREEZE_TEMPERATURE,
    PARAM_CH_MODE,
    PARAM_CH_SET_TEMPERATURE,
    PARAM_CH_SET_TEMPERATURE_MIN,
    PARAM_CH_SET_TEMPERATURE_MAX,
    PARAM_CH_COMFORT_TEMPERATURE,
    PARAM_CH_ECONOMY_TEMPERATURE,
    PARAM_CH_DETECTED_TEMPERATURE,
    PARAM_CH_PROGRAM,
    PARAM_ERRORS,
    PARAM_ERRORS_COUNT,
    PARAM_DHW_COMFORT_FUNCTION,
    PARAM_DHW_MODE,
    PARAM_DHW_PROGRAM,
    PARAM_DHW_SET_TEMPERATURE,
    PARAM_DHW_SET_TEMPERATURE_MIN,
    PARAM_DHW_SET_TEMPERATURE_MAX,
    PARAM_DHW_STORAGE_TEMPERATURE,
    PARAM_DHW_COMFORT_TEMPERATURE,
    PARAM_DHW_ECONOMY_TEMPERATURE,
    PARAM_HEATING_LAST_24H,
    PARAM_HEATING_LAST_7D,
    PARAM_HEATING_LAST_30D,
    PARAM_HEATING_LAST_365D,
    PARAM_HEATING_LAST_24H_LIST,
    PARAM_HEATING_LAST_7D_LIST,
    PARAM_HEATING_LAST_30D_LIST,
    PARAM_HEATING_LAST_365D_LIST,
    PARAM_MODE,
    PARAM_OUTSIDE_TEMPERATURE,
    PARAM_SIGNAL_STRENGTH,
    PARAM_WATER_LAST_24H,
    PARAM_WATER_LAST_7D,
    PARAM_WATER_LAST_30D,
    PARAM_WATER_LAST_365D,
    PARAM_WATER_LAST_24H_LIST,
    PARAM_WATER_LAST_7D_LIST,
    PARAM_WATER_LAST_30D_LIST,
    PARAM_WATER_LAST_365D_LIST,
    PARAM_UNITS,
    PARAM_THERMAL_CLEANSE_CYCLE,
    PARAM_GAS_TYPE,
    PARAM_GAS_COST,
    PARAM_ELECTRICITY_COST,
    PARAM_GAS_TYPE_UNIT,
    PARAM_GAS_COST_UNIT,
    PARAM_ELECTRICITY_COST_UNIT,
    PARAM_CH_AUTO_FUNCTION,
    PARAM_CH_FLAME,
    PARAM_DHW_FLAME,
    PARAM_FLAME,
    PARAM_HEAT_PUMP,
    PARAM_HOLIDAY_MODE,
    PARAM_INTERNET_TIME,
    PARAM_INTERNET_WEATHER,
    PARAM_ONLINE,
    PARAM_CHANGING_DATA,
    PARAM_THERMAL_CLEANSE_FUNCTION,
    PARAM_CH_PILOT,
    PARAM_UPDATE,
    PARAM_ONLINE_VERSION,
    VALUE,
    UNITS,
    VAL_METRIC,
    VAL_IMPERIAL,
    VAL_AUTO,
    VAL_WINTER,
    VAL_SUMMER,
    VAL_OFF,
    VAL_HEATING_ONLY,
)
from .sensor import SENSORS
from .switch import SWITCHES

DEFAULT_HVAC = VAL_SUMMER
DEFAULT_NAME = "Ariston"
DEFAULT_MAX_RETRIES = 5

_LOGGER = logging.getLogger(__name__)

ARISTON_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_BINARY_SENSORS): vol.All(
            cv.ensure_list, [vol.In(BINARY_SENSORS)]
        ),
        vol.Optional(CONF_SENSORS): vol.All(cv.ensure_list, [vol.In(SENSORS)]),
        vol.Optional(CONF_HVAC_OFF, default=DEFAULT_HVAC): vol.In(
            [VAL_OFF, VAL_SUMMER]
        ),
        vol.Optional(CONF_MAX_RETRIES, default=DEFAULT_MAX_RETRIES): vol.All(
            int, vol.Range(min=0, max=65535)
        ),
        vol.Optional(CONF_SWITCHES): vol.All(cv.ensure_list, [vol.In(SWITCHES)]),
        vol.Optional(CONF_STORE_CONFIG_FILES, default=False): cv.boolean,
        vol.Optional(CONF_HVAC_OFF_PRESENT, default=False): cv.boolean,
        vol.Optional(CONF_UNITS, default=VAL_METRIC): vol.In(
            [VAL_METRIC, VAL_IMPERIAL, VAL_AUTO]
        ),
    }
)


def _has_unique_names(devices):
    names = [device[CONF_NAME] for device in devices]
    vol.Schema(vol.Unique())(names)
    return devices


CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.All(cv.ensure_list, [ARISTON_SCHEMA], _has_unique_names)},
    extra=vol.ALLOW_EXTRA,
)


class AristonChecker:
    """Ariston checker"""

    def __init__(
        self,
        hass,
        device,
        name,
        username,
        password,
        store_file,
        units,
        sensors,
        binary_sensors,
        switches,
    ):
        """Initialize."""

        self.device = device
        self._hass = hass
        self.name = name

        list_of_sensors = list({*sensors, *binary_sensors, *switches})
        """ Some sensors or switches are not part of API """
        if PARAM_CHANGING_DATA in list_of_sensors:
            list_of_sensors.remove(PARAM_CHANGING_DATA)
        if PARAM_ONLINE in list_of_sensors:
            list_of_sensors.remove(PARAM_ONLINE)

        self.ariston_api = AristonHandler(
            username=username,
            password=password,
            sensors=list_of_sensors,
            units=units,
            store_file=store_file,
            #store_folder="/config/ariston_http_data",
        )


def setup(hass, config):
    """Set up the Ariston component."""
    if DOMAIN not in config:
        return True
    hass.data.setdefault(DATA_ARISTON, {DEVICES: {}, CLIMATES: [], WATER_HEATERS: []})
    api_list = []
    for device in config[DOMAIN]:
        name = device[CONF_NAME]
        username = device[CONF_USERNAME]
        password = device[CONF_PASSWORD]
        store_file = device[CONF_STORE_CONFIG_FILES]
        units = device[CONF_UNITS]
        binary_sensors = device.get(CONF_BINARY_SENSORS)
        sensors = device.get(CONF_SENSORS)
        switches = device.get(CONF_SWITCHES)

        api = AristonChecker(
            hass=hass,
            device=device,
            name=name,
            username=username,
            password=password,
            store_file=store_file,
            units=units,
            sensors=sensors,
            binary_sensors=binary_sensors,
            switches=switches,
        )

        api_list.append(api)
        # start api execution
        api.ariston_api.start()

        # load all devices
        hass.data[DATA_ARISTON][DEVICES][name] = AristonDevice(api, device)

        discovery.load_platform(hass, CLIMATE, DOMAIN, {CONF_NAME: name}, config)

        discovery.load_platform(hass, WATER_HEATER, DOMAIN, {CONF_NAME: name}, config)

        if switches:
            discovery.load_platform(
                hass,
                SWITCH,
                DOMAIN,
                {CONF_NAME: name, CONF_SWITCHES: switches},
                config,
            )

        if binary_sensors:
            discovery.load_platform(
                hass,
                BINARY_SENSOR,
                DOMAIN,
                {CONF_NAME: name, CONF_BINARY_SENSORS: binary_sensors},
                config,
            )

        if sensors:
            discovery.load_platform(
                hass, SENSOR, DOMAIN, {CONF_NAME: name, CONF_SENSORS: sensors}, config
            )

    def set_ariston_data(call):
        """Handle the service call to set the data."""
        # Start with mandatory parameter
        entity_id = call.data.get(ATTR_ENTITY_ID, "")

        try:
            domain = entity_id.split(".")[0]
        except:
            _LOGGER.warning("Invalid entity_id domain for Ariston")
            raise Exception("Invalid entity_id domain for Ariston")
        if domain.lower() not in {"climate", "water_heater"}:
            _LOGGER.warning("Invalid entity_id domain for Ariston")
            raise Exception("Invalid entity_id domain for Ariston")
        try:
            device_id = entity_id.split(".")[1]
        except:
            _LOGGER.warning("Invalid entity_id device for Ariston")
            raise Exception("Invalid entity_id device for Ariston")

        for api in api_list:
            if api.name.replace(' ', '_').lower() == device_id.lower():
                # climate entity is found
                parameter_list = {}

                data = call.data.get(PARAM_MODE, "")
                if data != "":
                    parameter_list[PARAM_MODE] = str(data).lower()

                data = call.data.get(PARAM_CH_MODE, "")
                if data != "":
                    parameter_list[PARAM_CH_MODE] = str(data).lower()

                data = call.data.get(PARAM_CH_SET_TEMPERATURE, "")
                if data != "":
                    parameter_list[PARAM_CH_SET_TEMPERATURE] = str(data).lower()

                data = call.data.get(PARAM_CH_COMFORT_TEMPERATURE, "")
                if data != "":
                    parameter_list[PARAM_CH_COMFORT_TEMPERATURE] = str(data).lower()

                data = call.data.get(PARAM_CH_ECONOMY_TEMPERATURE, "")
                if data != "":
                    parameter_list[PARAM_CH_ECONOMY_TEMPERATURE] = str(data).lower()

                data = call.data.get(PARAM_DHW_SET_TEMPERATURE, "")
                if data != "":
                    parameter_list[PARAM_DHW_SET_TEMPERATURE] = str(data).lower()

                data = call.data.get(PARAM_DHW_COMFORT_TEMPERATURE, "")
                if data != "":
                    parameter_list[PARAM_DHW_COMFORT_TEMPERATURE] = str(data).lower()

                data = call.data.get(PARAM_DHW_ECONOMY_TEMPERATURE, "")
                if data != "":
                    parameter_list[PARAM_DHW_ECONOMY_TEMPERATURE] = str(data).lower()

                data = call.data.get(PARAM_DHW_MODE, "")
                if data != "":
                    parameter_list[PARAM_DHW_MODE] = str(data).lower()

                data = call.data.get(PARAM_DHW_COMFORT_FUNCTION, "")
                if data != "":
                    parameter_list[PARAM_DHW_COMFORT_FUNCTION] = str(data).lower()

                data = call.data.get(PARAM_INTERNET_TIME, "")
                if data != "":
                    parameter_list[PARAM_INTERNET_TIME] = str(data).lower()

                data = call.data.get(PARAM_INTERNET_WEATHER, "")
                if data != "":
                    parameter_list[PARAM_INTERNET_WEATHER] = str(data).lower()

                data = call.data.get(PARAM_CH_AUTO_FUNCTION, "")
                if data != "":
                    parameter_list[PARAM_CH_AUTO_FUNCTION] = str(data).lower()

                data = call.data.get(PARAM_UNITS, "")
                if data != "":
                    parameter_list[PARAM_UNITS] = str(data).lower()

                data = call.data.get(PARAM_THERMAL_CLEANSE_CYCLE, "")
                if data != "":
                    parameter_list[PARAM_THERMAL_CLEANSE_CYCLE] = str(data).lower()

                data = call.data.get(PARAM_THERMAL_CLEANSE_FUNCTION, "")
                if data != "":
                    parameter_list[PARAM_THERMAL_CLEANSE_FUNCTION] = str(data).lower()

                _LOGGER.debug("Ariston device found, data to check and send")

                api.ariston_api.set_http_data(**parameter_list)
                return
            raise Exception("Corresponding entity_id for Ariston not found")
        return

    hass.services.register(DOMAIN, SERVICE_SET_DATA, set_ariston_data)

    if not hass.data[DATA_ARISTON][DEVICES]:
        return False
    # Return boolean to indicate that initialization was successful.
    return True


class AristonDevice:
    """Representation of a base Ariston discovery device."""

    def __init__(self, api, device):
        """Initialize the entity."""
        self.api = api
        self.device = device
