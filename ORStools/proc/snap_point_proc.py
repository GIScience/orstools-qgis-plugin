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
    QgsProcessingParameterPoint,
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
from ORStools.utils import exceptions, logger

from ORStools.utils.wrapper import create_qgs_field


# noinspection PyPep8Naming
class ORSSnapPointAlgo(ORSBaseProcessingAlgorithm):
    def __init__(self) -> None:
        super().__init__()
        self.ALGO_NAME: str = "snap_from_point"
        self.GROUP: str = "Snap"
        self.IN_POINT: str = "IN_POINT"
        self.RADIUS: str = "RADIUS"
        self.OUT_NAME: str = "Snapping_Point"
        self.PARAMETERS: list = [
            QgsProcessingParameterPoint(
                name=self.IN_POINT,
                description=self.tr(
                    "Input Point from map canvas (mutually exclusive with layer option)"
                ),
                optional=True,
            ),
            QgsProcessingParameterNumber(
                name=self.RADIUS,
                description=self.tr("Search Radius [m]"),
                defaultValue=300,
            ),
        ]

        self.setToolTip(self.PARAMETERS[0], self.tr("Select input point from map view."))
        self.setToolTip(
            self.PARAMETERS[1],
            self.tr(
                "The radius in which to search for points. Note: usually, a limit is configured."
            ),
        )

    crs_out = QgsCoordinateReferenceSystem.fromEpsgId(4326)

    def processAlgorithm(
        self, parameters: dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, str]:
        ors_client = self.get_client(parameters, context, feedback)

        # Get profile value
        profile = dict(enumerate(PROFILES))[parameters[self.IN_PROFILE]]

        # Get parameter values
        point = self.parameterAsPoint(parameters, self.IN_POINT, context, self.crs_out)
        radius = self.parameterAsDouble(parameters, self.RADIUS, context)

        params = {
            "locations": [[round(point.x(), 6), round(point.y(), 6)]],
            "radius": radius,
            "id": None,
        }

        sink_fields = QgsFields()
        sink_fields.append(create_qgs_field("SNAPPED_NAME", QMetaType.Type.QString))
        sink_fields.append(create_qgs_field("SNAPPED_DISTANCE", QMetaType.Type.Double))

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
            point_features = get_snapped_point_features(response, feedback=feedback)

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
        return self.tr("Snap from Point")

    def icon(self):
        icon_path = GuiUtils.get_icon("icon_snap.png")
        return QIcon(icon_path)
