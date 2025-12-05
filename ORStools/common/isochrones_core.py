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

from typing import Any, Generator

from qgis.core import (
    QgsMapLayer,
    QgsPointXY,
    QgsFeature,
    QgsFields,
    QgsGeometry,
    QgsStyle,
    QgsSymbol,
    QgsSimpleFillSymbolLayer,
    QgsRendererCategory,
    QgsCategorizedSymbolRenderer,
)

from qgis.PyQt.QtCore import QMetaType
from qgis.PyQt.QtGui import QColor

from ORStools.utils.wrapper import create_qgs_field

# import processing


class Isochrones:
    """convenience class to build isochrones"""

    def __init__(self) -> None:
        # Will all be set in self.set_parameters(), bcs Processing Algo has to initialize this class before it
        # knows about its own parameters
        self.profile = None
        self.dimension = None
        self.id_field_type = None
        self.id_field_name = None
        self.factor = None
        self.field_dimension_name = None

    def set_parameters(
        self,
        profile: str,
        dimension: str,
        factor: int,
        id_field_type: QMetaType.Type.QString = QMetaType.Type.QString,
        id_field_name: str = "ID",
    ) -> None:
        """
        Sets all parameters defined in __init__, because processing algorithm calls this class when it doesn't know
        its parameters yet.

        :param profile: Transportation mode being used
        :type profile: str

        :param dimension: Unit being used, time or distance.
        :type dimension: str

        :param factor: Unit factor being used, depending on dimension.
        :type factor: int

        :param id_field_type: field type of ID field
        :type id_field_type: QMetaType enum

        :param id_field_name: field name of ID field
        :type id_field_name: str
        """
        self.profile = profile
        self.dimension = dimension
        self.id_field_type = id_field_type
        self.id_field_name = id_field_name
        self.factor = factor

        self.field_dimension_name = "AA_MINS" if self.dimension == "time" else "AA_METERS"

    def get_fields(self) -> QgsFields:
        """
        Set all fields for output isochrone layer.

        :returns: Fields object of all output fields.
        :rtype: QgsFields
        """
        fields = QgsFields()
        fields.append(create_qgs_field(self.id_field_name, self.id_field_type))  # ID field
        fields.append(create_qgs_field("CENTER_LON", QMetaType.Type.QString))
        fields.append(create_qgs_field("CENTER_LAT", QMetaType.Type.QString))
        fields.append(
            create_qgs_field(self.field_dimension_name, QMetaType.Type.Int)
        )  # Dimension field
        fields.append(create_qgs_field("AA_MODE", QMetaType.Type.QString))
        fields.append(create_qgs_field("TOTAL_POP", QMetaType.Type.QString))

        return fields

    def get_features(
        self, response: dict, id_field_value: Any
    ) -> Generator[QgsFeature, None, None]:
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
        for isochrone in sorted(
            response["features"], key=lambda x: x["properties"]["value"], reverse=True
        ):
            feat = QgsFeature()
            coordinates = isochrone["geometry"]["coordinates"]
            iso_value = isochrone["properties"]["value"]
            center = isochrone["properties"]["center"]
            total_pop = isochrone["properties"].get("total_pop")
            qgis_coords = [QgsPointXY(x, y) for x, y in coordinates[0]]
            feat.setGeometry(QgsGeometry.fromPolygonXY([qgis_coords]))
            feat.setAttributes(
                [
                    id_field_value,
                    center[0],
                    center[1],
                    int(iso_value / self.factor),
                    self.profile,
                    total_pop,
                ]
            )

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

    def stylePoly(self, layer: QgsMapLayer) -> None:
        """
        Style isochrone polygon layer.

        :param layer: Polygon layer to be styled.
        :type layer: QgsMapLayer
        """

        if self.dimension == "time":
            legend_suffix = " min"
        else:
            legend_suffix = " m"

        field = layer.fields().indexOf(self.field_dimension_name)
        unique_values = sorted(layer.uniqueValues(field))

        style = QgsStyle.defaultStyle()
        color_ramp = style.colorRamp("Spectral")
        color_ramp.invert()

        n = len(unique_values)
        max_position = 0.7 if n < 10 else 1.0
        colors = [
            color_ramp.color(i / (n - 1) * max_position) if n > 1 else color_ramp.color(0)
            for i in range(n)
        ]

        categories = []

        for cid, unique_value in enumerate(unique_values):
            # initialize the default symbol for this geometry type
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())

            # configure a symbol layer
            symbol_layer = QgsSimpleFillSymbolLayer(
                color=colors[cid], strokeColor=QColor("#000000")
            )

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
