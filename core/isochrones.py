#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Contains isochrones class to perform requests to ORS isochrone API.
"""


from PyQt4.QtCore import QVariant
from PyQt4.QtGui import QColor

from qgis.core import (QgsPoint,
                       QgsVectorLayer,
                       QgsFeature,
                       QgsField,
                       QgsGeometry,
                       QgsSymbolV2,
                       QgsSimpleFillSymbolLayerV2,
                       QgsRendererCategoryV2,
                       QgsCategorizedSymbolRendererV2)

from OSMtools.core.convert import _build_coords, _comma_list
from OSMtools.core.exceptions import InvalidParameterException


ISOCHRONES_API = '/isochrones'
ISOCHRONES_METRICS = ['time', 'distance']
# TODO: inherit these from profiles shared with other ORS services
ISOCHRONES_PROFILES = [
    'driving-car',
    'driving-hgv',
    'cycling-regular',
    'cycling-road',
    'cycling-safe',
    'cycling-mountain',
    'cycling-tour',
    'foot-walking',
    'foot-hiking',
]

def requestFromPoint(client, point, metric, ranges, profile):
    """
    Requests isochrones for the given parameters.

    :param client: The client instance to use
    :type responses: OSMtools.core.client.Client

    :param point: The isochrone center to query
    :type name_ext: QgsPoint

    :param metric: The metric to use, see ISOCHRONES_METRICS
    :type name_ext: string

    :param ranges: A list of ranges to query, either in seconds or in meters
    :type name_ext: list of int

    :param profile: The mobility profile to use, see ISOCHRONES_PROFILES
    :type name_ext: string

    :rtype: QgsVectorLayer
    """
    if metric not in ISOCHRONES_METRICS:
        raise InvalidParameterException('metric', metric, ISOCHRONES_METRICS)

    if type(ranges) != list or len(ranges) == 0:
        raise InvalidParameterException('ranges', ranges)

    if profile not in ISOCHRONES_PROFILES:
        raise InvalidParameterException('profile', profile, ISOCHRONES_PROFILES)

    params = {
        # altough the parameter is called locations, it only supports one point..
        'locations': _build_coords([point.x(), point.y()]),
        'profile': profile,
        'range': _comma_list(ranges),
        'range_type': metric,
    }

    return client.request(ISOCHRONES_API, params)


def layerFromRequests(responses, layer=None):
    """
    Parses a list of ORS isochrones JSON responses into polygons and
    adds them to the given or newly created empty layer.
    Also appends the attribute columns and styles the layer.

    While the responses can technically be made of different profile, range
    or range_type requests, the layer is styled for the last matched range_type

    :param responses: Responses from isochrone request.
    :type responses: list of JSON

    :param layer: Optional layer to populate
    :type name_ext: QgsVectorLayer

    :rtype: QgsVectorLayer
    """

    if not layer:
        poly_out = QgsVectorLayer("Polygon?crs=EPSG:4326", "Isochrones", "memory")
    else:
        poly_out = layer

    poly_out.dataProvider().addAttributes([QgsField("AA_MINS", QVariant.Double, len=4, prec=2)])
    poly_out.dataProvider().addAttributes([QgsField("AA_METERS", QVariant.Int)])
    poly_out.dataProvider().addAttributes([QgsField("AA_MODE", QVariant.String)])
    poly_out.updateFields()

    # Sort features based on the isochrone value, so that longest isochrone
    # is added first. This will plot the isochrones on top of each other.
    l = lambda x: x['properties']['value']
    for response in responses:
        profile = response['info']['query']['profile']
        metric = response['info']['query']['range_type']

        for isochrone in sorted(response['features'], key=l, reverse=True):
            feat = QgsFeature()
            coordinates = isochrone['geometry']['coordinates']
            iso_value = isochrone['properties']['value']
            qgis_coords = [QgsPoint(x, y) for x, y in coordinates[0]]
            feat.setGeometry(QgsGeometry.fromPolygon([qgis_coords]))
            feat.setAttributes([float(iso_value) / 60 if metric == 'time' else None,
                                iso_value if metric == 'distance' else None,
                                profile])
            poly_out.dataProvider().addFeatures([feat])

    poly_out.updateExtents()
    _stylePoly(poly_out, metric)
    return poly_out


def _stylePoly(layer, metric):
    """
    Style isochrone polygon layer

    :param layer: Polygon layer to be styled.
    :type layer: QgsMapLayer
    """
    if metric == 'time':
        field_name = 'AA_MINS'
        legend_suffix = ' min'
    elif metric == 'distance':
        field_name = 'AA_METERS'
        legend_suffix = ' m'
    field = layer.fields().indexFromName(field_name)
    unique_values = sorted(layer.uniqueValues(field))
    unique_values.append('') # workaround for https://issues.qgis.org/issues/14779

    colors = {0: QColor('#2b83ba'),
              1: QColor('#64abb0'),
              2: QColor('#9dd3a7'),
              3: QColor('#c7e9ad'),
              4: QColor('#edf8b9'),
              5: QColor('#ffedaa'),
              6: QColor('#fec980'),
              7: QColor('#f99e59'),
              8: QColor('#e85b3a'),
              9: QColor('#d7191c')}

    categories = []

    for cid, unique_value in enumerate(unique_values):
        # initialize the default symbol for this geometry type
        symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())

        # configure a symbol layer
        symbol_layer = QgsSimpleFillSymbolLayerV2(color=colors[cid],
                                                #strokeColor=QColor('#000000')
                                                )

        # replace default symbol layer with the configured one
        if symbol_layer is not None:
            symbol.changeSymbolLayer(0, symbol_layer)

        # entry for the list of category items
        legendtext = "{:.2f}".format(unique_value) + legend_suffix if unique_value else ''
        category = QgsRendererCategoryV2(unique_value, symbol, legendtext)
        categories.append(category)

    # create renderer object
    renderer = QgsCategorizedSymbolRendererV2(field_name, categories)

    # assign the created renderer to the layer
    if renderer is not None:
        layer.setRendererV2(renderer)
    layer.setLayerTransparency(50)

    layer.triggerRepaint()
