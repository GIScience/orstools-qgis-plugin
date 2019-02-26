# ORS Tools QGIS plugin

**Note, only QGIS v3.x is supported.**

Set of tools to use [openrouteservice](https://openrouteservice.org) (ORS) API's in QGIS.

ORS Tools gives you easy access to the following API's:

- [Directions](https://openrouteservice.org/documentation/#/reference/directions/directions/directions-service)
- [Isochrones](https://openrouteservice.org/documentation/#/reference/isochrones/isochrones/isochrones-service)
- [Matrix](https://openrouteservice.org/documentation/#/reference/matrix/matrix/matrix-service-(post))

The [wiki](https://github.com/nilsnolde/ORStools/wiki/ORS-Tools-Help) offers a tutorial on usage.

In case of issues/bugs, please use the [issue tracker](https://github.com/nilsnolde/ORStools/issues).

In case of questions, please ask our [forum](https://ask.openrouteservice.org/c/sdks).

See also:
- [Rate limits](https://openrouteservice.org/restrictions/)
- Developer [dashboard](https://openrouteservice.org/dev/#/home)
- [ORS developer documentation](https://openrouteservice.org/documentation/)
- ORS openrouteservice-py on [PyPi](https://pypi.python.org/pypi/openrouteservice)
- ORS Tools plugin in [QGIS repo](https://plugins.qgis.org/plugins/OSMtools/)

## Functionalities

### General

Use QGIS to generate input for **routing**, **isochrones** and **matrix calculations** powered by ORS.

It offers either a GUI in the Web menu and toolbar of QGIS to interactively use the API's from the map canvas.

For batch operations you can find a ORS toolbox in the Processing toolbox.

### Customization

You'll have to get an API key first: <https://openrouteservice.org/sign-up>.

Additionally you can register your other providers, e.g. if you're hosting a custom ORS backend.

Configuration takes place either from the Web menu entry *ORS Tools* ► *Provider settings*. Or from *Config* button in the GUI.

## Getting Started

### Prerequisites

QGIS versin: min. **v3.0**

API key: https://openrouteservice.org/sign-up/

### Installation

Either from QGIS plugin repository or manually:
  - [Download](https://github.com/nilsnolde/OSMtools/archive/master.zip) ZIP file from Github
  - Unzip folder contents and copy `ORStools` folder to:
    - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins`
    - Windows: `C:\Users\USER\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins`
    - Mac OS: `Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins`

## License

This project is published under the GPLv3 license, see [LICENSE.md](https://github.com/nilsnolde/ORStools/blob/master/LICENSE.md) for details.

By using this plugin, you also agree to the terms and conditions of OpenRouteService, as outlined [here](https://openrouteservice.org/terms-of-service/).
