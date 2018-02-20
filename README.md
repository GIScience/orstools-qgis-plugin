# OSM tools
Set of tools to use openrouteservice (ORS) API's as a plugin in QGIS (www.openrouteservice.org).

See also:
- [Rate limits](https://openrouteservice.org/ratelimits/)
- [ORS developer documentation](https://openrouteservice.org/documentation/)
- ORS openrouteservice-py on [PyPi](https://pypi.python.org/pypi/openrouteservice)
- OSM Tools plugin in [QGIS repo](https://plugins.qgis.org/plugins/OSMtools/)

## Functionalities

Use QGIS to generate input for routing and accessibility area analysis powered by ORS, either via clicking coordinates in the map canvas or using point layers for batch operation.

## Getting Started
### Prerequisite

QGIS versin: min. v2.99

API key: https://openrouteservice.org/sign-up/

### Installation

Either from QGIS plugin repository or manually:
  - Copy branch contents to folder named 'OSMtools'
  - Copy folder to .../.qgis2/python/plugins
  
## Contributing
The plugin has undergone a major refactoring while moving to QGIS v3. I'm still in the process of writing unit tests. However, if you'd like to contribute, feel free to fork and create PR's. 

## License
This project is published under the MIT license, see [LICENSE.md](https://github.com/nilsnolde/ORStools/blob/master/LICENSE.md) for details.

By using this plugin, you also agree to the terms and conditions of OpenRouteService, as outlined [here](https://developers.openrouteservice.org/portal/about).
