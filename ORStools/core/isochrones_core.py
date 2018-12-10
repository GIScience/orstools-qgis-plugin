# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ORStools
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
"""
Contains isochrones class to perform requests to ORS isochrone API.
"""


from PyQt5.QtCore import QVariant
from PyQt5.QtGui import QColor

from qgis.core import (QgsPointXY,
                       QgsVectorLayer,
                       QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsGeometry,
                       QgsSymbol,
                       QgsSimpleFillSymbolLayer,
                       QgsRendererCategory,
                       QgsCategorizedSymbolRenderer)

class Isochrones():

    def __init__(self):

        # Will all be set in self.set_parameters(), bcs Processing Algo has to initialize this class before it
        # knows about its own parameters
        self.layer_name = None
        self.profile = None
        self.dimension = None
        self.id_field_type = None
        self.id_field_name = None
        self.factor = None
        self.difference = None
        self.field_dimension_name = None

    def set_parameters(self, layer_name, profile, dimension, id_field_type, id_field_name, factor, difference=None):
        self.layer_name = layer_name
        self.profile = profile
        self.dimension = dimension
        self.id_field_type = id_field_type
        self.id_field_name = id_field_name
        self.factor = factor
        self.difference = difference or None

        self.field_dimension_name = "AA_MINS" if self.dimension == 'time' else "AA_METERS"

    def get_fields(self):

        fields = QgsFields()
        fields.append(QgsField(self.id_field_name, self.id_field_type))  # ID field
        fields.append(QgsField(self.field_dimension_name, QVariant.Int))  # Dimension field
        fields.append(QgsField("AA_MODE", QVariant.String))
        fields.append(QgsField("TOTAL_POP", QVariant.String))

        return fields

    def get_polygon_layer(self):

        poly_out = QgsVectorLayer("Polygon?crs=EPSG:4326", self.layer_name, "memory")

        poly_out.dataProvider().addAttributes(self.get_fields())
        poly_out.updateFields()

        return poly_out

    def get_features(self, response, id_field_value):

        # Sort features based on the isochrone value, so that longest isochrone
        # is added first. This will plot the isochrones on top of each other.
        l = lambda x: x['properties']['value']
        for isochrone in sorted(response['features'], key=l, reverse=True):
            feat = QgsFeature()
            coordinates = isochrone['geometry']['coordinates']
            iso_value = isochrone['properties']['value']
            total_pop = isochrone['properties']['total_pop']
            qgis_coords = [QgsPointXY(x, y) for x, y in coordinates[0]]
            feat.setGeometry(QgsGeometry.fromPolygonXY([qgis_coords]))
            feat.setAttributes([
                id_field_value,
                int(iso_value / self.factor),
                self.profile,
                total_pop
            ])

            yield feat

    # def calculate_difference(self, dest_id, context):
    #     """Something goes wrong here.. The parent algorithm can't see the dissolved layer.."""
    #     layer = QgsProcessingUtils.mapLayerFromString(dest_id, context)
    #
    #     dissolve_params = {
    #         'INPUT': layer,
    #         'FIELD': self.field_dimension_name,
    #         'OUTPUT': 'memory:'
    #     }
    #     dissolved = processing.run('qgis:dissolve', dissolve_params, context=context)['OUTPUT']
    #
    #     return dissolved

    def stylePoly(self, layer):
        """
        Style isochrone polygon layer

        :param layer: Polygon layer to be styled.
        :type layer: QgsMapLayer
        """

        if self.dimension == 'time':
            legend_suffix = ' mins'
        else:
            legend_suffix = ' m'

        field = layer.fields().lookupField(self.field_dimension_name)
        unique_values = sorted(layer.uniqueValues(field))

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
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())

            # configure a symbol layer
            symbol_layer = QgsSimpleFillSymbolLayer(color=colors[cid],
                                                    strokeColor=QColor('#000000'))

            # replace default symbol layer with the configured one
            if symbol_layer is not None:
                symbol.changeSymbolLayer(0, symbol_layer)

            # create renderer object
            category = QgsRendererCategory(unique_value, symbol, str(unique_value) + legend_suffix)
            # entry for the list of category items
            categories.append(category)

        # create renderer object
        renderer = QgsCategorizedSymbolRenderer(self.field_dimension_name, categories)

        # assign the created renderer to the layer
        if renderer is not None:
            layer.setRenderer(renderer)
        layer.setOpacity(0.5)

        layer.triggerRepaint()
