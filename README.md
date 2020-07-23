# Ariston NET remotethermo integration for Home Assistant
Thin integration is a side project which works only with 1 zone climate configured. It logs in to Ariston website (https://www.ariston-net.remotethermo.com) and fetches/sets data on that site.
You are free to modify and distribute it. It is distributed 'as is' with no liability for possible damage.
Cimate has presets to switch between `off`, `summer` and `winter` in order to be able to control boiler from one entity.

## Donations
If you like this app, please consider donating some sum to your local charity organizations or global organization like Red Cross. I don't mind receiving donations myself (you may conact me for more details if you want to), but please consider charity at first.

## Integration slow nature
Intergation uses api developed by me based on assumptions and test results. It continiously fetches the data from the site with periods determined during tests to have not as many interference with other applications (like Ariston NET application or Google Home application) but be quick enough to get information as soon as possible.
You may read more about API (`ariston.py`) on the website: https://pypi.org/project/aristonremotethermo/.

## Integration was tested on and works with:
  - Ariston Clas Evo
  - Ariston Genus One with Ariston BCH cylinder
  - Ariston Nimbus Flex

## Integration was tested and does not work with:
  - Ariston Lydos Wifi. use https://github.com/chomupashchuk/ariston-aqua-remotethermo-home-assistant instead.
  - Ariston Velis Wifi. use https://github.com/chomupashchuk/ariston-aqua-remotethermo-home-assistant instead.

## How to check if intergation supports your model
You may check possible support of your boiler by logging into https://www.ariston-net.remotethermo.com and if climate and water heater parts (like temperatures) are available on the home page, then intergation should potentially work.

## Integration installation
In `/config` folder create `custom_components` folder and folder `ariston` with its contents in it.
In `configuration.yaml` include:
```
ariston:
  username: !secret ariston_username
  password: !secret ariston_password
```
All optional attributes are described in **Integration attributes**

### Integration attributes
  - `username` - **mandatory** user name used in https://www.ariston-net.remotethermo.com
  - `password` - **mandatory** password used in https://www.ariston-net.remotethermo.com
    **! It is recommended for security purposes to not use your common password, just in case !**
  - `name` - friendly name for integration, default is `Ariston`
  - `hvac_off_present` - indicates if `HVAC OFF` shall be present in climate entity. Default value is `false`.
  - `hvac_off` - indicates how to treat `HVAC OFF` action in climate (use depends on `hvac_off_present`). Options are `off` and `summer`. By default it is `summer`, which means that turning off would keep DHW water heating on (e.g. summer mode). Presets in climate allow switching between `off`, `summer` and `winter`.
  - `store_config_files` - `true` or `false` indicating if configuration `json` files to be stored in `/config/custom_components/ariston` folder. Can be used for troubleshooting purposes. Default value is `false`.
  - `units` - which uniots to be used. Values are: `metric` (°C-bar-kW...), `imperial` (°F-psi-kBtu/h...), `auto` (detect automatically, which takes additional time). Default is `metric`. Note that use of `auto` requires additional request to be used, which would result in slower update of other sensors.

#### Switches
**Some parameters are not supported on all models**
  - `internet_time` - turn off and on sync with internet time.
  - `internet_weather` - turn off and on fetching of weather from internet.
  - `ch_auto_function` - turn off and on Auto function.
  - `dhw_thermal_cleanse_function` - DHW thermal cleanse function enabled.

#### Sensors
**Some parameters are not supported on all models**
  - `account_ch_gas` - gas use summary for CH. Not supported on all models.
  - `account_ch_electricity` - electricity use summary for CH. Not supported on all models.
  - `account_dhw_gas` - gas use summary for DHW. Not supported on all models.
  - `account_dhw_electricity` - electricity use summary for DHW. Not supported on all models.
  - `ch_antifreeze_temperature` - CH antifreeze temperature.
  - `ch_detected_temperature` - temperature measured by thermostat.
  - `ch_mode` - mode of CH (`manual` or `scheduled` and others).
  - `ch_comfort_temperature` - CH comfort temperature.
  - `ch_economy_temperature` - CH economy temperature.
  - `ch_set_temperature` - set CH temperature.
  - `ch_program` - CH Time Program.
  - `dhw_program` - DHW Time Program.
  - `dhw_comfort_function` - DHW comfort function.
  - `dhw_mode` - mode of DHW. Not supported on all models.
  - `dhw_comfort_temperature` - DHW storage comfort temperature. Not supported on all models.
  - `dhw_economy_temperature` - DHW storage economy temperature. Not supported on all models.
  - `dhw_set_temperature` - set DHW temperature.
  - `dhw_storage_temperature` - DHW storage temperature. Not supported on all models.
  - `dhw_thermal_cleanse_cycle` - DHW thermal cleanse cycle.
  - `electricity_cost` - Electricity cost.
  - `errors_count` - active errors (no actual errors to test on).
  - `gas_type` - Gas type.
  - `gas_cost` - Gas cost.
  - `heating_last_24h` - energy use for heating in last 24 hours. Not supported on all models.
  - `heating_last_30d` - energy use for heating in last 7 days. Not supported on all models.
  - `heating_last_365d` - energy use for heating in last 30 days. Not supported on all models.
  - `heating_last_7d` - energy use for heating in last 365 days. Not supported on all models.
  - `mode` - mode of boiler (`off` or `summer` or `winter` and others).
  - `outside_temperature` - outside temperature. Not supported on all models.
  - `signal_strength` - Wifi signal strength.
  - `units` - Units of measurement
  - `water_last_24h` - energy use for water in last 24 hours. Not supported on all models.
  - `water_last_30d` - energy use for water in last 7 days. Not supported on all models.
  - `water_last_365d` - energy use for water in last 30 days. Not supported on all models.
  - `water_last_7d` - energy use for water in last 365 days. Not supported on all models.

#### Binary sensors
**Some parameters are not supported on all models**
  - `ch_auto_function` - CH AUTO function status.
  - `ch_flame` - CH heating ongoing.
  - `ch_pilot` - CH Pilot mode.
  - `dhw_flame` - DHW heating ongoing. **This parameter is not reported by boilers and is approximated based on multiple parameters**.
  - `dhw_thermal_cleanse_function` - DHW thermal cleanse function.
  - `flame` - CH and/or DHW heating ongoing.
  - `heat_pump` - Heating pump status.
  - `holiday_mode` - Holiday mode status.
  - `internet_time` - Internet time status.
  - `internet_weather` - Internet weather status.
  - `changing_data` - API is attempting to configure requested data. **API specific sensor**.
  - `online` - Online status. Indicates if API has communication with the heater. **API specific sensor**.
  - `update` - API update status. **API specific sensor**.


### Example of configuration.yaml entry
```
ariston:
  username: !secret ariston_user
  password: !secret ariston_password
  switches:
    - internet_time
    - internet_weather
  sensors:
    - ch_detected_temperature
    - ch_mode
    - ch_comfort_temperature
    - ch_economy_temperature
    - ch_set_temperature
    - dhw_set_temperature
    - errors_count
    - mode
    - outside_temperature
  binary_sensors:
    - changing_data
    - online
```

## Services
`ariston.set_data` - Sets the requested data.

### Service attributes:
- `entity_id` - **mandatory** entity of Ariston `climate`.
- for the rest of attributes please see `Developer Tools` tab `Services` within Home Assistant and select `ariston.set_data`. You may also directly read `services.yaml` within the `ariston` folder.

### Service use example
```
service: ariston.set_data
data:
    entity_id: 'climate.ariston'
    ch_comfort_temperature: 20.5
```

## Some known issues and workarounds

### Climate and water_heater entity become unavailable
Since integration interacts with server, which interacts with boiler directly or via gateway, it is possible that some link in the chain is not working. Integration is designed to constantly retry the connection (requests are sent more reearely in case of multiple faults to reduce load on whole chain). Mostly connection recovers in time, but sometimes restart of router or boiler can help (but not always).

### Only part of data becomes unavailable after it was available
Even though many functions are not accessible via integration once boiler configuration (parameter 228 in the menu) changed from 1 (boiler with water heater sensor) to 0 (default configuration without sensor), possibly due to packets corruption on the way or some specific bit sequence. It caused Genus One model not being able to handle DHW. The solution is to enter boiler menu directly and change the value of parameter 228.
Also boiler might require restart (complete loss of power).

### Unexpected status or temperature reported
For example CH temperature set to 0, which is not in supported range. Try to log in into https://www.ariston-net.remotethermo.com and change the value there. If it does not help try disconnecting heater from electricity and connecting again.
