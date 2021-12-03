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

from itertools import product
from qgis.core import (QgsPoint,
                       QgsPointXY,
                       QgsGeometry,
                       QgsFeature,
                       QgsFields,
                       QgsField)
from typing import List

from PyQt5.QtCore import QVariant

from ORStools.utils import convert


def get_request_point_features(route_dict, row_by_row):
    """
    Processes input point features depending on the layer to layer relation in directions settings

    :param route_dict: all coordinates and ID field values of start and end point layers
    :type route_dict: dict

    :param row_by_row: Specifies whether row-by-row relation or all-by-all has been used.
    :type row_by_row: str

    :returns: tuple of coordinates and ID field value for each routing feature in route_dict
    :rtype: tuple
    """

    locations_list = list(product(route_dict['start']['geometries'],
                                  route_dict['end']['geometries']))
    values_list = list(product(route_dict['start']['values'],
                               route_dict['end']['values']))

    # If row-by-row in two-layer mode, then only zip the locations
    if row_by_row == 'Row-by-Row':
        locations_list = list(zip(route_dict['start']['geometries'],
                                  route_dict['end']['geometries']))

        values_list = list(zip(route_dict['start']['values'],
                               route_dict['end']['values']))

    for properties in zip(locations_list, values_list):
        # Skip if first and last location are the same
        if properties[0][0] == properties[0][-1]:
            continue

        coordinates = [[round(x, 6), round(y, 6)] for x, y in properties[0]]
        values = properties[1]

        yield coordinates, values


def get_fields(from_type=QVariant.String, to_type=QVariant.String, from_name="FROM_ID", to_name="TO_ID", line=False):
    """
    Builds output fields for directions response layer.

    :param from_type: field type for 'FROM_ID' field
    :type from_type: QVariant enum

    :param to_type: field type for 'TO_ID' field
    :type to_type: QVariant enum

    :param from_name: field name for 'FROM_ID' field
    :type from_name: str

    :param to_name: field name for 'TO_ID' field
    :type to_name: field name for 'TO_ID' field

    :param line: Specifies whether the output feature is a line or a point
    :type line: boolean

    :returns: fields object to set attributes of output layer
    :rtype: QgsFields
    """

    fields = QgsFields()
    fields.append(QgsField("DIST_KM", QVariant.Double))
    fields.append(QgsField("DURATION_H", QVariant.Double))
    fields.append(QgsField("PROFILE", QVariant.String))
    fields.append(QgsField("PREF", QVariant.String))
    fields.append(QgsField("OPTIONS", QVariant.String))
    fields.append(QgsField(from_name, from_type))
    if not line:
        fields.append(QgsField(to_name, to_type))

    return fields


def get_output_feature_directions(response, profile, preference, options=None, from_value=None, to_value=None):
    """
    Build output feature based on response attributes for directions endpoint.

    :param response: API response object
    :type response: dict

    :param profile: Transportation mode being used
    :type profile: str

    :param preference: Cost being used, shortest, fastest or recommended.
    :type preference: str

    :param options: Avoidables being used.
    :type options: str

    :param from_value: value of 'FROM_ID' field
    :type from_value: any

    :param to_value: value of 'TO_ID' field
    :type to_value: any

    :returns: Output feature with attributes and geometry set.
    :rtype: QgsFeature
    """
    response_mini = response['features'][0]
    feat = QgsFeature()
    coordinates = response_mini['geometry']['coordinates']
    distance = response_mini['properties']['summary']['distance']
    duration = response_mini['properties']['summary']['duration']
    qgis_coords = [QgsPoint(x, y, z) for x, y, z in coordinates]
    feat.setGeometry(QgsGeometry.fromPolyline(qgis_coords))
    feat.setAttributes([f"{distance / 1000:.3f}",
                        f"{duration / 3600:.3f}",
                        profile,
                        preference,
                        str(options),
                        from_value,
                        to_value
                        ])

    return feat


def get_output_features_optimization(response, profile, from_value=None):
    """
    Build output feature based on response attributes for optimization endpoint.

    :param response: API response object
    :type response: dict

    :param profile: transportation profile to be used
    :type profile: str

    :param from_value: value of 'FROM_ID' field
    :type from_value: any

    :returns: built feature
    :rtype: QgsFeature
    """

    response_mini = response['routes'][0]
    feat = QgsFeature()
    polyline = response_mini['geometry']
    distance = response_mini['distance']
    duration = response_mini['cost']
    qgis_coords = [QgsPointXY(x, y) for x, y in convert.decode_polyline(polyline)]
    feat.setGeometry(QgsGeometry.fromPolylineXY(qgis_coords))
    feat.setAttributes([f"{distance / 1000:.3f}",
                        f"{duration / 3600:.3f}",
                        profile,
                        'fastest',
                        'optimized',
                        from_value
                        ])

    return feat


def build_default_parameters(preference: str, point_list: List[QgsPointXY] = None, coordinates: list = None, options: dict = None) -> dict:
    """
    Build default parameters for directions endpoint. Either uses a list of QgsPointXY to create the coordinates
    passed in point_list or an existing coordinate list within the coordinates parameter.
    TODO no optimal solution, maybe let get_request_point_features() return QgsPointXY as well to only use point_list

    :param preference: routing preference, shortest/fastest/recommended
    :type preference: str

    :param point_list:
    :type point_list: list of QgsPointXY

    :param coordinates:
    :type coordinates: list

    :returns: parameters for directions endpoint
    :rtype: dict
    """
    coords = coordinates if coordinates else [[round(point.x(), 6), round(point.y(), 6)] for point in point_list]
    params = {
        'coordinates': coords,
        'preference': preference,
        'geometry': 'true',
        'instructions': 'false',
        'elevation': True,
        'id': None,
        "options": options
    }

    return params
