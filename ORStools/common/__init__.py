# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ORStools
                                 A QGIS plugin
 QGIS client to query openrouteservice
                              -------------------
        begin                : 2017-02-01
        git sha              : $Format:%H$
        copyright            : (C) 2021 by HeiGIT gGmbH
        email                : support@openrouteservice.heigit.org
 ***************************************************************************/

 This plugin provides access to openrouteservice API functionalities
 (https://openrouteservice.org), developed and
 maintained by the openrouteservice team of HeiGIT gGmbH, Germany. By using
 this plugin you agree to the ORS terms of service
 (https://openrouteservice.org/terms-of-service/).

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

PROFILES = [
    "driving-car",
    "driving-hgv",
    "cycling-regular",
    "cycling-road",
    "cycling-mountain",
    "cycling-electric",
    "foot-walking",
    "foot-hiking",
    "wheelchair",
]

DIMENSIONS = ["time", "distance"]

PREFERENCES = ["fastest", "shortest", "recommended"]

OPTIMIZATION_MODES = ["Round Trip", "Fix Start Point", "Fix End Point", "Fix Start and End Point"]

AVOID_FEATURES = ["highways", "tollways", "ferries", "fords", "steps"]

AVOID_BORDERS = ["all", "controlled", "none"]

ADVANCED_PARAMETERS = [
    "INPUT_AVOID_FEATURES",
    "INPUT_AVOID_BORDERS",
    "INPUT_AVOID_COUNTRIES",
    "INPUT_AVOID_POLYGONS",
    "INPUT_SMOOTHING",
    "EXTRA_INFO",
    "CSV_FACTOR",
    "CSV_COLUMN",
]

LOCATION_TYPES = ["start", "destination"]

EXTRA_INFOS = [
    "steepness",
    "suitability",
    "surface",
    "waytype",
    "waycategory",
    "tollways",
    "traildifficulty",
    "osmid",
    "roadaccessrestrictions",
    "countryinfo",
    "green",
    "noise",
    "csv",
    "shadow",
]
