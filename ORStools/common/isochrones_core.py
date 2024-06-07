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
    QgsPointXY,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsGraduatedSymbolRenderer,
    QgsMapLayer,
    QgsStyle,
    QgsClassificationEqualInterval,
)

from qgis.PyQt.QtCore import QVariant


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
        id_field_type: QVariant.String = QVariant.String,
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
        :type id_field_type: QVariant enum

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
        fields.append(QgsField(self.id_field_name, self.id_field_type))  # ID field
        fields.append(QgsField("CENTER_LON", QVariant.String))
        fields.append(QgsField("CENTER_LAT", QVariant.String))
        fields.append(QgsField(self.field_dimension_name, QVariant.Int))  # Dimension field
        fields.append(QgsField("AA_MODE", QVariant.String))
        fields.append(QgsField("TOTAL_POP", QVariant.String))

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

        field = layer.fields().indexOf(self.field_dimension_name)
        unique_values = sorted(layer.uniqueValues(field))

        classification_method = QgsClassificationEqualInterval()
        ramp_name = "Spectral"
        default_style = QgsStyle().defaultStyle()
        color_ramp = default_style.colorRamp(ramp_name)
        num_classes = len(unique_values)

        renderer = QgsGraduatedSymbolRenderer(self.field_dimension_name)
        renderer.setSourceColorRamp(color_ramp)
        renderer.setClassificationMethod(classification_method)
        renderer.updateClasses(layer, num_classes)

        # assign the created renderer to the layer
        if renderer is not None:
            layer.setRenderer(renderer)
        layer.setOpacity(0.5)

        layer.triggerRepaint()
