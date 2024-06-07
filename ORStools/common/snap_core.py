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

from qgis.core import QgsFeature, QgsPointXY, QgsGeometry


def get_snapped_point_features(response: dict) -> list:
    locations = response["locations"]
    feats = []
    for location in locations:
        feat = QgsFeature()
        if location:
            coords = location["location"]
            if "name" in location.keys():
                name = location["name"]
            snapped_distance = location["snapped_distance"]
            attr = [name, snapped_distance] if "name" in location.keys() else ["", snapped_distance]
            feat.setAttributes(attr)
            feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(coords[0], coords[1])))

        feats.append(feat)

    return feats
