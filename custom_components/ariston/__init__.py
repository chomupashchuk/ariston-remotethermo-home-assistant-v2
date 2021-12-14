"""Suppoort for Ariston."""
import logging

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR
from homeassistant.components.climate import DOMAIN as CLIMATE
from homeassistant.components.sensor import DOMAIN as SENSOR
from homeassistant.components.switch import DOMAIN as SWITCH
from homeassistant.components.select import DOMAIN as SELECT
from homeassistant.components.water_heater import DOMAIN as WATER_HEATER
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_BINARY_SENSORS,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_SENSORS,
    CONF_SWITCHES,
    CONF_SELECTOR,
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
    CONF_POLLING,
    CONF_LOG,
    CONF_GW,
    CONF_ZONES,
    CONF_CLIMATES,
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
    PARAM_CH_FIXED_TEMP,
    PARAM_CH_WATER_TEMPERATURE,
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
    VAL_COOLING,
    ZONE_PARAMETERS,
    ZONE_TEMPLATE,
    ZONE_NAME_TEMPLATE
)
from .sensor import SENSORS
from .switch import SWITCHES
from .select import SELECTS

DEFAULT_HVAC = VAL_SUMMER
DEFAULT_NAME = "Ariston"
DEFAULT_MAX_RETRIES = 5
DEFAULT_POLLING = 1.0
DEFAULT_ZONES = 1

_LOGGER = logging.getLogger(__name__)

ARISTON_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_GW, default=""): cv.string,
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
        vol.Optional(CONF_SELECTOR): vol.All(cv.ensure_list, [vol.In(SELECTS)]),
        vol.Optional(CONF_STORE_CONFIG_FILES, default=False): cv.boolean,
        vol.Optional(CONF_HVAC_OFF_PRESENT, default=False): cv.boolean,
        vol.Optional(CONF_UNITS, default=VAL_METRIC): vol.In(
            [VAL_METRIC, VAL_IMPERIAL, VAL_AUTO]
        ),
        vol.Optional(CONF_POLLING, default=DEFAULT_POLLING): vol.All(
            float, vol.Range(min=1, max=5)
        ),
        vol.Optional(CONF_LOG, default="DEBUG"): vol.In(
            ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]
        ),
        vol.Optional(CONF_ZONES, default=DEFAULT_ZONES): vol.All(
            int, vol.Range(min=1, max=3)
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
        selectors,
        polling,
        logging,
        gw,
        zones
    ):
        """Initialize."""

        self.device = device
        self._hass = hass
        self.name = name
        self.zones = zones

        if not sensors:
            sensors = list()
        if not binary_sensors:
            binary_sensors = list()
        if not switches:
            switches = list()
        if not selectors:
            selectors = list()

        list_of_sensors = list({*sensors, *binary_sensors, *switches, *selectors})
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
            polling=polling,
            logging_level=logging,
            #store_folder="/config/ariston_http_data",
            gw=gw,
            zones=zones
        )


def setup(hass, config):
    """Set up the Ariston component."""
    if DOMAIN not in config:
        return True
    hass.data.setdefault(DATA_ARISTON, {DEVICES: {}, CLIMATES: [], WATER_HEATERS: []})
    api_list = []
    dev_gateways = set()
    dev_names = set()
    for device in config[DOMAIN]:
        name = device[CONF_NAME]
        username = device[CONF_USERNAME]
        password = device[CONF_PASSWORD]
        store_file = device[CONF_STORE_CONFIG_FILES]
        units = device[CONF_UNITS]
        binary_sensors = device.get(CONF_BINARY_SENSORS)
        sensors = device.get(CONF_SENSORS)
        switches = device.get(CONF_SWITCHES)
        selectors =  device.get(CONF_SELECTOR)
        polling = device.get(CONF_POLLING)
        logging = device.get(CONF_LOG)
        zones = device.get(CONF_ZONES)
        gw = device.get(CONF_GW)
        if gw in dev_gateways:
            _LOGGER.error(f"Duplicate value of 'gw': {gw}")
            raise Exception(f"Duplicate value of 'gw': {gw}")
        if name in dev_names:
            _LOGGER.error(f"Duplicate value of 'name': {name}")
            raise Exception(f"Duplicate value of 'name': {name}")
        dev_gateways.add(gw)
        dev_names.add(name)

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
            selectors=selectors,
            polling=polling,
            logging=logging,
            gw=gw,
            zones=zones
        )

        api_list.append(api)
        # start api execution
        api.ariston_api.start()

        # load all devices
        hass.data[DATA_ARISTON][DEVICES][name] = AristonDevice(api, device)

        climate_entities = [name]
        if zones > 1:
            for zone in range(2, zones + 1):
                climate_entities.append(ZONE_NAME_TEMPLATE.format(name, zone))
                for param in ZONE_PARAMETERS:
                    if param in switches:
                        switches.append(ZONE_TEMPLATE.format(param, zone))
                    if param in sensors:
                        sensors.append(ZONE_TEMPLATE.format(param, zone))
                    if param in selectors:
                        selectors.append(ZONE_TEMPLATE.format(param, zone))
                    if param in binary_sensors:
                        binary_sensors.append(ZONE_TEMPLATE.format(param, zone))

        discovery.load_platform(hass, CLIMATE, DOMAIN, {CONF_NAME: name, CONF_CLIMATES: climate_entities}, config)

        discovery.load_platform(hass, WATER_HEATER, DOMAIN, {CONF_NAME: name}, config)

        if switches:
            discovery.load_platform(
                hass,
                SWITCH,
                DOMAIN,
                {CONF_NAME: name, CONF_SWITCHES: switches},
                config,
            )

        if selectors:
            discovery.load_platform(
                hass,
                SELECT,
                DOMAIN,
                {CONF_NAME: name, CONF_SELECTOR: selectors},
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
            
    gateways_txt = ", ".join(dev_gateways)
    names_txt = ", ".join(dev_names)
    _LOGGER.info(f"All gateways: {gateways_txt}")
    _LOGGER.info(f"All names: {names_txt}")

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

                params_to_set = {
                    PARAM_MODE,
                    PARAM_CH_MODE,
                    PARAM_CH_SET_TEMPERATURE,
                    PARAM_CH_COMFORT_TEMPERATURE,
                    PARAM_CH_ECONOMY_TEMPERATURE,
                    PARAM_CH_AUTO_FUNCTION,
                    PARAM_CH_WATER_TEMPERATURE,
                    PARAM_DHW_MODE,
                    PARAM_DHW_SET_TEMPERATURE,
                    PARAM_DHW_COMFORT_TEMPERATURE,
                    PARAM_DHW_ECONOMY_TEMPERATURE,
                    PARAM_DHW_COMFORT_FUNCTION,
                    PARAM_INTERNET_TIME,
                    PARAM_INTERNET_WEATHER,
                    PARAM_UNITS,
                    PARAM_THERMAL_CLEANSE_CYCLE,
                    PARAM_THERMAL_CLEANSE_FUNCTION,
                    PARAM_CH_FIXED_TEMP,
                }
                for param in ZONE_PARAMETERS:
                    if param in params_to_set:
                        for zone in range(2, 4):
                            params_to_set.add(ZONE_TEMPLATE.format(param, zone))
                

                for param in params_to_set:
                    data = call.data.get(param, "")
                    if data != "":
                        parameter_list[param] = str(data).lower()

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
