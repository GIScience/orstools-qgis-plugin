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


class ORSdirectionsLinesAlgo(QgsProcessingAlgorithm):
    """Algorithm class for Directions Lines."""

    ALGO_NAME = 'directions_from_polylines_layer'
    ALGO_NAME_LIST = ALGO_NAME.split('_')

    IN_PROVIDER = "INPUT_PROVIDER"
    IN_LINES = "INPUT_LINE_LAYER"
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
                name=self.IN_LINES,
                description="Input Line layer",
                types=[QgsProcessing.TypeVectorLine],
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                name=self.IN_FIELD,
                description="Layer ID Field",
                parentLayerParameterName=self.IN_LINES,
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
        return ORSdirectionsLinesAlgo()

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
            self.IN_LINES,
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
                                               source.wkbType(),
                                               QgsCoordinateReferenceSystem.fromEpsgId(4326))
        count = source.featureCount()

        for num, (line, field_value) in enumerate(self._get_sorted_lines(source, source_field_name)):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            try:
                if optimize:
                    params = self._get_params_optimize(line, profile)
                    response = clnt.request('/optimization', {}, post_json=params)

                    sink.addFeature(directions_core.get_output_features_optimization(
                        response,
                        profile,
                        from_value=field_value
                    ))
                else:
                    params = self._get_params_directions(line, profile, preference)
                    response = clnt.request('/v2/directions/' + profile + '/geojson', {}, post_json=params)

                    sink.addFeature(directions_core.get_output_feature_directions(
                        response,
                        profile,
                        preference,
                        from_value=field_value
                    ))
            except (exceptions.ApiError,
                    exceptions.InvalidKey,
                    exceptions.GenericServerError) as e:
                msg = f"Feature ID {line[source_field_name]} caused a {e.__class__.__name__}:\n{str(e)}"
                feedback.reportError(msg)
                logger.log(msg)
                continue

            feedback.setProgress(int(100.0 / count * num))

        return {self.OUT: dest_id}

    @staticmethod
    def _get_sorted_lines(layer, field_name):
        """
        Generator to yield geometry and ID value sorted by feature ID. Careful: feat.id() is not necessarily
        permanent

        :param layer: source input layer
        :type layer: QgsProcessingParameterFeatureSource

        :param field_name: name of ID field
        :type field_name: str
        """
        # First get coordinate transformer
        xformer = transform.transformToWGS(layer.sourceCrs())

        for feat in sorted(layer.getFeatures(), key=lambda f: f.id()):
            line = None
            field_value = feat[field_name]
            # for
            if layer.wkbType() == QgsWkbTypes.MultiLineString:
                # TODO: only takes the first polyline geometry from the multiline geometry currently
                # Loop over all polyline geometries
                line = [xformer.transform(QgsPointXY(point)) for point in feat.geometry().asMultiPolyline()[0]]

            elif layer.wkbType() == QgsWkbTypes.LineString:
                line = [xformer.transform(QgsPointXY(point)) for point in feat.geometry().asPolyline()]

            yield line, field_value

    @staticmethod
    def _get_params_directions(line, profile, preference):
        """
        Build parameters for optimization endpoint

        :param line: individual polyline points
        :type line: list of QgsPointXY

        :param profile: transport profile to be used
        :type profile: str

        :param preference: routing preference, shortest/fastest/recommended
        :type preference: str

        :returns: parameters for optimization endpoint
        :rtype: dict
        """

        params = {
            'coordinates': [[round(point.x(), 6), round(point.y(), 6)] for point in line],
            'preference': preference,
            'geometry': 'true',
            'format': 'geojson',
            'instructions': 'false',
            'elevation': True,
            'id': None
        }

        return params

    @staticmethod
    def _get_params_optimize(line, profile):
        """
        Build parameters for optimization endpoint

        :param line: individual polyline points
        :type line: list of QgsPointXY

        :param profile: transport profile to be used
        :type profile: str

        :returns: parameters for optimization endpoint
        :rtype: dict
        """

        start = line.pop(0)
        end = line.pop(-1)

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
        for point in line:
            params['jobs'].append({
                "location": [point.x(), point.y()],
                "id": line.index(point)
            })

        return params
