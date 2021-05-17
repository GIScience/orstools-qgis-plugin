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

from PyQt5.QtGui import QIcon

from qgis.core import (QgsWkbTypes,
                       QgsCoordinateReferenceSystem,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterBoolean,
                       QgsPointXY,
                       )
from . import HELP_DIR
from ORStools import RESOURCE_PREFIX, __help__
from ORStools.common import client, directions_core, PROFILES, PREFERENCES
from ORStools.utils import configmanager, transform, exceptions,logger, convert


class ORSdirectionsPointsLayerAlgo(QgsProcessingAlgorithm):
    """Algorithm class for Directions Lines."""

    ALGO_NAME = 'directions_from_points_1_layer'
    ALGO_NAME_LIST = ALGO_NAME.split('_')

    IN_PROVIDER = "INPUT_PROVIDER"
    IN_POINTS = "INPUT_POINT_LAYER"
    IN_FIELD = "INPUT_LAYER_FIELD"
    IN_PROFILE = "INPUT_PROFILE"
    IN_PREFERENCE = "INPUT_PREFERENCE"
    IN_OPTIMIZE = "INPUT_OPTIMIZE"
    IN_MODE = "INPUT_MODE"
    OUT = 'OUTPUT'

    def initAlgorithm(self, configuration, p_str=None, Any=None, *args, **kwargs):

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
            QgsProcessingParameterFeatureSource(
                name=self.IN_POINTS,
                description="Input (Multi)Point layer",
                types=[QgsProcessing.TypeVectorPoint],
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                name=self.IN_FIELD,
                description="Layer ID Field",
                parentLayerParameterName=self.IN_POINTS,
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
                self.IN_PREFERENCE,
                "Travel preference",
                PREFERENCES,
                defaultValue=PREFERENCES[0]
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.IN_OPTIMIZE,
                description="Optimize waypoint order (except first and last)",
                defaultValue=False
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                name=self.OUT,
                description="Output Layer",
            )
        )

    def group(self):
        return "Directions"

    def groupId(self):
        return 'directions'

    def name(self):
        return self.ALGO_NAME

    def shortHelpString(self):
        """Displays the sidebar help in the algorithm window"""

        file = os.path.join(
            HELP_DIR,
            'algorithm_directions_line.help'
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
        return QIcon(RESOURCE_PREFIX + 'icon_directions.png')

    def createInstance(self):
        return ORSdirectionsPointsLayerAlgo()

    def processAlgorithm(self, parameters, context, feedback):
        # Init ORS client

        providers = configmanager.read_config()['providers']
        provider = providers[self.parameterAsEnum(parameters, self.IN_PROVIDER, context)]
        clnt = client.Client(provider)
        clnt.overQueryLimit.connect(lambda : feedback.reportError("OverQueryLimit: Retrying..."))

        profile = PROFILES[self.parameterAsEnum(
            parameters,
            self.IN_PROFILE,
            context
        )]

        preference = PREFERENCES[self.parameterAsEnum(
            parameters,
            self.IN_PREFERENCE,
            context
        )]

        optimize = self.parameterAsBool(
            parameters,
            self.IN_OPTIMIZE,
            context
        )

        # Get parameter values
        source = self.parameterAsSource(
            parameters,
            self.IN_POINTS,
            context
        )

        source_field_idx = self.parameterAsEnum(
            parameters,
            self.IN_FIELD,
            context
        )

        source_field_name = self.parameterAsString(
            parameters,
            self.IN_FIELD,
            context
        )

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUT, context,
                                               directions_core.get_fields(from_type=source.fields().field(source_field_name).type(),
                                                                          from_name=source_field_name,
                                                                          line=True),
                                               QgsWkbTypes.LineString,
                                               QgsCoordinateReferenceSystem.fromEpsgId(4326))
        count = source.featureCount()

        input_points = list()
        from_values = list()
        xformer = transform.transformToWGS(source.sourceCrs())

        if source.wkbType() == QgsWkbTypes.Point:
            points = list()
            for feat in sorted(source.getFeatures(), key=lambda f: f.id()):
                points.append(xformer.transform(QgsPointXY(feat.geometry().asPoint())))
            input_points.append(points)
            from_values.append(None)
        elif source.wkbType() == QgsWkbTypes.MultiPoint:
            # loop through multipoint features
            for feat in sorted(source.getFeatures(), key=lambda f: f.id()):
                points = list()
                for point in feat.geometry().asMultiPoint():
                    points.append(xformer.transform(QgsPointXY(point)))
                input_points.append(points)
                from_values.append(feat[source_field_name])

        for num, (points, from_value) in enumerate(zip(input_points, from_values)):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            try:
                if optimize:
                    params = self._get_params_optimize(points, profile)
                    response = clnt.request('/optimization', {}, post_json=params)

                    sink.addFeature(directions_core.get_output_features_optimization(
                        response,
                        profile,
                        from_value=from_value
                    ))
                else:
                    params = self._get_params_directions(points, profile, preference)
                    response = clnt.request('/v2/directions/' + profile + '/geojson', {}, post_json=params)

                    sink.addFeature(directions_core.get_output_feature_directions(
                        response,
                        profile,
                        preference,
                        from_value=from_value
                    ))
            except (exceptions.ApiError,
                    exceptions.InvalidKey,
                    exceptions.GenericServerError) as e:
                msg = f"Feature ID {from_value} caused a {e.__class__.__name__}:\n{str(e)}"
                feedback.reportError(msg)
                logger.log(msg)
                continue

            feedback.setProgress(int(100.0 / count * num))

        return {self.OUT: dest_id}

    @staticmethod
    def _get_params_directions(points, profile, preference):
        """
        Build parameters for optimization endpoint

        :param points: individual points
        :type points: list of QgsPointXY

        :param profile: transport profile to be used
        :type profile: str

        :param preference: routing preference, shortest/fastest/recommended
        :type preference: str

        :returns: parameters for optimization endpoint
        :rtype: dict
        """

        params = {
            'coordinates': [[round(point.x(), 6), round(point.y(), 6)] for point in points],
            'preference': preference,
            'geometry': 'true',
            'instructions': 'false',
            'elevation': True,
            'id': None
        }

        return params

    @staticmethod
    def _get_params_optimize(points, profile):
        """
        Build parameters for optimization endpoint

        :param points: individual points list
        :type points: list of QgsPointXY

        :param profile: transport profile to be used
        :type profile: str

        :returns: parameters for optimization endpoint
        :rtype: dict
        """

        start = points.pop(0)
        end = points.pop(-1)

        params = {
            'jobs': list(),
            'vehicles': [{
                "id": 0,
                "profile": profile,
                "start": [start.x(), start.y()],
                "end": [end.x(), end.y()]
            }],
            'options': {'g': True}
        }
        for point in points:
            params['jobs'].append({
                "location": [point.x(), point.y()],
                "id": points.index(point)
            })

        return params
