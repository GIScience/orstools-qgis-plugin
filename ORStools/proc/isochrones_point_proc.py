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

from qgis.core import (QgsWkbTypes,
                       QgsCoordinateReferenceSystem,
                       QgsProcessingUtils,
                       QgsProcessingParameterString,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterPoint,
                       )

from ORStools.common import isochrones_core, PROFILES, DIMENSIONS
from ORStools.utils import exceptions, logger
from .base_processing_algorithm import ORSBaseProcessingAlgorithm


# noinspection PyPep8Naming
class ORSIsochronesPointAlgo(ORSBaseProcessingAlgorithm):
    def __init__(self):
        super().__init__()
        self.ALGO_NAME = 'isochrones_from_point'
        self.GROUP = "Isochrones"
        self.IN_POINT = "INPUT_POINT"
        self.IN_METRIC = 'INPUT_METRIC'
        self.IN_RANGES = 'INPUT_RANGES'
        self.IN_KEY = 'INPUT_APIKEY'
        self.IN_DIFFERENCE = 'INPUT_DIFFERENCE'
        self.PARAMETERS = [
            QgsProcessingParameterPoint(
                name=self.IN_POINT,
                description="Input Point from map canvas (mutually exclusive with layer option)",
                optional=True
            ),
            QgsProcessingParameterEnum(
                name=self.IN_METRIC,
                description="Dimension",
                options=DIMENSIONS,
                defaultValue=DIMENSIONS[0]
            ),
            QgsProcessingParameterString(
                name=self.IN_RANGES,
                description="Comma-separated ranges [min or m]",
                defaultValue="5, 10"
            )
        ]

    # Save some important references
    # TODO bad style, refactor
    isochrones = isochrones_core.Isochrones()
    dest_id = None
    crs_out = QgsCoordinateReferenceSystem.fromEpsgId(4326)
    # difference = None

    # TODO: preprocess parameters to options the range cleanup below:
    # https://www.qgis.org/pyqgis/master/core/Processing/QgsProcessingAlgorithm.html#qgis.core.QgsProcessingAlgorithm.preprocessParameters
    def processAlgorithm(self, parameters, context, feedback):
        ors_client = self._get_ors_client_from_provider(parameters[self.IN_PROVIDER], feedback)

        profile = dict(enumerate(PROFILES))[parameters[self.IN_PROFILE]]
        dimension = dict(enumerate(DIMENSIONS))[parameters[self.IN_METRIC]]

        factor = 60 if dimension == 'time' else 1
        ranges_raw = parameters[self.IN_RANGES]
        ranges_proc = [x * factor for x in map(int, ranges_raw.split(','))]

        options = self.parseOptions(parameters, context)

        point = self.parameterAsPoint(parameters, self.IN_POINT, context, self.crs_out)

        # Make the actual requests
        # If layer source is set
        self.isochrones.set_parameters(profile, dimension, factor)
        params = {
            "locations": [[round(point.x(), 6), round(point.y(), 6)]],
            "range_type": dimension,
            "range": ranges_proc,
            "attributes": ['total_pop'],
            "id": None,
            "options": options
        }

        (sink, self.dest_id) = self.parameterAsSink(parameters, self.OUT, context,
                                                    self.isochrones.get_fields(),
                                                    QgsWkbTypes.Polygon,
                                                    # Needs Multipolygon if difference parameter will ever be
                                                    # reactivated
                                                    self.crs_out)

        try:
            response = ors_client.request('/v2/isochrones/' + profile, {}, post_json=params)

            # Populate features from response
            for isochrone in self.isochrones.get_features(response, params['id']):
                sink.addFeature(isochrone)

        except (exceptions.ApiError,
                exceptions.InvalidKey,
                exceptions.GenericServerError) as e:
            msg = f"Feature ID {params['id']} caused a {e.__class__.__name__}:\n{str(e)}"
            feedback.reportError(msg)
            logger.log(msg, 2)

        return {self.OUT: self.dest_id}

    # noinspection PyUnusedLocal
    def postProcessAlgorithm(self, context, feedback):
        """Style polygon layer in post-processing step."""
        processed_layer = QgsProcessingUtils.mapLayerFromString(self.dest_id, context)
        self.isochrones.stylePoly(processed_layer)

        return {self.OUT: self.dest_id}
