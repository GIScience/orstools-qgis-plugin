# OSM tools
**Note, only QGIS v3.x is supported.**

Set of tools to use [openrouteservice](https://openrouteservice.org) (ORS) API's as a plugin in QGIS.

OSM Tools gives you easy access to the following API's:

- [Directions](https://openrouteservice.org/documentation/#/reference/directions/directions/directions-service)
- [Isochrones](https://openrouteservice.org/documentation/#/reference/isochrones/isochrones/isochrones-service)
- [Matrix](https://openrouteservice.org/documentation/#/reference/matrix/matrix/matrix-service-(post))

In case of issues/bugs, please use the [issue tracker](https://github.com/nilsnolde/OSMtools/issues).

In case of questions, please ask our [forum](https://ask.openrouteservice.org/c/sdks).

See also:
- [Rate limits](https://openrouteservice.org/restrictions/)
- Developer [dashboard](https://openrouteservice.org/dev/#/home)
- [ORS developer documentation](https://openrouteservice.org/documentation/)
- ORS openrouteservice-py on [PyPi](https://pypi.python.org/pypi/openrouteservice)
- OSM Tools plugin in [QGIS repo](https://plugins.qgis.org/plugins/OSMtools/)

## Functionalities

### General
Use QGIS to generate input for **routing**, **isochrones** and **matrix calculations** powered by ORS, either via clicking coordinates in the map canvas or using point layers for batch operation.

### Customization
The tool includes a `config.yml` to set the basic config parameters for openrouteservice:

```yaml
base_url: https://api.openrouteservice.org
api_key: 
req_per_min: 40
```
The `api_key` is updated dynamically from the UI. However, if you're running a local ORS version, you want to change the `base_url`. If your API key is eligible for higher rate limits than 40 req/min, you can also specify this here.

## Getting Started

### Prerequisites

QGIS versin: min. **v3.0**

API key: https://openrouteservice.org/sign-up/

### Installation

Either from QGIS plugin repository or manually:
  - [Download](https://github.com/nilsnolde/OSMtools/archive/master.zip) ZIP file from Github
  - Unzip folder contents and copy `OSMtools` folder to:
    - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins`
    - Windows: `C:\Users\USER\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins`
    - Mac OS: `Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins`

## License
This project is published under the GPLv3 license, see [LICENSE.md](https://github.com/nilsnolde/ORStools/blob/master/LICENSE.md) for details.

By using this plugin, you also agree to the terms and conditions of OpenRouteService, as outlined [here](https://openrouteservice.org/terms-of-service/).
