# Consider donations to support Ukraine (where I'm from) to one of mentioned below or some other of your choosing
### Volunteering organization to help UA army
ICF COME BACK ALIVE
https://savelife.in.ua/en/donate-en/#desktop-donate-abroad-en

#### IBAN Code Euro (EUR)
UA093052990000026004025029786

#### IBAN Code US Dollar (USD)
UA173052990000026009035028620

#### IBAN Code Swedish Krona (SEC)
UA473052990000026009035019253

#### IBAN Code Polish Zloty (PLN)
UA933052990000026001045027448

#### IBAN Code Norwegian Krone (NOK)
UA173052990000026001005022621

#### IBAN Code Pound Sterling (GBP)
UA043052990000026002035022690

#### IBAN Code Czech Koruna (CZK)
UA503052990000026007015024657

#### IBAN Code Swiss Franc (CHF)
UA143052990000026009005017456

### UA army
https://bank.gov.ua/en/news/all/natsionalniy-bank-vidkriv-spetsrahunok-dlya-zboru-koshtiv-na-potrebi-armiyi


#### In order to pay UA Army in USD:
BENEFICIARY: National Bank of Ukraine
BENEFICIARY BIC: NBUA UA UX
BENEFICIARY ADDRESS: 9 Instytutska St, Kyiv, 01601, Ukraine
ACCOUNT NUMBER: 804790258
BENEFICIARY BANK NAME: JP MORGAN CHASE BANK, New York
BENEFICIARY BANK BIC: CHASUS33
ABA 0210 0002 1
BENEFICIARY BANK ADDRESS: 383 Madison Avenue, New York, NY 10017, USA
PURPOSE OF PAYMENT: for ac 47330992708 

#### In order to pay UA Army in EUR:
BENEFICIARY: National Bank of Ukraine
IBAN DE05504000005040040066
PURPOSE OF PAYMENT: for ac 47330992708
BENEFICIARY BANK NAME: DEUTSCHE  BUNDESBANK, Frankfurt
BENEFICIARY BANK BIC: MARKDEFF
BENEFICIARY BANK ADDRESS: Wilhelm-Epstein-Strasse 14, 60431 Frankfurt Am Main, Germany

#### In order to pay UA Army in GBP:
BENEFICIARY/RECIPIENT NAME: National Bank of Ukraine
ACCOUNT NUMBER: 80033041
IBAN GB52CHAS60924280033041
BENEFICIARY ADDRESS: 9 Instytutska St, Kyiv, 01601, Ukraine
BENEFICIARY BANK NAME: JP MORGAN CHASE BANK NA, London
BENEFICIARY BANK BIC: CHASGB2L
SORT CODE: 60-92-42 
BENEFICIARY BANK ADDRESS: 125 London Wall, London EC2Y 5AJ, UK
PURPOSE OF PAYMENT: for ac 47330992708 

#### In order to pay UA Army in AUD:
BENEFICIARY: National Bank of Ukraine
BENEFICIARY BIC: NBUA UA UX
BENEFICIARY ADDRESS: 9 Instytutska St, Kyiv, 01601, Ukraine
ACCOUNT NUMBER: 817532
BSB code 092-002
BENEFICIARY BANK NAME: RESERVE  BANK OF AUSTRALIA, Sydney
BENEFICIARY BANK BIC: RSBKAU2S
BENEFICIARY BANK ADDRESS: GPO Box 3947, Sydney NSW 2000, Australia
PURPOSE OF PAYMENT: for ac 47330992708 

#### In order to pay UA Army in CAD:
BENEFICIARY: National Bank of Ukraine
BENEFICIARY BIC: NBUA UA UX
BENEFICIARY ADDRESS: 9 Instytutska St, Kyiv, 01601, Ukraine
ACCOUNT NUMBER: 31441044166
BENEFICIARY BANK NAME: BANK OF MONTREAL, Toronto
BENEFICIARY BANK BIC: BOFMCAM2
BENEFICIARY BANK ADDRESS: 100 King Street West, Toronto, Ontario, M5X 1A9, Canada
PURPOSE OF PAYMENT: for ac 47330992708 

#### In order to pay UA Army in PLN:
BENEFICIARY: National Bank of Ukraine
BENEFICIARY BIC: NBUA UA UX
BENEFICIARY ADDRESS: 9 Instytutska St, Kyiv, 01601, Ukraine
ACCOUNT NUMBER: PL91113000070080239435200002
BENEFICIARY BANK NAME: Bank Gospodarstwa Krajowego
BENEFICIARY BANK BIC: GOSKPLPW
BENEFICIARY BANK ADDRESS: Al. Jerozolimskie 7, 00-955 Warszawa, Polska (temporary address: Chmielna 73, 00-801 Warszawa, Polska)
PURPOSE OF PAYMENT: for ac 47330992708
<br/>
<br/>
<br/>

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
  - Ariston Alteas One (note that `internet_weather` is not supported by this model and must not be included in switches or binary sensors)

## Integration was tested and does not work with:
  - Ariston Lydos. use https://github.com/chomupashchuk/ariston-aqua-remotethermo-home-assistant instead.
  - Ariston Velis. use https://github.com/chomupashchuk/ariston-aqua-remotethermo-home-assistant instead.
  - Ariston Lydos Hybrid. use https://github.com/chomupashchuk/ariston-aqua-remotethermo-home-assistant instead.

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
All optional attributes are described in **Integration attributes**\
Order of Installation:
- Copy data to `custom_components`;
- Restart Home Assistant to find the component;
- Include data in `configuration.yaml`;
- Restart Home Asistant to see new services.

### Integration attributes
  - `username` - **mandatory** user name used in https://www.ariston-net.remotethermo.com
  - `password` - **mandatory** password used in https://www.ariston-net.remotethermo.com
    **! It is recommended for security purposes to not use your common password, just in case !**
  - `name` - friendly name for integration, default is `Ariston`
  - `logging` - sets logging level (`CRITICAL`, `ERROR`, `WARNING`, `INFO`, `DEBUG`, `NOTSET`). Default is `WARNING`.
  - `period_set` - period in seconds between requests to read sensor values (integer, minimum is `30`). Default is `30`.
  - `period_get`- period in seconds between requests to set sensor values (integer, minimum is `30`). Default is `30`.
  - `max_set_retries` - attempts to set the value until giving up setting the value. Default is `5`.
  - `num_ch_zones` - number of CH zones (`1`-`6`). Default is `1`.

#### Switches
**Some parameters are not supported on all models**
  - `internet_time` - turn off and on sync with internet time.
  - `internet_weather` - turn off and on fetching of weather from internet. **WORKS ONLY ON SPECIFIC MODELS WHILE ON OTHERS CAUSES CRASHES**
  - `ch_auto_function` - turn off and on Auto function.
  - `dhw_thermal_cleanse_function` - DHW thermal cleanse function enabled.

#### Selectors
**Some parameters are not supported on all models**
  - `mode` - mode of boiler (`off` or `summer` or `winter` and others).
  - `ch_mode` - mode of CH (`manual` or `scheduled` and others).
  - `dhw_mode` - mode of DHW. Not supported on all models.
  - `dhw_comfort_function` - DHW comfort function.
  - `ch_set_temperature` - set CH temperature.
  - `ch_comfort_temperature` - CH comfort temperature.
  - `ch_economy_temperature` - CH economy temperature.
  - `ch_water_temperature` - CH Water Temperature. **WORKS ONLY ON SPECIFIC MODELS WHILE ON OTHERS CAUSES CRASHES**
  - `ch_fixed_temperature` - CH Fixed Temperature.
  - `dhw_set_temperature` - set DHW temperature.
  - `dhw_comfort_temperature` - DHW storage comfort temperature. Not supported on all models.
  - `dhw_economy_temperature` - DHW storage economy temperature. Not supported on all models.

#### Sensors
**Some parameters are not supported on all models**
  - `ch_antifreeze_temperature` - CH antifreeze temperature.
  - `ch_detected_temperature` - temperature measured by thermostat.
  - `ch_mode` - mode of CH (`manual` or `scheduled` and others).
  - `ch_comfort_temperature` - CH comfort temperature.
  - `ch_economy_temperature` - CH economy temperature.
  - `ch_set_temperature` - set CH temperature.
  - `ch_program` - CH Time Program.
  - `ch_water_temperature` - CH Water Temperature. **WORKS ONLY ON SPECIFIC MODELS WHILE ON OTHERS CAUSES CRASHES**
  - `ch_fixed_temperature` - CH Fixed Temperature.
  - `ch_flow_temperature` - CH Flow Setpoint Temperature.
  - `dhw_program` - DHW Time Program.
  - `dhw_comfort_function` - DHW comfort function.
  - `dhw_mode` - mode of DHW. Not supported on all models.
  - `dhw_comfort_temperature` - DHW storage comfort temperature. Not supported on all models.
  - `dhw_economy_temperature` - DHW storage economy temperature. Not supported on all models.
  - `dhw_set_temperature` - set DHW temperature.
  - `dhw_storage_temperature` - DHW storage temperature. Not supported on all models.
  - `dhw_thermal_cleanse_cycle` - DHW thermal cleanse cycle.
  - `errors_count` - active errors (no actual errors to test on).
  - `mode` - mode of boiler (`off` or `summer` or `winter` and others).
  - `outside_temperature` - outside temperature. Not supported on all models.
  - `pressure` - Water Pressure.
  - `signal_strength` - Wifi signal strength.
  - `units` - Units of measurement.
  - `ch_gas_last_month` - gas use last month for CH.
  - `ch_electricity_last_month` - electricity use last month for CH.
  - `dhw_gas_last_month` - gas use last month for DHW.
  - `dhw_electricity_last_month` - electricity use last month for DHW.
  - `ch_energy_today` - Energy use for CH today (matches values in application for some models, unavailable for other models)
  - `ch_energy_yesterday` - Energy use for CH yesterday (matches values in application for some models, unavailable for other models)
  - `dhw_energy_today` - Energy use for DHW today (matches values in application for some models, unavailable for other models)
  - `dhw_energy_yesterday` - Energy use for DHW yesterday (matches values in application for some models, unavailable for other models)
  - `ch_energy_last_7_days` - Energy use for CH last 7 days (matches values in application for some models, unavailable for other models)
  - `dhw_energy_last_7_days` - Energy use for DHW last 7 days (matches values in application for some models, unavailable for other models)
  - `ch_energy_this_month` - Energy use for CH this month (matches values in application for some models, unavailable for other models)
  - `ch_energy_last_month` - Energy use for CH last month (matches values in application for some models, unavailable for other models)
  - `dhw_energy_this_month` - Energy use for DHW this month (matches values in application for some models, unavailable for other models)
  - `dhw_energy_last_month` - Energy use for DHW last month (matches values in application for some models, unavailable for other models)
  - `ch_energy_this_year` - Energy use for CH this year (matches values in application for some models, unavailable for other models)
  - `ch_energy_last_year` - Energy use for CH last year (matches values in application for some models, unavailable for other models)
  - `dhw_energy_this_year` - Energy use for DHW this year (matches values in application for some models, unavailable for other models)
  - `dhw_energy_last_year` - Energy use for DHW last year (matches values in application for some models, unavailable for other models)
  - `ch_energy2_today` - Energy use for CH today (has additional energy use compared to energy sensor (unknow what it is) and only viable option for other models)
  - `ch_energy2_yesterday` - Energy use for CH yesterday (has additional energy use compared to energy sensor (unknow what it is) and only viable option for other models)
  - `dhw_energy2_today` - Energy use for DHW today (has additional energy use compared to energy sensor (unknow what it is) and only viable option for other models)
  - `dhw_energy2_yesterday` - Energy use for DHW yesterday (has additional energy use compared to energy sensor (unknow what it is) and only viable option for other models)
  - `ch_energy2_last_7_days` - Energy use for CH last 7 days (has additional energy use compared to energy sensor (unknow what it is) and only viable option for other models)
  - `dhw_energy2_last_7_days` - Energy use for DHW last 7 days (has additional energy use compared to energy sensor (unknow what it is) and only viable option for other models)
  - `ch_energy2_this_month` - Energy use for CH this month (has additional energy use compared to energy sensor (unknow what it is) and only viable option for other models)
  - `ch_energy2_last_month` - Energy use for CH last month (has additional energy use compared to energy sensor (unknow what it is) and only viable option for other models)
  - `dhw_energy2_this_month` - Energy use for DHW this month (has additional energy use compared to energy sensor (unknow what it is) and only viable option for other models)
  - `dhw_energy2_last_month` - Energy use for DHW last month (has additional energy use compared to energy sensor (unknow what it is) and only viable option for other models)
  - `ch_energy2_this_year` - Energy use for CH this year (has additional energy use compared to energy sensor (unknow what it is) and only viable option for other models)
  - `ch_energy2_last_year` - Energy use for CH last year (has additional energy use compared to energy sensor (unknow what it is) and only viable option for other models)
  - `dhw_energy2_this_year` - Energy use for DHW this year (has additional energy use compared to energy sensor (unknow what it is) and only viable option for other models)
  - `dhw_energy2_last_year` - Energy use for DHW last year (has additional energy use compared to energy sensor (unknow what it is) and only viable option for other models)
  - `ch_energy_delta_today` - Energy use for CH today some extra anargy (difference between energy and energy2 for models that have both values)
  - `ch_energy_delta_yesterday` - Energy use for CH yesterday some extra anargy (difference between energy and energy2 for models that have both values)
  - `dhw_energy_delta_today` - Energy use for DHW today some extra anargy (difference between energy and energy2 for models that have both values)
  - `dhw_energy_delta_yesterday` - Energy use for DHW yesterday some extra anargy (difference between energy and energy2 for models that have both values)
  - `ch_energy_delta_last_7_days` - Energy use for CH last 7 days some extra anargy (difference between energy and energy2 for models that have both values)
  - `dhw_energy_delta_last_7_days` - Energy use for DHW last 7 days some extra anargy (difference between energy and energy2 for models that have both values)
  - `ch_energy_delta_this_month` - Energy use for CH this month some extra anargy (difference between energy and energy2 for models that have both values)
  - `ch_energy_delta_last_month` - Energy use for CH last month some extra anargy (difference between energy and energy2 for models that have both values)
  - `dhw_energy_delta_this_month` - Energy use for DHW this month some extra anargy (difference between energy and energy2 for models that have both values)
  - `dhw_energy_delta_last_month` - Energy use for DHW last month some extra anargy (difference between energy and energy2 for models that have both values)
  - `ch_energy_delta_this_year` - Energy use for CH this year some extra anargy (difference between energy and energy2 for models that have both values)
  - `ch_energy_delta_last_year` - Energy use for CH last year some extra anargy (difference between energy and energy2 for models that have both values)
  - `dhw_energy_delta_this_year` - Energy use for DHW this year some extra anargy (difference between energy and energy2 for models that have both values)
  - `dhw_energy_delta_last_year` - Energy use for DHW last year some extra anargy (difference between energy and energy2 for models that have both values)
  - `integration_version` - version of the integration

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
  - `internet_weather` - Internet weather status. **WORKS ONLY ON SPECIFIC MODELS WHILE ON OTHERS CAUSES CRASHES**
  - `changing_data` - API is attempting to configure requested data. **API specific sensor**.
  - `online` - Online status. Indicates if API has communication with the heater. **API specific sensor**.


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
  selector:
    - mode
    - ch_mode
```

## Multiple boilers under one account setup
Multiple boilers can exist under one account and by default first gateway is used to connect to appropriate boiler, so in case of multiple boilers each gateway must be specified individually.

### Multiple boilers Gateways collection
Perform actions in the following order:
  - Login to https://www.ariston-net.remotethermo.com/
  - Click on `MANAGE APPLIANCES` or similar (where all appliances are listed)
  - In the list of devices click on each radio button on the left side, and for each selected device note gateway number in the URL. For example the First device in the list is selected, then URL should look something like `https://www.ariston-net.remotethermo.com/PlantManagement/Index/[GAETWAYNUMBER]>`, note `GAETWAYNUMBER`, which corresponds to device selected. Then select the Second device, note URL change and save new `GAETWAYNUMBER`.

### Example with 4 boilers (2 ariston and 2 aquaariston) with minimal configuration
```
ariston:
  - name: boiler_1_name
    gw: "BOILER1GW"                         # See GAETWAYNUMBER fetching
    username: !secret ariston_username
    password: !secret ariston_password
    selector:
      - mode

  - name: boiler_2_name
    gw: "BOILER2GW"                         # See GAETWAYNUMBER fetching
    username: !secret ariston_username
    password: !secret ariston_password
    sensors:
      - mode

aquaariston:
  - name: boiler_3_name
    gw: "BOILER3GW"                         # See GAETWAYNUMBER fetching
    username: !secret ariston_username
    password: !secret ariston_password
    type: "velis"
    switches:
      - power

  - name: boiler_4_name
    gw: "BOILER4GW"                         # See GAETWAYNUMBER fetching
    username: !secret ariston_username
    password: !secret ariston_password
    type: "lydos"
    selector:
      - mode

```
In example there are 4 devices, for which `GAETWAYNUMBER` was fetched manually and is used as value for `gw` parameter. Parameter `name` must be unique (could be based on `Nickname` from Ariston URL or selected randomly). Gateway must be selected according to integration (see details per integration, which boilers it supports). Sensors, switches, binary sensors and selectors can be specified under each boiler individually. Integration attempts to check for supported gateways when one is specified, and logs corresponding events in case gateway is not found in parsed HTML body.


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
