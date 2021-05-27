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

import os.path
from qgis.core import (QgsWkbTypes,
                       QgsCoordinateReferenceSystem,
                       QgsProcessingUtils,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterString,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterPoint,
                       )

from PyQt5.QtGui import QIcon

from ORStools import RESOURCE_PREFIX, __help__
from ORStools.common import client, isochrones_core, PROFILES, DIMENSIONS
from ORStools.utils import exceptions, configmanager, logger
from . import HELP_DIR


class ORSisochronesPointAlgo(QgsProcessingAlgorithm):
    # TODO: create base algorithm class common to all modules

    ALGO_NAME = 'isochrones_from_point'
    ALGO_NAME_LIST = ALGO_NAME.split('_')

    IN_PROVIDER = "INPUT_PROVIDER"
    IN_POINT = "INPUT_POINT"
    IN_PROFILE = "INPUT_PROFILE"
    IN_METRIC = 'INPUT_METRIC'
    IN_RANGES = 'INPUT_RANGES'
    IN_KEY = 'INPUT_APIKEY'
    IN_DIFFERENCE = 'INPUT_DIFFERENCE'
    OUT = 'OUTPUT'

    # Save some important references
    isochrones = isochrones_core.Isochrones()
    dest_id = None
    crs_out = QgsCoordinateReferenceSystem.fromEpsgId(4326)
    # difference = None

    # noinspection PyUnusedLocal
    def initAlgorithm(self, configuration):

        providers = [provider['name'] for provider in configmanager.read_config()['providers']]
        self.addParameter(
            QgsProcessingParameterEnum(
                self.IN_PROVIDER,
                "Provider",
                providers,
                defaultValue=providers[0]
            )
        )

        self.addParameter(
            QgsProcessingParameterPoint(
                name=self.IN_POINT,
                description="Input Point from map canvas (mutually exclusive with layer option)",
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.IN_PROFILE,
                "Travel mode",
                PROFILES,
                defaultValue=PROFILES[0]
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                name=self.IN_METRIC,
                description="Dimension",
                options=DIMENSIONS,
                defaultValue=DIMENSIONS[0]
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                name=self.IN_RANGES,
                description="Comma-separated ranges [mins or m]",
                defaultValue="5, 10"
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                name=self.OUT,
                description="Isochrones",
                createByDefault=False
            )
        )

    def group(self):
        return "Isochrones"

    def groupId(self):
        return 'isochrones'

    def name(self):
        return self.ALGO_NAME

    def shortHelpString(self):
        """Displays the sidebar help in the algorithm window"""

        file = os.path.join(
            HELP_DIR,
            'algorithm_isochrone_point.help'
        )
        with open(file, encoding='utf-8') as helpf:
            msg = helpf.read()

        return msg

    def helpUrl(self):
        """will be connected to the Help button in the Algorithm window"""
        return __help__

    def displayName(self):
        return " ".join(map(lambda x: x.capitalize(), self.ALGO_NAME_LIST))

    def icon(self):
        return QIcon(RESOURCE_PREFIX + 'icon_isochrones.png')

    def createInstance(self):
        return ORSisochronesPointAlgo()

    # TODO: preprocess parameters to options the range cleanup below:
    # https://www.qgis.org/pyqgis/master/core/Processing/QgsProcessingAlgorithm.html#qgis.core.QgsProcessingAlgorithm.preprocessParameters

    def processAlgorithm(self, parameters, context, feedback):
        # Init ORS client
        providers = configmanager.read_config()['providers']
        provider = providers[self.parameterAsEnum(parameters, self.IN_PROVIDER, context)]
        clnt = client.Client(provider)
        clnt.overQueryLimit.connect(lambda : feedback.reportError("OverQueryLimit: Retrying..."))

        params = dict()
        params['attributes'] = ['total_pop']

        profile = PROFILES[self.parameterAsEnum(parameters, self.IN_PROFILE, context)]
        params['range_type'] = dimension = DIMENSIONS[self.parameterAsEnum(parameters, self.IN_METRIC, context)]

        factor = 60 if params['range_type'] == 'time' else 1
        ranges_raw = self.parameterAsString(parameters, self.IN_RANGES, context)
        ranges_proc = [x * factor for x in map(int, ranges_raw.split(','))]
        params['range'] = ranges_proc

        point = self.parameterAsPoint(parameters, self.IN_POINT, context, self.crs_out)

        # Make the actual requests
        # If layer source is set
        requests = []
        self.isochrones.set_parameters(profile, dimension, factor)
        params['locations'] = [[round(point.x(), 6), round(point.y(), 6)]]
        params['id'] = None
        requests.append(params)

        (sink, self.dest_id) = self.parameterAsSink(parameters, self.OUT, context,
                                                    self.isochrones.get_fields(),
                                                    QgsWkbTypes.Polygon,  # Needs Multipolygon if difference parameter will ever be reactivated
                                                    self.crs_out)

        # If feature causes error, report and continue with next
        try:
            # Populate features from response
            response = clnt.request('/v2/isochrones/' + profile, {}, post_json=params)

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
        processed_layer= QgsProcessingUtils.mapLayerFromString(self.dest_id, context)
        self.isochrones.stylePoly(processed_layer)

        return {self.OUT: self.dest_id}
