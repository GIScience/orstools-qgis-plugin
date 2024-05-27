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

from qgis.PyQt.QtCore import QVariant
from qgis.core import (QgsProcessingParameterFeatureSource,
                       QgsProcessing,
                       QgsProcessingParameterNumber,
                       QgsProcessingContext,
                       QgsProcessingFeedback,
                       QgsWkbTypes,
                       QgsFields,
                       QgsCoordinateReferenceSystem,
                       QgsField
                       )

from ORStools.common import PROFILES
from ORStools.common.snap_core import get_snapped_point_features
from ORStools.proc.base_processing_algorithm import ORSBaseProcessingAlgorithm
from ORStools.utils import exceptions, logger, transform


# noinspection PyPep8Naming
class ORSSnapAlgo(ORSBaseProcessingAlgorithm):
    def __init__(self):
        super().__init__()
        self.ALGO_NAME: str = "snap_from_point_layer"
        self.GROUP: str = "Snap"
        self.IN_POINTS = "IN_POINTS"
        self.RADIUS = "RADIUS"
        self.PARAMETERS: list = [
            QgsProcessingParameterFeatureSource(
                name=self.IN_POINTS,
                description=self.tr("Input Point layer"),
                types=[QgsProcessing.SourceType.TypeVectorPoint],
            ),
            QgsProcessingParameterNumber(
                name=self.RADIUS,
                description=self.tr("Search Radius [m]"),
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
            "radius": radius
        }

        # Make request and catch ApiError
        try:
            response = ors_client.request("/v2/snap/" + profile, {}, post_json=params)

        except (exceptions.ApiError, exceptions.InvalidKey, exceptions.GenericServerError) as e:
            msg = f"{e.__class__.__name__}: {str(e)}"
            feedback.reportError(msg)
            logger.log(msg)

        sink_fields = QgsFields()
        sink_fields.append(QgsField("NAME", QVariant.String))
        sink_fields.append(QgsField("SNAPPED_DISTANCE", QVariant.Double))

        (sink, dest_id) = self.parameterAsSink(
            parameters, self.OUT, context, sink_fields, QgsWkbTypes.Type.Point, QgsCoordinateReferenceSystem.fromEpsgId(4326)
        )

        point_features = get_snapped_point_features(response)

        for feat in point_features:
            sink.addFeature(feat)

        return {self.OUT: dest_id}


    def displayName(self) -> str:
        """
        Algorithm name shown in QGIS toolbox
        :return:
        """
        return self.tr("Snap from Point Layer")
