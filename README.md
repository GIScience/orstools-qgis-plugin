# ORS Tools QGIS plugin

![ORS Tools](https://user-images.githubusercontent.com/23240110/122937401-3ee72400-d372-11eb-8e3b-6c435d1dd964.png)

Set of tools for QGIS to use the [openrouteservice](https://openrouteservice.org) (ORS) API.

ORS Tools gives you easy access to the following API's:

- [Directions](https://openrouteservice.org/dev/#/api-docs/v2/directions/{profile}/geojson/post)
- [Isochrones](https://openrouteservice.org/dev/#/api-docs/v2/isochrones/{profile}/post)
- [Matrix](https://openrouteservice.org/dev/#/api-docs/v2/matrix/{profile}/post)
- [Traveling Salesman](https://openrouteservice.org/dev/#/api-docs/optimization/post)

The [wiki](https://github.com/GIScience/orstools-qgis-plugin/wiki/ORS-Tools-Help) offers a tutorial on usage.

In case of issues/bugs, please use the [issue tracker](https://github.com/GIScience/orstools-qgis-plugin/issues).

For general questions, please ask in our [forum](https://ask.openrouteservice.org/c/sdks/qgis).

See also:
- [Rate limits](https://openrouteservice.org/restrictions/)
- [ORS user dashboard](https://openrouteservice.org/dev/#/home)
- [API documentation](https://openrouteservice.org/dev/#/api-docs)
- ORS openrouteservice-py on [PyPi](https://pypi.python.org/pypi/openrouteservice)
- ORS Tools plugin in [QGIS repo](https://plugins.qgis.org/plugins/ORStools/)

## Functionalities

### General

Use QGIS to generate input for **routing**, **isochrones** and **matrix calculations** powered by ORS.

You'll have to create an openrouteservice account and get a free API key first: <https://openrouteservice.org/sign-up>.
After you have received your key, add it to the default `openrouteservice` provider via `Web` ► `ORS Tools` ►
`Provider Settings` or click the settings button in the ORS Tools dialog.

The plugin offers either a GUI in the `Web` menu and toolbar of QGIS to interactively use the ORS API
from the map canvas.

For batch operations you can find an `ORS Tools` folder in the Processing Toolbox.

### Customization

Additionally, you can register other ORS providers, e.g. if you're hosting a custom ORS backend.

Configuration takes place either from the Web menu entry *ORS Tools* ► *Provider settings*. Or from the *Config* button
in the GUI.

## Getting Started

### Prerequisites

QGIS version: **v3.4** or above

API key: https://openrouteservice.org/sign-up/

### Installation

In the QGIS menu bar click `Plugins` ► `Manage and Install Plugins...`.

Then search for `openrouteservice` and install `ORS Tools`.

Alternatively, install the plugin manually:
  - [Download](https://github.com/GIScience/orstools-qgis-plugin/archive/main.zip) ZIP file from GitHub
  - Unzip folder contents and copy `ORStools` folder to:
    - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins`
    - Windows: `C:\Users\USER\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins`
    - Mac OS: `Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins`

## License

This project is published under the GPLv3 license, see [LICENSE.md](https://github.com/GIScience/orstools-qgis-plugin/blob/main/LICENSE.md) for details.

By using this plugin, you also agree to the [terms and conditions](https://openrouteservice.org/terms-of-service/) of
openrouteservice.

## Acknowledgements

This project was first started by [Nils Nolde](https://github.com/nilsnolde).
