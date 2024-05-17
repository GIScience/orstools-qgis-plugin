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
    QgsCoordinateReferenceSystem,
    QgsProcessingUtils,
    QgsProcessingParameterString,
    QgsProcessingParameterEnum,
    QgsProcessingParameterPoint,
    QgsProcessingParameterNumber,
    QgsProcessingContext,
    QgsProcessingFeedback,
)

from ORStools.common import isochrones_core, PROFILES, DIMENSIONS, LOCATION_TYPES
from ORStools.utils import exceptions, logger
from .base_processing_algorithm import ORSBaseProcessingAlgorithm


# noinspection PyPep8Naming
class ORSIsochronesPointAlgo(ORSBaseProcessingAlgorithm):
    def __init__(self):
        super().__init__()
        self.ALGO_NAME: str = "isochrones_from_point"
        self.GROUP: str = "Isochrones"
        self.IN_POINT: str = "INPUT_POINT"
        self.IN_METRIC: str = "INPUT_METRIC"
        self.IN_RANGES: str = "INPUT_RANGES"
        self.IN_KEY: str = "INPUT_APIKEY"
        self.IN_DIFFERENCE: str = "INPUT_DIFFERENCE"
        self.IN_SMOOTHING: str = "INPUT_SMOOTHING"
        self.LOCATION_TYPE: str = "LOCATION_TYPE"
        self.PARAMETERS: list = [
            QgsProcessingParameterPoint(
                name=self.IN_POINT,
                description=self.tr(
                    "Input Point from map canvas (mutually exclusive with layer option)"
                ),
                optional=True,
            ),
            QgsProcessingParameterEnum(
                name=self.IN_METRIC,
                description=self.tr("Dimension"),
                options=DIMENSIONS,
                defaultValue=DIMENSIONS[0],
            ),
            QgsProcessingParameterString(
                name=self.IN_RANGES,
                description=self.tr("Comma-separated ranges [min or m]"),
                defaultValue="5, 10",
            ),
            QgsProcessingParameterNumber(
                name=self.IN_SMOOTHING,
                description=self.tr("Smoothing factor between 0 [detailed] and 100 [generalized]"),
                defaultValue=None,
                minValue=0,
                maxValue=100,
                optional=True,
            ),
            QgsProcessingParameterEnum(
                name=self.LOCATION_TYPE,
                description=self.tr("Location Type"),
                options=LOCATION_TYPES,
                defaultValue=LOCATION_TYPES[0],
            ),
        ]

    # Save some important references
    # TODO bad style, refactor
    isochrones = isochrones_core.Isochrones()
    dest_id = None
    crs_out = QgsCoordinateReferenceSystem.fromEpsgId(4326)
    # difference = None

    # TODO: preprocess parameters to options the range cleanup below:
    # https://www.qgis.org/pyqgis/master/core/Processing/QgsProcessingAlgorithm.html#qgis.core.QgsProcessingAlgorithm.preprocessParameters
    def processAlgorithm(
        self, parameters: dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, str]:
        ors_client = self._get_ors_client_from_provider(parameters[self.IN_PROVIDER], feedback)

        profile = dict(enumerate(PROFILES))[parameters[self.IN_PROFILE]]
        dimension = dict(enumerate(DIMENSIONS))[parameters[self.IN_METRIC]]
        location_type = dict(enumerate(LOCATION_TYPES))[parameters[self.LOCATION_TYPE]]

        factor = 60 if dimension == "time" else 1
        ranges_raw = parameters[self.IN_RANGES]
        ranges_proc = [x * factor for x in map(float, ranges_raw.split(","))]
        # round to the nearest second or meter
        ranges_proc = list(map(int, ranges_proc))
        smoothing = parameters[self.IN_SMOOTHING]

        options = self.parseOptions(parameters, context)

        point = self.parameterAsPoint(parameters, self.IN_POINT, context, self.crs_out)

        # Make the actual requests
        # If layer source is set
        self.isochrones.set_parameters(profile, dimension, factor)
        params = {
            "locations": [[round(point.x(), 6), round(point.y(), 6)]],
            "range_type": dimension,
            "range": ranges_proc,
            "attributes": ["total_pop"],
            "id": None,
            "options": options,
            "location_type": location_type,
        }

        if smoothing or smoothing == 0:
            params["smoothing"] = smoothing

        (sink, self.dest_id) = self.parameterAsSink(
            parameters,
            self.OUT,
            context,
            self.isochrones.get_fields(),
            QgsWkbTypes.Type.Polygon,
            # Needs Multipolygon if difference parameter will ever be
            # reactivated
            self.crs_out,
        )

        try:
            response = ors_client.request("/v2/isochrones/" + profile, {}, post_json=params)

            # Populate features from response
            for isochrone in self.isochrones.get_features(response, params["id"]):
                sink.addFeature(isochrone)

        except (exceptions.ApiError, exceptions.InvalidKey, exceptions.GenericServerError) as e:
            msg = f"Feature ID {params['id']} caused a {e.__class__.__name__}:\n{str(e)}"
            feedback.reportError(msg)
            logger.log(msg, 2)

        return {self.OUT: self.dest_id}

    # noinspection PyUnusedLocal
    def postProcessAlgorithm(self, context, feedback) -> Dict[str, str]:
        """Style polygon layer in post-processing step."""
        processed_layer = QgsProcessingUtils.mapLayerFromString(self.dest_id, context)
        self.isochrones.stylePoly(processed_layer)

        return {self.OUT: self.dest_id}

    def displayName(self) -> str:
        """
        Algorithm name shown in QGIS toolbox
        :return:
        """
        return self.tr("Isochrones from Point")
