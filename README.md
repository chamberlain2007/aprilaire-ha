# aprilaire-ha

aprilaire-ha is a custom integration for [Home Assistant](https://www.home-assistant.io/) to interact with Aprilaire thermostats.

# Compatibility

aprilaire-ha is compatible with many models of Aprilaire thermostats. It is tested with an Aprilaire 6045m, but it should work with other 6000- and 8000-series thermostats.

# Prerequisites

In order to connect to the thermostat, you will need to enable automation mode. This involves going into the Contractor Menu on your thermostat and changing the Connection Type to Automation. Please look up the instructions for your model, as this can vary between models.

# Installation

## HACS (preferred)
Add the respository URL as a custom [repository integration](https://hacs.xyz/docs/faq/custom_repositories).

## Manual
Copy the aprilaire folder from this repo to config/custom_components (create custom_components folder if it doesn't exist already)

## Setup
Once aprilaire-ha is installed, you can set it up by adding it as an integration.  You'll need to know the IP Address of thermostat and the port (defaults to 7000 which is the standard port). It is recommended to assign a static IP to the thermostat.

# Supported functionality

Currently, the integration supports creating a climate entity in Home Assistant, which has the ability to view current temperature and humidity, viewing and changing the HVAC mode (heat, cool, auto, off), and setting the heat/cool setpoint.

Further support for additional sensors is planned.

# Development

## Mock server

During development, it is necessary to connect to a thermostat, but this can be problematic as a thermostat only allows a single connection at a time. There is a mock server that can be run to expose a local server for development that emulates a thermostat.

From within the `custom_components/aprilaire` directory:

```
python3 -m aprilaire.mock_server
```

The port can be specified with `-p PORT_NUMBER`. The default port is 7001.