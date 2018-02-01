# BountyTools Client
This client will be placed on any host intended to execute BountyTools plugins. It will present a simple REST API that allows the BountyTools Platform to interact with it and its plugins. Each plugin is written as a library to be imported by the bountytools_client listener.

## Plugin Design
Each plugin is a Python module to be imported. Every plugin module presents all functionality as an API. Included in the plugin is all logic required to setup the external software required to run the plugin.