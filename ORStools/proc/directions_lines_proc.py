# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ORStools
                                 A QGIS plugin
 QGIS client to query openrouteservice
                              -------------------
        begin                : 2017-02-01
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Nils Nolde
        email                : nils.nolde@gmail.com
 ***************************************************************************/

 This plugin provides access to the various APIs from OpenRouteService
 (https://openrouteservice.org), developed and
 maintained by GIScience team at University of Heidelberg, Germany. By using
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
                       QgsPointXY,
                       )
from . import HELP_DIR
from ORStools import RESOURCE_PREFIX, __help__
from ORStools.core import client, directions_core, PROFILES, PREFERENCES
from ORStools.utils import configmanager, transform, exceptions,logger, convert


class ORSdirectionsLinesAlgo(QgsProcessingAlgorithm):
    """Algorithm class for Directions Lines."""

    ALGO_NAME = 'directions_lines'
    ALGO_NAME_LIST = ALGO_NAME.split('_')

    IN_PROVIDER = "INPUT_PROVIDER"
    IN_LINES = "INPUT_LINE_LAYER"
    IN_FIELD = "INPUT_LAYER_FIELD"
    IN_PROFILE = "INPUT_PROFILE"
    IN_PREFERENCE = "INPUT_PREFERENCE"
    IN_MODE = "INPUT_MODE"
    OUT = 'OUTPUT'

    providers = configmanager.read_config()['providers']

    def initAlgorithm(self, configuration, p_str=None, Any=None, *args, **kwargs):

        providers = [provider['name'] for provider in self.providers]
        self.addParameter(
            QgsProcessingParameterEnum(
                self.IN_PROVIDER,
                "Provider",
                providers
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
                PROFILES
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.IN_PREFERENCE,
                "Travel preference",
                PREFERENCES
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                name=self.OUT,
                description="Directions",
            )
        )

    def name(self):
        return self.ALGO_NAME

    def shortHelpString(self):
        """Displays the sidebar help in the algorithm window"""

        file = os.path.join(
            HELP_DIR,
            'algorithm_directions_line.help'
        )
        with open(file) as helpf:
            msg = helpf.read()

        return msg

    def helpUrl(self):
        """will be connected to the Help button in the Algorithm window"""
        return __help__

    def displayName(self):
        return 'Generate ' + " ".join(map(lambda x: x.capitalize(), self.ALGO_NAME_LIST))

    def icon(self):
        return QIcon(RESOURCE_PREFIX + 'icon_directions.png')

    def createInstance(self):
        return ORSdirectionsLinesAlgo()

    def processAlgorithm(self, parameters, context, feedback):
        # Init ORS client

        providers = configmanager.read_config()['providers']
        provider = providers[self.parameterAsEnum(parameters, self.IN_PROVIDER, context)]
        clnt = client.Client(provider)
        clnt.overQueryLimit.connect(lambda sleep_for: feedback.reportError("OverQueryLimit: Wait for {} seconds".format(sleep_for)))

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

        params = {
            'profile': profile,
            'preference': preference,
            'geometry': 'true',
            'format': 'geojson',
            'geometry_format': 'geojson',
            'instructions': 'false',
            'id': None
        }

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUT, context,
                                               directions_core.get_fields(from_type=source.fields().field(source_field_name).type(),
                                                                          from_name=source_field_name,
                                                                          line=True),
                                               source.wkbType(),
                                               QgsCoordinateReferenceSystem(4326))
        count = source.featureCount()

        for num, (line, field_value) in enumerate(self.get_sorted_lines(source, source_field_name)):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            params['coordinates'] = convert.build_coords([[point.x(), point.y()] for point in line])

            try:
                response = clnt.request(provider['endpoints'][self.ALGO_NAME_LIST[0]], params)
            except (exceptions.ApiError,
                    exceptions.InvalidKey,
                    exceptions.GenericServerError) as e:
                msg = "Feature ID {} caused a {}:\n{}".format(
                    line[source_field_name],
                    e.__class__.__name__,
                    str(e))
                feedback.reportError(msg)
                logger.log(msg)
                continue

            sink.addFeature(directions_core.get_output_feature(
                response,
                profile,
                preference,
                from_value=field_value,
                line=True
            ))

            feedback.setProgress(int(100.0 / count * num))

        return {self.OUT: dest_id}

    def get_sorted_lines(self, layer, field_name):
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
                line = [xformer.transform(QgsPointXY(point)) for point in feat.geometry().asMultiPolyline()[0]]

            elif layer.wkbType() == QgsWkbTypes.LineString:
                line = [xformer.transform(QgsPointXY(point)) for point in feat.geometry().asPolyline()]

            yield line, field_value
