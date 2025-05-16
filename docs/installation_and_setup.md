# Installation

## Default Installation
The ORS plugin is available over the official [QGIS plugin repository](https://plugins.qgis.org/plugins/ORStools/) and is best installed from the QGIS built-in Plugin Manager.

## Development Installation
However, if you want or need to install the latest development version:
1. Download the ZIP archive from the [`main`](https://github.com/GIScience/orstools-qgis-plugin/tree/main) branch
2. Unzip and copy the folder `ORStools` into your system's QGIS plugin directory:
  - **Linux**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins`
  - **Windows**: `C:\Users\USER\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins`
  - **Mac OS**: `Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins`
3. Restart QGIS and if necessary, activate the ORS Tools plugin over the Plugin Manager.

# Setup

First, you'll have to [sign-up](https://openrouteservice.org/sign-up) and register your API key in your [dashboard](https://openrouteservice.org/dev/#/home).

In the configuration window (`Web` > `ORS Tools` > `Configuration`) you have set up the API key, which will be saved locally in a configuration file and will automatically be used across all tools. Here you can also set the base URL in case you're using a self-hosted ORS version and the requests per minute you're allocated (usually set to 40).

![ORS Tools config](/img/wiki_orstools_config.png)