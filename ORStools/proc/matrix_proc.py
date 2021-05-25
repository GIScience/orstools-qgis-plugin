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
from PyQt5.QtCore import QVariant

from qgis.core import (QgsWkbTypes,
                       QgsFeature,
                       QgsProcessing,
                       QgsFields,
                       QgsField,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSink,
                       )
from . import HELP_DIR
from ORStools import RESOURCE_PREFIX, __help__
from ORStools.common import client, PROFILES
from ORStools.utils import transform, exceptions, logger, configmanager


class ORSmatrixAlgo(QgsProcessingAlgorithm):
    # TODO: create base algorithm class common to all modules

    ALGO_NAME = 'matrix_from_layers'
    ALGO_NAME_LIST = ALGO_NAME.split('_')

    IN_PROVIDER = "INPUT_PROVIDER"
    IN_START = "INPUT_START_LAYER"
    IN_START_FIELD = "INPUT_START_FIELD"
    IN_END = "INPUT_END_LAYER"
    IN_END_FIELD = "INPUT_END_FIELD"
    IN_PROFILE = "INPUT_PROFILE"
    OUT = 'OUTPUT'

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
            QgsProcessingParameterFeatureSource(
                name=self.IN_START,
                description="Input Start Point layer",
                types=[QgsProcessing.TypeVectorPoint],
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                name=self.IN_START_FIELD,
                description="Start ID Field (can be used for joining)",
                parentLayerParameterName=self.IN_START,
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                name=self.IN_END,
                description="Input End Point layer",
                types=[QgsProcessing.TypeVectorPoint],
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                name=self.IN_END_FIELD,
                description="End ID Field (can be used for joining)",
                parentLayerParameterName=self.IN_END,
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
            QgsProcessingParameterFeatureSink(
                name=self.OUT,
                description="Matrix",
            )
        )

    def group(self):
        return "Matrix"

    def groupId(self):
        return 'matrix'

    def name(self):
        return self.ALGO_NAME

    def shortHelpString(self):
        """Displays the sidebar help in the algorithm window"""

        file = os.path.join(
            HELP_DIR,
            'algorithm_matrix.help'
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
        return QIcon(RESOURCE_PREFIX + 'icon_matrix.png')

    def createInstance(self):
        return ORSmatrixAlgo()

    def processAlgorithm(self, parameters, context, feedback):

        # Init ORS client
        providers = configmanager.read_config()['providers']
        provider = providers[self.parameterAsEnum(parameters, self.IN_PROVIDER, context)]
        clnt = client.Client(provider)
        clnt.overQueryLimit.connect(lambda: feedback.reportError("OverQueryLimit: Retrying"))

        params = dict()

        # Get profile value
        profile = PROFILES[self.parameterAsEnum(
            parameters,
            self.IN_PROFILE,
            context
        )]

        # Get parameter values
        source = self.parameterAsSource(
            parameters,
            self.IN_START,
            context
        )
        source_field_name = self.parameterAsString(
            parameters,
            self.IN_START_FIELD,
            context
        )
        destination = self.parameterAsSource(
            parameters,
            self.IN_END,
            context
        )
        destination_field_name = self.parameterAsString(
            parameters,
            self.IN_END_FIELD,
            context
        )

        # Get fields from field name
        source_field_id = source.fields().lookupField(source_field_name)
        source_field = source.fields().field(source_field_id)

        destination_field_id = destination.fields().lookupField(destination_field_name)
        destination_field = destination.fields().field(destination_field_id)

        # Abort when MultiPoint type
        if (source.wkbType() or destination.wkbType()) == 4:
            raise QgsProcessingException("TypeError: Multipoint Layers are not accepted. Please convert to single geometry layer.")

        # Get source and destination features
        sources_features = list(source.getFeatures())
        destination_features = list(destination.getFeatures())
        # Get feature amounts/counts
        sources_amount = source.featureCount()
        destinations_amount = destination.featureCount()

        # Allow for 50 features in source if source == destination
        source_equals_destination = parameters['INPUT_START_LAYER'] == parameters['INPUT_END_LAYER']
        if source_equals_destination:
            features = sources_features
            xformer = transform.transformToWGS(source.sourceCrs())
            features_points = [xformer.transform(feat.geometry().asPoint()) for feat in features]
        else:
            xformer = transform.transformToWGS(source.sourceCrs())
            sources_features_xformed = [xformer.transform(feat.geometry().asPoint()) for feat in sources_features]

            xformer = transform.transformToWGS(destination.sourceCrs())
            destination_features_xformed = [xformer.transform(feat.geometry().asPoint()) for feat in destination_features]

            features_points = sources_features_xformed + destination_features_xformed

        # Get IDs
        sources_ids = list(range(sources_amount)) if source_equals_destination else list(range(sources_amount))
        destination_ids = list(range(sources_amount)) if source_equals_destination else list(range(sources_amount, sources_amount + destinations_amount))

        # Populate parameters further
        params.update({
            'locations': [[point.x(), point.y()] for point in features_points],
            'sources': sources_ids,
            'destinations': destination_ids,
            'metrics': ["duration", "distance"],
            'id': 'Matrix'
        })

        # Make request and catch ApiError
        try:
            response = clnt.request('/v2/matrix/' + profile, {}, post_json=params)

        except (exceptions.ApiError,
                exceptions.InvalidKey,
                exceptions.GenericServerError) as e:
            msg = f"{e.__class__.__name__}: {str(e)}"
            feedback.reportError(msg)
            logger.log(msg)

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUT,
            context,
            self.get_fields(
                source_field.type(),
                destination_field.type()
            ),
            QgsWkbTypes.NoGeometry
        )

        sources_attributes = [feat.attribute(source_field_name) for feat in sources_features]
        destinations_attributes = [feat.attribute(destination_field_name) for feat in destination_features]

        for s, source in enumerate(sources_attributes):
            for d, destination in enumerate(destinations_attributes):
                duration = response['durations'][s][d]
                distance = response['distances'][s][d]
                feat = QgsFeature()
                feat.setAttributes([
                    source,
                    destination,
                    duration / 3600 if duration is not None else None,
                    distance / 1000 if distance is not None else None
                ])

                sink.addFeature(feat)

        return {self.OUT: dest_id}

    @staticmethod
    def get_fields(source_type, destination_type):

        fields = QgsFields()
        fields.append(QgsField("FROM_ID", source_type))
        fields.append(QgsField("TO_ID", destination_type))
        fields.append(QgsField("DURATION_H", QVariant.Double))
        fields.append(QgsField("DIST_KM", QVariant.Double))

        return fields

    @staticmethod
    def chunks(l, n):
        """Yield successive n-sized chunks from l."""
        for i in range(0, len(l), n):
            yield l[i:i + n]
