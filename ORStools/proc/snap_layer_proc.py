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

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QMetaType
from qgis.core import (
    QgsProcessingParameterFeatureSource,
    QgsProcessing,
    QgsProcessingParameterNumber,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsWkbTypes,
    QgsFields,
    QgsCoordinateReferenceSystem,
)

from ORStools.common import PROFILES
from ORStools.utils.gui import GuiUtils
from ORStools.utils.processing import get_snapped_point_features
from ORStools.proc.base_processing_algorithm import ORSBaseProcessingAlgorithm
from ORStools.utils import exceptions, logger, transform

from ORStools.utils.wrapper import create_qgs_field


# noinspection PyPep8Naming
class ORSSnapLayerAlgo(ORSBaseProcessingAlgorithm):
    def __init__(self) -> None:
        super().__init__()
        self.ALGO_NAME: str = "snap_from_point_layer"
        self.GROUP: str = "Snap"
        self.IN_POINTS: str = "IN_POINTS"
        self.RADIUS: str = "RADIUS"
        self.OUT_NAME: str = "Snapping_Layer"
        self.PARAMETERS: list = [
            QgsProcessingParameterFeatureSource(
                name=self.IN_POINTS,
                description=self.tr("Input Point Layer"),
                types=[QgsProcessing.SourceType.TypeVectorPoint],
            ),
            QgsProcessingParameterNumber(
                name=self.RADIUS,
                description=self.tr("Search Radius [m]"),
                defaultValue=300,
            ),
        ]

    def processAlgorithm(
        self, parameters: dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, str]:
        ors_client = self._get_ors_client_from_provider(parameters[self.IN_PROVIDER], feedback)

        # Get profile value
        profile = dict(enumerate(PROFILES))[parameters[self.IN_PROFILE]]

        # Get parameter values
        source = self.parameterAsSource(parameters, self.IN_POINTS, context)
        radius = self.parameterAsDouble(parameters, self.RADIUS, context)

        sources_features = list(source.getFeatures())

        x_former = transform.transformToWGS(source.sourceCrs())
        sources_features_x_formed = [
            x_former.transform(feat.geometry().asPoint()) for feat in sources_features
        ]

        params = {
            "locations": [[point.x(), point.y()] for point in sources_features_x_formed],
            "radius": radius,
            "id": None,
        }

        sink_fields = QgsFields()
        sink_fields.append(create_qgs_field("NAME", QMetaType.Type.QString))
        sink_fields.append(create_qgs_field("SNAPPED_DISTANCE", QMetaType.Type.Double))

        source_fields = [field for field in source.fields()]

        for field in source_fields:
            if field.name() in ["SNAPPED_DISTANCE", "SNAPPED_NAME"]:
                raise Exception(
                    self.tr(
                        'Source layer may not contain field names "SNAPPED_DISTANCE" or "SNAPPED_NAME"'
                    )
                )
            sink_fields.append(field)

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUT,
            context,
            sink_fields,
            QgsWkbTypes.Type.Point,
            QgsCoordinateReferenceSystem.fromEpsgId(4326),
        )

        # Make request and catch ApiError
        try:
            response = ors_client.fetch_with_retry("/v2/snap/" + profile, {}, post_json=params)
            point_features = get_snapped_point_features(response, sources_features, feedback)

            for feat in point_features:
                sink.addFeature(feat)

        except (exceptions.ApiError, exceptions.InvalidKey, exceptions.GenericServerError) as e:
            msg = f"{e.__class__.__name__}: {str(e)}"
            feedback.reportError(msg)
            logger.log(msg)

        return {self.OUT: dest_id}

    def displayName(self) -> str:
        """
        Algorithm name shown in QGIS toolbox
        :return:
        """
        return self.tr("Snap from Point Layer")

    def icon(self):
        icon_path = GuiUtils.get_icon("icon_snap.png")
        return QIcon(icon_path)
