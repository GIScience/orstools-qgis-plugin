# -*- coding: utf-8 -*-
"""
/***************************************************************************
 OSMtools
                                 A QGIS plugin
 falk
                              -------------------
        begin                : 2017-02-01
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Nils Nolde
        email                : nils.nolde@gmail.com
 ***************************************************************************/

 This plugin provides access to the various APIs from OpenRouteService
 (https://openrouteservice.org), developed and
 maintained by GIScience team at University of Heidelberg, Germany. By using
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

from itertools import product
from PyQt5.QtCore import QVariant

from qgis.core import (QgsPointXY,
                       QgsGeometry,
                       QgsFeature,
                       QgsFields,
                       QgsField,
                       QgsCoordinateReferenceSystem)

from ORStools.utils import convert


def get_request_features(route_dict, row_by_row):

    locations_list = list(product(route_dict['start']['geometries'],
                                  route_dict['end']['geometries']))
    values_list = list(product(route_dict['start']['values'],
                               route_dict['end']['values']))

    # If row-by-row in two-layer mode, then only zip the locations
    if row_by_row in (True, 'Row-by-Row'):
        locations_list = list(zip(route_dict['start']['geometries'],
                                  route_dict['end']['geometries']))

        values_list = list(zip(route_dict['start']['values'],
                               route_dict['end']['values']))

    for properties in zip(locations_list, values_list):
        # Skip if first and last location are the same
        if properties[0][0] == properties[0][-1]:
            continue

        coordinates = convert.build_coords(properties[0])
        values = properties[1]

        yield (coordinates, values)


def get_fields(from_type, to_type):

    fields = QgsFields()
    fields.append(QgsField("DISTANCE", QVariant.Double))
    fields.append(QgsField("TIME_H", QVariant.Double))
    fields.append(QgsField("PROFILE", QVariant.String))
    fields.append(QgsField("PREF", QVariant.String))
    fields.append(QgsField("AVOID_TYPE", QVariant.String))
    fields.append(QgsField("FROM_ID", from_type))
    fields.append(QgsField("TO_ID", to_type))

    return fields


def get_feature(response, profile, preference, avoid, from_value, to_value):
    response_mini = response['features'][0]
    feat = QgsFeature()
    coordinates = response_mini['geometry']['coordinates']
    distance = response_mini['properties']['summary'][0]['distance']
    duration = response_mini['properties']['summary'][0]['duration']
    qgis_coords = [QgsPointXY(x, y) for x, y in coordinates]
    feat.setGeometry(QgsGeometry.fromPolylineXY(qgis_coords))
    feat.setAttributes(["{0:.3f}".format(distance / 1000),
                        "{0:.3f}".format(duration / 3600),
                        profile,
                        preference,
                        avoid,
                        from_value,
                        to_value
                        ])
    return feat
