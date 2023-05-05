# aprilaire-ha

aprilaire-ha is a custom integration for [Home Assistant](https://www.home-assistant.io/) to interact with Aprilaire thermostats. This integration uses the [pyaprilaire](https://github.com/chamberlain2007/pyaprilaire) library.

# Compatibility

aprilaire-ha is generally compatible with Aprilaire [Home Automation](https://www.aprilairepartners.com/technical-information-options/home-automation-technical-information) 8800-series and [Zone Control](https://www.aprilairepartners.com/technical-information-options/zoning-technical-information) 6000-series thermostats. However, due to the number of physical models, it has not been tested on all models.

# Prerequisites

In order to connect to the thermostat, you will need to enable automation mode. This involves going into the Contractor Menu on your thermostat and changing the Connection Type to Automation. Please look up the instructions for your model, as this can vary between models.

# Installation

## HACS (preferred)
Add the respository URL as a custom [repository integration](https://hacs.xyz/docs/faq/custom_repositories).

## Manual
Copy the aprilaire folder from this repo to config/custom_components (create custom_components folder if it doesn't exist already)

## Setup
Once aprilaire-ha is installed, you can set it up by adding it as an integration.  You'll need to know the IP Address of thermostat and the port (defaults to 7000). This is typically port 7000 for 6000-series, and 8000 for 8800-series thermostats. It is recommended to assign a static IP to the thermostat, as the integration cannot automatically pick up changes to your thermostat's IP.

# Supported functionality

Currently, the integration supports the following interactions with the thermostat. Note that some functions require specific sensors and components to be installed in the system. Functions that are not supported by the system will generally not be displayed.

- View the current indoor and outdoor temperature and humidity
- View the current system status (heating, cooling, idle)
- View and change the HVAC mode (heat, cool, auto, off)
- View and change the heat/cool setpoint
- View and change the humidification/dehumidification setpoint (only humidity is shown visually in the Home Assistant climate card)
- Trigger and cancel air cleaning and fresh air events
- View and change the hold type (away, vacation, temporary/permanent hold when activated by changing the setpoint)
- View and change the fan mode (on, auto, circulate)
- View the statuses of the air cleaning, humidifier, dehumidifier, fan and ventilation systems

# Development

## Mock server

During development, it is necessary to connect to a thermostat, but this can be problematic as a thermostat only allows a single connection at a time. There is a mock server that can be run to expose a local server for development that emulates a thermostat.

Install [pyaprilaire](https://pypi.org/project/pyaprilaire/) with pip:

```
python -m pip install pyaprilaire
```

Run the mock server:

```
python -m pyaprilaire.mock_server
```

The port can be specified with `-p PORT_NUMBER`. The default port is 7001.

# Caution regarding device limitations

Due to limitations of the thermostats, only one home automation connection to a device is permitted at one time (the Aprilaire app is not included in this limitation as it uses a separate protocol). Attempting to connecting multiple times to the same thermostat simultaneously can cause various issues, including the thermostat becoming unresponsive and shutting down. If this does occur, power cycling the thermostat should restore functionality.

The socket that is exposed by the thermostat can be unreliable in general. In some cases, it can silently drop the connection or otherwise stop responding. The integration handles this by quietly disconnecting and reconnecting every hour, which generally improves stability. In some cases, however, there may be periods where the change of state (COS) packets aren't received, potentially causing stale data to be shown until the connection is reset. *If this happens to you frequently and you are able to capture the packets at the time via Wireshark showing the state of the socket, this data would be valuable to share.*