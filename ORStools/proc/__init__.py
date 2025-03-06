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
from ORStools.common import PROFILES

ENDPOINTS = {
    "directions": "directions",
    "isochrones": "isochrones",
    "matrix": "matrix",
    "optimization": "optimization",
    "snapping": "snapping",
    "export": "export",
}

DEFAULT_SETTINGS = {
    "providers": [
        {
            "ENV_VARS": {
                "ORS_QUOTA": "X-Ratelimit-Limit",
                "ORS_REMAINING": "X-Ratelimit-Remaining",
            },
            "base_url": "https://api.openrouteservice.org",
            "key": "",
            "name": "openrouteservice",
            "timeout": 60,
            "endpoints": ENDPOINTS,
            "profiles": PROFILES,
        }
    ]
}
