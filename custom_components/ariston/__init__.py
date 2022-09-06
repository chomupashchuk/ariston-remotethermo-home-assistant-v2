"""Suppoort for Ariston."""
import logging
import re

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
from .const import param_zoned

from .binary_sensor import binary_sensors_default
from .const import (
    DOMAIN,
    DATA_ARISTON,
    DEVICES,
    SERVICE_SET_DATA,
    CLIMATES,
    WATER_HEATERS,
    CONF_LOG,
    CONF_GW,
    CONF_PERIOD_SET,
    CONF_PERIOD_GET,
    CONF_MAX_SET_RETRIES,
    CONF_CH_ZONES,
    ZONED_PARAMS,
    PARAM_CH_MODE,
    PARAM_CH_SET_TEMPERATURE,
    PARAM_CH_WATER_TEMPERATURE,
    PARAM_DHW_COMFORT_FUNCTION,
    PARAM_DHW_SET_TEMPERATURE,
    PARAM_MODE,
    PARAM_THERMAL_CLEANSE_CYCLE,
    PARAM_CH_AUTO_FUNCTION,
    PARAM_INTERNET_TIME,
    PARAM_INTERNET_WEATHER,
    PARAM_ONLINE,
    PARAM_CHANGING_DATA,
    PARAM_VERSION,
    PARAM_THERMAL_CLEANSE_FUNCTION,
)
from .sensor import sensors_default
from .switch import switches_default
from .select import selects_deafult

DEFAULT_NAME = "Ariston"
DEFAULT_MAX_RETRIES = 5
DEFAULT_PERIOD_GET = 30
DEFAULT_PERIOD_SET = 30

_LOGGER = logging.getLogger(__name__)

ARISTON_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_GW, default=""): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_BINARY_SENSORS): vol.All(
            cv.ensure_list, [vol.In(binary_sensors_default)]
        ),
        vol.Optional(CONF_SENSORS): vol.All(cv.ensure_list, [vol.In(sensors_default)]),

        vol.Optional(CONF_MAX_SET_RETRIES, default=DEFAULT_MAX_RETRIES): vol.All(
            int, vol.Range(min=1, max=10)
        ),
        vol.Optional(CONF_SWITCHES): vol.All(cv.ensure_list, [vol.In(switches_default)]),
        vol.Optional(CONF_SELECTOR): vol.All(cv.ensure_list, [vol.In(selects_deafult)]),

        vol.Optional(CONF_PERIOD_GET, default=DEFAULT_PERIOD_GET): vol.All(
            int, vol.Range(min=30, max=3600)
        ),
        vol.Optional(CONF_PERIOD_SET, default=DEFAULT_PERIOD_SET): vol.All(
            int, vol.Range(min=30, max=3600)
        ),
        vol.Optional(CONF_LOG, default="WARNING"): vol.In(
            ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]
        ),
        vol.Optional(CONF_CH_ZONES, default=1): vol.All(
            int, vol.Range(min=1, max=6)
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
        sensors,
        binary_sensors,
        switches,
        selectors,
        logging,
        gw,
        period_set,
        period_get,
        retries
    ):
        """Initialize."""

        self.device = device
        self._hass = hass
        self.name = name

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
        if PARAM_VERSION in list_of_sensors:
            list_of_sensors.remove(PARAM_VERSION)

        self.ariston_api = AristonHandler(
            username=username,
            password=password,
            sensors=list_of_sensors,
            logging_level=logging,
            gw=gw,
            set_max_retries=retries,
            period_get_request=period_get,
            period_set_request=period_set
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
        gw = device.get(CONF_GW)
        username = device[CONF_USERNAME]
        password = device[CONF_PASSWORD]
        binary_sensors = device.get(CONF_BINARY_SENSORS)
        sensors = device.get(CONF_SENSORS)
        switches = device.get(CONF_SWITCHES)
        selectors =  device.get(CONF_SELECTOR)
        num_ch_zones = device.get(CONF_CH_ZONES)
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
            sensors=sensors,
            binary_sensors=binary_sensors,
            switches=switches,
            selectors=selectors,
            gw=gw,
            logging=device.get(CONF_LOG),
            period_set=device.get(CONF_PERIOD_SET),
            period_get=device.get(CONF_PERIOD_GET),
            retries=device.get(CONF_MAX_SET_RETRIES)
        )

        api_list.append(api)
        # start api execution
        api.ariston_api.start()

        climates = []
        for zone in range(1, num_ch_zones + 1):
            climates.append(f'{name} Zone{zone}')
        
        def update_list(updated_list):
            if updated_list:
                if param in updated_list:
                    updated_list.remove(param)
                    for zone in range(1, num_ch_zones + 1):
                        updated_list.append(param_zoned(param, zone))
        params_temp = set()
        if sensors:
            params_temp.update(sensors)
        if binary_sensors:
            params_temp.update(binary_sensors)
        if switches:
            params_temp.update(switches)
        if selectors:
            params_temp.update(selectors)
        params = params_temp.intersection(ZONED_PARAMS)
        for param in params:
            update_list(switches)
            update_list(binary_sensors)
            update_list(sensors)
            update_list(selectors)

        # load all devices
        hass.data[DATA_ARISTON][DEVICES][name] = AristonDevice(api, device)
        discovery.load_platform(hass, CLIMATE, DOMAIN, {CONF_NAME: name, CLIMATES: climates}, config)
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
            api_name = api.name.replace(' ', '_').lower()
            if re.search(f'{api_name}_zone[1-9]$', device_id.lower()) or api_name == device_id.lower():
                # climate entity is found
                parameter_list = {}

                params_to_set = {
                    PARAM_MODE,
                    PARAM_CH_MODE,
                    PARAM_CH_SET_TEMPERATURE,
                    PARAM_CH_AUTO_FUNCTION,
                    PARAM_CH_WATER_TEMPERATURE,
                    PARAM_DHW_SET_TEMPERATURE,
                    PARAM_DHW_COMFORT_FUNCTION,
                    PARAM_THERMAL_CLEANSE_CYCLE,
                    PARAM_THERMAL_CLEANSE_FUNCTION,
                    PARAM_INTERNET_TIME,
                    PARAM_INTERNET_WEATHER,
                }
                
                set_zoned_params = []
                for param in params_to_set:
                    if param in ZONED_PARAMS:
                        for zone in range(1, 7):
                            set_zoned_params.append(param_zoned(param, zone))
                    else:
                        set_zoned_params.append(param)

                for param in set_zoned_params:
                    data = call.data.get(param, "")
                    if data != "":
                        parameter_list[param] = str(data)

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
