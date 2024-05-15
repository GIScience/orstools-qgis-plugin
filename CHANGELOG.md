# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)

<!--
This is how a Changelog entry should look like:

## [version] - YYYY-MM-DD

### Added
- for new features.
### Changed
- existing functionality.
### Deprecated
- soon-to-be removed features.
### Removed
- now removed features.
### Fixed
- any bug.
### Security
- in case of vulnerabilities. (Use for vulnerability fixes)

RELEASING:
1. Change Unreleased to new release number
2. Add today's Date
3. Change unreleased link to compare new release:
[unreleased]: https://github.com/GIScience/orstools-qgis-plugin/compare/vnew...HEAD
4. Add new compare link below
[new]: https://github.com/GIScience/orstools-qgis-plugin/compare/vlast...vnew
5. Double check issue links are valid. Format: item ([#issue-nr](full-url))
6. Replace ORStools/metadata.txt changelog with latest release info
7. Update ORStools/metadata.txt with the new version number
8. Commit changes with `git commit -m 'chore: release vX.X.X'`
9. Tag the commit `git tag -a vX.X.X -m "vX.X.X"`
10. Push release commit and tag 'git push && git push origin vX.X.X'
11. Make sure that your branch is up to date with 'origin/main' and there are no unstaged changes
12. In repository root generate the plugin package: `zip -r ORStools-vX.X.X.zip ORStools -x "*__pycache__*" "*.ruff_cache*"`
13. Upload the package to https://plugins.qgis.org/plugins/ORStools/ (Manage > Add Version)
14. Create new release in GitHub with tag version and release title of `vX.X.X`
 -->

## Unreleased

### Fixed
- QGis crashes when selecting more than two vertices for deletion ([#230](https://github.com/GIScience/orstools-qgis-plugin/issues/230))
- Vertices on canvas not depicted fully with n having more than one digit in length ([#235](https://github.com/GIScience/orstools-qgis-plugin/issues/235))
- Replace qt QSettings with QgsSettings for centralized configuration management ([#239](https://github.com/GIScience/orstools-qgis-plugin/issues/239))
- Fix: Point Annotations stay after saving project and not deleting them manually([#229](https://github.com/GIScience/orstools-qgis-plugin/issues/229))
- Improved type hints

### Added
- Add support for decimal ranges with isochrones([#237](https://github.com/GIScience/orstools-qgis-plugin/issues/237))
- Add hint for joining with `Layer ID Field` ([#143](https://github.com/GIScience/orstools-qgis-plugin/issues/143))
- Add option to export order of optimization route points ([#145](https://github.com/GIScience/orstools-qgis-plugin/issues/145))

### Changed
- Rename `Ok` button in configuration window to `Save` for clarification([#241](https://github.com/GIScience/orstools-qgis-plugin/issues/241))

## [1.7.1] - 2024-01-15

### Added
- Add hint to use batch jobs for point layers in tooltip in save vertices button ([#211](https://github.com/GIScience/orstools-qgis-plugin/issues/211))

### Fixed
- TypeError if no SVGPaths are set ([#212](https://github.com/GIScience/orstools-qgis-plugin/issues/212))
- replace removesuffix() function with replace() function in base processing algorithm ([#215](https://github.com/GIScience/orstools-qgis-plugin/pull/215))
- Replace line style with style from QGIS v3.16 to enable correct rendering in older versions ([#218](https://github.com/GIScience/orstools-qgis-plugin/issues/218))

## [1.7.0] - 2023-12-22

### Added
- Add keyboard shortcut (Ctrl+R)
- Additional parameter for the "smoothing factor" to isochrones processing algorithms ([#172](https://github.com/GIScience/orstools-qgis-plugin/issues/172))
- Mention omission of configuration options when using traveling salesman
- option to set location type for isochrones ([#191](https://github.com/GIScience/orstools-qgis-plugin/pull/191))
- Add styling of routing output in main plugin ([#149](https://github.com/GIScience/orstools-qgis-plugin/issues/149))
- make items in centroid list drag and droppable ([#144](https://github.com/GIScience/orstools-qgis-plugin/issues/144))
- Add save button for vertices ([#144](https://github.com/GIScience/orstools-qgis-plugin/issues/144))
- remove blue lines every time the red X button is clicked ([#120](https://github.com/GIScience/orstools-qgis-plugin/issues/120))

## [1.6.0] - 2023-07-25

### Added
- translation mechanism ([#183](https://github.com/GIScience/orstools-qgis-plugin/pull/183))
- german translation ([#183](https://github.com/GIScience/orstools-qgis-plugin/pull/183))

## [1.5.3] - 2023-03-30

### Fixed
- error on QGIS 3.30 with QgsWkbType used for QgsRubberBand ([#179](https://github.com/GIScience/orstools-qgis-plugin/pull/179))

## [1.5.2] - 2022-01-20

### Fixed
- error for layers with z/m values ([#166](https://github.com/GIScience/orstools-qgis-plugin/pull/166))

## [1.5.1] - 2022-01-11

### Fixed
- matrix algorithm parsing hidden options ([#164](https://github.com/GIScience/orstools-qgis-plugin/issues/164))

## [1.5.0] - 2021-12-08

### Added
- isochrone center lat and lon to isochrone attribute table ([#137](https://github.com/GIScience/orstools-qgis-plugin/issues/137))
- implement `options`-parameter for routing and isochrones
- prepare `options`-parameter for matrix
- custom request timeouts for providers ([#122](https://github.com/GIScience/orstools-qgis-plugin/issues/122))
- exception on network failures due to unresponsive provider

### Changed
- default url for new provider entry to default ors backend url

## [1.4.0] - 2021-06-15

### Added
- CHANGELOG.md including release instructions
- 'recommended' preference
- round trip parameter to TSP-options for Advanced Directions ([#125](https://github.com/GIScience/orstools-qgis-plugin/issues/125))
- all TSP-options to 'Directions (Line and 1 Layer)' algorithms ([#155](https://github.com/GIScience/orstools-qgis-plugin/issues/155))
- custom sorting order for waypoints in 'Directions'-Algorithms ([#142](https://github.com/GIScience/orstools-qgis-plugin/issues/142))

### Changed
- parameter names of TSP-options for Advanced Directions
- help file formatting to highlight parameters and unify format

### Fixed
- author information
- repository link
- Correct isochrone computation from layer without fields
- other errors stemming from layers without fields

### Removed
- 'cycling-safe' profile
- gis-ops information

## [1.3.0] - 2021-04-30

### Changed
- maintainers from [nils](https://github.com/nilsnolde) to [jakob](https://github.com/koebi) and [amandus](https://github.com/TheGreatRefrigerator)

### Fixed
- directions from line layer ([#123](https://github.com/GIScience/orstools-qgis-plugin/issues/123))
- help file encodings on mac
- typos in help docs
- Layer ID types for directions from 1 point layer ([#124](https://github.com/GIScience/orstools-qgis-plugin/issues/124), [#127](https://github.com/GIScience/orstools-qgis-plugin/issues/127))
- incorrect algorithm ownership ([#119](https://github.com/GIScience/orstools-qgis-plugin/issues/119))
- avoid_polygons ([#118](https://github.com/GIScience/orstools-qgis-plugin/issues/118))
- metadata category
- ors ask forum links
- warning popup for missing waypoints

## [1.2.3] - 2020-02-22

### Changed
- GeoPackage implementation from v1.2.2 to [Nyall's suggestion](https://github.com/qgis/QGIS/issues/34606#issuecomment-589901410)

## [1.2.2] - 2020-02-20

### Added
- backwards-compatible and future-proof workaround for possible QGIS GeoPackage bug ([#114](https://github.com/GIScience/orstools-qgis-plugin/issues/114))

## [1.2.1] - 2019-12-02

### Fixed
- isochrone layer bug for empty IDs ([#113](https://github.com/GIScience/orstools-qgis-plugin/issues/113))
- isochrones for local setups ([#112](https://github.com/GIScience/orstools-qgis-plugin/issues/112))

## [1.2.0] - 2019-08-19

### Added
- avoid_polygons parameter ([#79](https://github.com/GIScience/orstools-qgis-plugin/issues/79))

## [1.1.1] - 2019-08-19

### Changed
- metadata, because repository moved to GIScience

## [1.1.0] - 2019-08-19

### Added
- traveling salesman option ([#109](https://github.com/GIScience/orstools-qgis-plugin/issues/109))
- support for more than 2 waypoints (batch & interactive)
- elevation information ([#83](https://github.com/GIScience/orstools-qgis-plugin/issues/83))
- avoid_countries ([#78](https://github.com/GIScience/orstools-qgis-plugin/issues/78))

### Changed
- openrouteservice requests from v1 API to v2 ([#99](https://github.com/GIScience/orstools-qgis-plugin/issues/99))

## [1.0.7] - 2019-05-21

### Added
- warning messages to improve first user experience ([#106](https://github.com/GIScience/orstools-qgis-plugin/issues/106))

## [1.0.6] - 2019-05-06

### Changed
- quota info to being optional ([#106](https://github.com/GIScience/orstools-qgis-plugin/issues/106))

## [1.0.5] - 2019-05-02

### Added
- info message when no API key set for provider ([#101](https://github.com/GIScience/orstools-qgis-plugin/issues/101))

### Fixed
- custom provider not working ([#103](https://github.com/GIScience/orstools-qgis-plugin/issues/103))

## [1.0.4] - 2019-04-17

### Fixed
- POST requests not accepting dictionaries as parameter ([#100](https://github.com/GIScience/orstools-qgis-plugin/issues/100))

## [1.0.3] - 2019-04-15

## Added
- NetworkAccessManager to leverage QGIS Proxy settings ([#98](https://github.com/GIScience/orstools-qgis-plugin/issues/98))

## Removed
- requests module
- user defined rate limits ([#97](https://github.com/GIScience/orstools-qgis-plugin/issues/97))

## [1.0.2] - 2019-03-14

### Fixed
- mix-up of source and destination layer in matrix algo ([#92](https://github.com/GIScience/orstools-qgis-plugin/issues/92))
- UTF-8 encoding issues for Mac OSX ([#91](https://github.com/GIScience/orstools-qgis-plugin/issues/91))

## [1.0.1] - 2019-03-01

### Added
- default isochrone layer ID field of first layer attribute ([#90](https://github.com/GIScience/orstools-qgis-plugin/issues/90))

## [1.0.0] - 2019-01-27

### Added
- first working version of ORS Tools, after replacing OSM Tools plugin


[unreleased]: https://github.com/GIScience/orstools-qgis-plugin/compare/v1.7.1...HEAD
[1.7.1]: https://github.com/GIScience/orstools-qgis-plugin/compare/v1.7.0...v1.7.1
[1.7.0]: https://github.com/GIScience/orstools-qgis-plugin/compare/v1.6.0...v1.7.0
[1.6.0]: https://github.com/GIScience/orstools-qgis-plugin/compare/v1.5.3...v1.6.0
[1.5.3]: https://github.com/GIScience/orstools-qgis-plugin/compare/v1.5.2...v1.5.3
[1.5.2]: https://github.com/GIScience/orstools-qgis-plugin/compare/v1.5.1...v1.5.2
[1.5.1]: https://github.com/GIScience/orstools-qgis-plugin/compare/v1.5.0...v1.5.1
[1.5.0]: https://github.com/GIScience/orstools-qgis-plugin/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/GIScience/orstools-qgis-plugin/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/GIScience/orstools-qgis-plugin/compare/v1.2.3...v1.3.0
[1.2.3]: https://github.com/GIScience/orstools-qgis-plugin/compare/v1.2.2...v1.2.3
[1.2.2]: https://github.com/GIScience/orstools-qgis-plugin/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/GIScience/orstools-qgis-plugin/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/GIScience/orstools-qgis-plugin/compare/v1.1.1...v1.2.0
[1.1.1]: https://github.com/GIScience/orstools-qgis-plugin/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/GIScience/orstools-qgis-plugin/compare/v1.0.7...v1.1.0
[1.0.7]: https://github.com/GIScience/orstools-qgis-plugin/compare/v1.0.6...v1.0.7
[1.0.6]: https://github.com/GIScience/orstools-qgis-plugin/compare/v1.0.5...v1.0.6
[1.0.5]: https://github.com/GIScience/orstools-qgis-plugin/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/GIScience/orstools-qgis-plugin/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/GIScience/orstools-qgis-plugin/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/GIScience/orstools-qgis-plugin/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/GIScience/orstools-qgis-plugin/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/GIScience/orstools-qgis-plugin/commit/db36024
