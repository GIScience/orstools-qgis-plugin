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
7. Commit changes with `git commit -m 'Release vX.X.X'`
8. Tag the commit `git tag -a vX.X.X -m "vX.X.X"`
9. Push release commit and tag 'git push && git push vX.X.X'
10. In repository root generate the plugin package: `zip -r ORStools-vX.X.X.zip ORStools -x "*__pycache__*"`
11. Upload the package to https://plugins.qgis.org/plugins/ORStools/ (Manage > Add Version)
12. Create new release in GitHub with tag version and release title of `vX.X.X`
 -->

## [Unreleased]

### Added
- CHANGELOG.md including release instructions
- 'recommended' preference

### Fixed
- author information
- repository link
- Correct isochrone computation from layer without fields

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


[unreleased]: https://github.com/GIScience/orstools-qgis-plugin/compare/v1.3.0...HEAD
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
