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
        self.PARAMETERS: list = [
            QgsProcessingParameterExtent(
                name=self.IN_EXPORT,
                description=self.tr("Input Extent"),
            ),
        ]

    def processAlgorithm(
        self, parameters: dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, str]:
        ors_client = self._get_ors_client_from_provider(parameters[self.IN_PROVIDER], feedback)

        # Get profile value
        profile = dict(enumerate(PROFILES))[parameters[self.IN_PROFILE]]

        rect = self.parameterAsExtent(parameters, self.IN_EXPORT, context)

        target_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        source_crs = iface.mapCanvas().mapSettings().destinationCrs()

        transform = QgsCoordinateTransform(source_crs, target_crs, QgsProject.instance())

        bottom_left = transform.transform(rect.xMinimum(), rect.yMinimum())
        top_right = transform.transform(rect.xMaximum(), rect.yMaximum())

        extent = [[bottom_left.x(), bottom_left.y()], [top_right.x(), top_right.y()]]

        params = {
            "bbox": extent,
            "id": "export_request",
        }

        sink_fields = self.get_fields()

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUT,
            context,
            sink_fields,
            QgsWkbTypes.Type.LineString,
            QgsCoordinateReferenceSystem.fromEpsgId(4326),
        )

        # Make request and catch ApiError
        try:
            response = ors_client.request("/v2/export/" + profile, {}, post_json=params)
            nodes_dict = {item['nodeId']: item['location'] for item in response["nodes"]}
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
                sink.addFeature(feat)

        except (exceptions.ApiError, exceptions.InvalidKey, exceptions.GenericServerError) as e:
            msg = f"{e.__class__.__name__}: {str(e)}"
            feedback.reportError(msg)
            logger.log(msg)

        return {self.OUT: dest_id}

    @staticmethod
    def get_fields():
        fields = QgsFields()
        fields.append(QgsField("FROM_ID", QVariant.Double))
        fields.append(QgsField("TO_ID", QVariant.Double))
        fields.append(QgsField("WEIGHT", QVariant.Double))

        return fields

    def displayName(self) -> str:
        """
        Algorithm name shown in QGIS toolbox
        :return:
        """
        return self.tr("Export Network from Map")
