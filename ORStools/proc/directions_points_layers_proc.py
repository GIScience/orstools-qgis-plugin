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
                       )
from . import HELP_DIR
from ORStools import RESOURCE_PREFIX, __help__
from ORStools.common import client, directions_core, PROFILES, PREFERENCES
from ORStools.utils import configmanager, transform, exceptions,logger


class ORSdirectionsPointsLayersAlgo(QgsProcessingAlgorithm):
    # TODO: create base algorithm class common to all modules

    ALGO_NAME = 'directions_from_points_2_layers'
    ALGO_NAME_LIST = ALGO_NAME.split('_')
    MODE_SELECTION = ['Row-by-Row', 'All-by-All']

    IN_PROVIDER = "INPUT_PROVIDER"
    IN_START = "INPUT_START_LAYER"
    IN_START_FIELD = "INPUT_START_FIELD"
    IN_END = "INPUT_END_LAYER"
    IN_END_FIELD = "INPUT_END_FIELD"
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
            QgsProcessingParameterEnum(
                self.IN_PREFERENCE,
                "Travel preference",
                PREFERENCES,
                defaultValue=PREFERENCES[0]
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.IN_MODE,
                "Layer mode",
                self.MODE_SELECTION,
                defaultValue=self.MODE_SELECTION[0]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                name=self.OUT,
                description="Directions",
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
            'algorithm_directions_point.help'
        )
        with open(file) as helpf:
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
        return ORSdirectionsPointsLayersAlgo()

    # TODO: preprocess parameters to options the range clenaup below:
    # https://www.qgis.org/pyqgis/master/core/Processing/QgsProcessingAlgorithm.html#qgis.core.QgsProcessingAlgorithm.preprocessParameters

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

        mode = self.MODE_SELECTION[self.parameterAsEnum(
            parameters,
            self.IN_MODE,
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

        params = {
            'preference': preference,
            'geometry': 'true',
            'instructions': 'false',
            'elevation': True,
            'id': None
        }

        route_dict = self._get_route_dict(
            source,
            source_field,
            destination,
            destination_field
        )

        if mode == 'Row-by-Row':
            route_count = min([source.featureCount(), destination.featureCount()])
        else:
            route_count = source.featureCount() * destination.featureCount()

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUT, context,
                                               directions_core.get_fields(source_field.type(), destination_field.type()),
                                               QgsWkbTypes.LineString,
                                               QgsCoordinateReferenceSystem(4326))

        counter = 0
        for coordinates, values in directions_core.get_request_point_features(route_dict, mode):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            params['coordinates'] = coordinates

            try:
                response = clnt.request('/v2/directions/' + profile + '/geojson', {}, post_json=params)
            except (exceptions.ApiError,
                    exceptions.InvalidKey,
                    exceptions.GenericServerError) as e:
                msg = "Route from {} to {} caused a {}:\n{}".format(
                    values[0],
                    values[1],
                    e.__class__.__name__,
                    str(e))
                feedback.reportError(msg)
                logger.log(msg)
                continue

            sink.addFeature(directions_core.get_output_feature_directions(
                response,
                profile,
                preference,
                from_value=values[0],
                to_value=values[1]
            ))

            counter += 1
            feedback.setProgress(int(100.0 / route_count * counter))

        return {self.OUT: dest_id}

    def _get_route_dict(self, source, source_field, destination, destination_field):
        """
        Compute route_dict from input layer.

        :param source: Input from layer
        :type source: QgsProcessingParameterFeatureSource

        :param source_field: ID field from layer.
        :type source_field: QgsField

        :param destination: Input to layer.
        :type destination: QgsProcessingParameterFeatureSource

        :param destination_field: ID field to layer.
        :type destination_field: QgsField

        :returns: route_dict with coordinates and ID values
        :rtype: dict
        """
        route_dict = dict()

        source_feats = list(source.getFeatures())
        xformer_source = transform.transformToWGS(source.sourceCrs())
        route_dict['start'] = dict(
            geometries=[xformer_source.transform(feat.geometry().asPoint()) for feat in source_feats],
            values= [feat.attribute(source_field.name()) for feat in source_feats],
        )

        destination_feats = list(destination.getFeatures())
        xformer_destination = transform.transformToWGS(destination.sourceCrs())
        route_dict['end'] = dict(
            geometries=[xformer_destination.transform(feat.geometry().asPoint()) for feat in destination_feats],
            values= [feat.attribute(destination_field.name()) for feat in destination_feats],
        )

        return route_dict
