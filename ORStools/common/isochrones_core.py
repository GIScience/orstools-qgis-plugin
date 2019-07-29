# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ORStools
                                 A QGIS plugin
 QGIS client to query openrouteservice
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


from PyQt5.QtCore import QVariant
from PyQt5.QtGui import QColor

from qgis.core import (QgsPointXY,
                       QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsGeometry,
                       QgsSymbol,
                       QgsSimpleFillSymbolLayer,
                       QgsRendererCategory,
                       QgsCategorizedSymbolRenderer,
                       QgsProcessingUtils)
import processing

class Isochrones():
    """convenience class to build isochrones"""

    def __init__(self):

        # Will all be set in self.set_parameters(), bcs Processing Algo has to initialize this class before it
        # knows about its own parameters
        self.profile = None
        self.dimension = None
        self.id_field_type = None
        self.id_field_name = None
        self.factor = None
        self.field_dimension_name = None

    def set_parameters(self, profile, dimension, factor, id_field_type=QVariant.String, id_field_name='ID'):
        """
        Sets all parameters defined in __init__, because processing algorithm calls this class when it doesn't know its parameters yet.

        :param profile: Transportation mode being used
        :type profile: str

        :param dimension: Unit being used, time or distance.
        :type dimension: str

        :param factor: Unit factor being used, depending on dimension.
        :type factor: int

        :param id_field_type: field type of ID field
        :type id_field_type: QVariant enum

        :param id_field_name: field name of ID field
        :type id_field_name: str
        """
        self.profile = profile
        self.dimension = dimension
        self.id_field_type = id_field_type
        self.id_field_name = id_field_name
        self.factor = factor

        self.field_dimension_name = "AA_MINS" if self.dimension == 'time' else "AA_METERS"

    def get_fields(self):
        """
        Set all fields for output isochrone layer.

        :returns: Fields object of all output fields.
        :rtype: QgsFields
        """
        fields = QgsFields()
        fields.append(QgsField(self.id_field_name, self.id_field_type))  # ID field
        fields.append(QgsField(self.field_dimension_name, QVariant.Int))  # Dimension field
        fields.append(QgsField("AA_MODE", QVariant.String))
        fields.append(QgsField("TOTAL_POP", QVariant.String))

        return fields

    def get_features(self, response, id_field_value):
        """
        Generator to return output isochrone features from response.

        :param response: API response
        :type response: dict

        :param id_field_value: Value of ID field.
        :type id_field_value: any

        :returns: output feature
        :rtype: QgsFeature
        """

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
    #         'FIELD': "AA_MINS",
    #         'OUTPUT': 'memory:'
    #     }
    #     dissolved = processing.run('qgis:dissolve', dissolve_params, context=context)['OUTPUT']
    #
    #     return dissolved

    def stylePoly(self, layer):
        """
        Style isochrone polygon layer.

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
