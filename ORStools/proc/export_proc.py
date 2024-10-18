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

from typing import Dict

from qgis.core import (
    QgsWkbTypes,
    QgsFeature,
    QgsField,
    QgsFields,
    QgsProject,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsProcessingParameterExtent,
    QgsProcessingParameterFeatureSink,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsPointXY,
    QgsGeometry,
)

from qgis.PyQt.QtCore import QVariant

from qgis.utils import iface


from ORStools.common import PROFILES
from ORStools.utils import exceptions, logger
from .base_processing_algorithm import ORSBaseProcessingAlgorithm


# noinspection PyPep8Naming
class ORSExportAlgo(ORSBaseProcessingAlgorithm):
    def __init__(self):
        super().__init__()
        self.ALGO_NAME: str = "export_network_from_map"
        self.GROUP: str = "Export"
        self.IN_EXPORT: str = "INPUT_EXPORT"
        self.OUT_POINT = "OUTPUT_POINT"
        self.PARAMETERS: list = [
            QgsProcessingParameterExtent(
                name=self.IN_EXPORT,
                description=self.tr("Input Extent"),
            ),
            QgsProcessingParameterFeatureSink(
                name=self.OUT_POINT,
                description="Node Export",
            ),
        ]

    def processAlgorithm(
        self, parameters: dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, str]:
        ors_client = self._get_ors_client_from_provider(parameters[self.IN_PROVIDER], feedback)

        # Get profile value
        profile = dict(enumerate(PROFILES))[parameters[self.IN_PROFILE]]

        target_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        rect = self.parameterAsExtent(parameters, self.IN_EXPORT, context, crs=target_crs)

        extent = [[rect.xMinimum(), rect.yMinimum()], [rect.xMaximum(), rect.yMaximum()]]

        params = {
            "bbox": extent,
            "id": "export_request",
        }

        (sink_line, dest_id_line) = self.parameterAsSink(
            parameters,
            self.OUT,
            context,
            self.get_fields_line(),
            QgsWkbTypes.Type.LineString,
            QgsCoordinateReferenceSystem.fromEpsgId(4326),
        )

        (sink_point, dest_id_point) = self.parameterAsSink(
            parameters,
            self.OUT_POINT,
            context,
            self.get_fields_point(),
            QgsWkbTypes.Type.Point,
            QgsCoordinateReferenceSystem.fromEpsgId(4326),
        )

        # Make request and catch ApiError
        try:
            response = ors_client.request("/v2/export/" + profile, {}, post_json=params)
            nodes_dict = {item["nodeId"]: item["location"] for item in response["nodes"]}
            edges = response["edges"]
            for edge in edges:
                from_id = edge["fromId"]
                to_id = edge["toId"]
                weight = edge["weight"]

                to_coords = nodes_dict[to_id]
                from_coords = nodes_dict[from_id]

                geometry = QgsGeometry.fromPolylineXY(
                    [
                        QgsPointXY(from_coords[0], from_coords[1]),
                        QgsPointXY(to_coords[0], to_coords[1]),
                    ]
                )

                feat = QgsFeature()
                feat.setGeometry(geometry)
                feat.setAttributes([from_id, to_id, weight])
                sink_line.addFeature(feat)

            unique_coordinates = {
                tuple(item["location"]): item["nodeId"] for item in response["nodes"]
            }
            points = [(coords, node_id) for coords, node_id in unique_coordinates.items()]
            for item in points:
                point = QgsPointXY(item[0][0], item[0][1])
                point_geometry = QgsGeometry.fromPointXY(point)

                point_feat = QgsFeature()
                point_feat.setGeometry(point_geometry)
                point_feat.setAttributes([item[1]])
                sink_point.addFeature(point_feat)

        except (exceptions.ApiError, exceptions.InvalidKey, exceptions.GenericServerError) as e:
            msg = f"{e.__class__.__name__}: {str(e)}"
            feedback.reportError(msg)
            logger.log(msg)

        return {self.OUT: dest_id_line, self.OUT_POINT: dest_id_point}

    @staticmethod
    def get_fields_line():
        fields = QgsFields()
        fields.append(QgsField("FROM_ID", QVariant.Double))
        fields.append(QgsField("TO_ID", QVariant.Double))
        fields.append(QgsField("WEIGHT", QVariant.Double))

        return fields

    @staticmethod
    def get_fields_point():
        fields = QgsFields()
        fields.append(QgsField("ID", QVariant.Int))

        return fields

    def displayName(self) -> str:
        """
        Algorithm name shown in QGIS toolbox
        :return:
        """
        return self.tr("Export Network from Map")
