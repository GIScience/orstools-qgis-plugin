# OSM tools
Set of tools to use openrouteservice (ORS) API's as a plugin in QGIS (www.openrouteservice.org).

**Note**, this branch is backported from `master` for QGIS **v.2.x**!

See also:
- [Rate limits](https://openrouteservice.org/ratelimits/)
- [ORS developer documentation](https://openrouteservice.org/documentation/)
- ORS openrouteservice-py on [PyPi](https://pypi.python.org/pypi/openrouteservice)
- OSM Tools plugin in [QGIS repo](https://plugins.qgis.org/plugins/OSMtools/)

## Functionalities

### General
Use QGIS to generate input for routing, isochrones and matrix calculations powered by ORS, either via clicking coordinates in the map canvas or using point layers for batch operation.

### Customization
From v2.x/3.x, the tool includes a `config.yml` to set the basic config parameters for openrouteservice:

```yaml
base_url: https://api.openrouteservice.org
api_key: 
req_per_min: 40
```
Use QGIS to generate input for **routing**, **isochrones** and **matrix calculations** powered by ORS, either via clicking coordinates in the map canvas or using point layers for batch operation.

## Getting Started
### Prerequisite

QGIS versin: min. **v2.x**

API key: https://openrouteservice.org/sign-up/

### Installation

Either from QGIS plugin repository or manually:
  - Copy branch contents to folder named 'OSMtools'
  - Copy folder to OS dependent plugin directory
  
## Contributing
The plugin has undergone a major refactoring while moving to QGIS v3. I'm still in the process of writing unit tests. However, if you'd like to contribute, feel free to fork and create PR's. 

## License
This project is published under the MIT license, see [LICENSE.md](https://github.com/nilsnolde/ORStools/blob/master/LICENSE.md) for details.

By using this plugin, you also agree to the terms and conditions of OpenRouteService, as outlined [here](https://developers.openrouteservice.org/portal/about).
