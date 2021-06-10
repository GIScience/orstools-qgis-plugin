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
                       QgsProcessing,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterEnum,
                       )

from ORStools.common import directions_core, PROFILES, PREFERENCES
from ORStools.utils import transform, exceptions, logger
from .base_processing_algorithm import ORSBaseProcessingAlgorithm


# noinspection PyPep8Naming
class ORSDirectionsPointsLayersAlgo(ORSBaseProcessingAlgorithm):

    def __init__(self):
        super().__init__()
        self.ALGO_NAME = 'directions_from_points_2_layers'
        self.GROUP = "Directions"
        self.MODE_SELECTION: list = ['Row-by-Row', 'All-by-All']
        self.IN_START = "INPUT_START_LAYER"
        self.IN_START_FIELD = "INPUT_START_FIELD"
        self.IN_END = "INPUT_END_LAYER"
        self.IN_END_FIELD = "INPUT_END_FIELD"
        self.IN_PROFILE = "INPUT_PROFILE"
        self.IN_PREFERENCE = "INPUT_PREFERENCE"
        self.IN_MODE = "INPUT_MODE"
        self.PARAMETERS = [
            QgsProcessingParameterFeatureSource(
                name=self.IN_START,
                description="Input Start Point layer",
                types=[QgsProcessing.TypeVectorPoint],
            ),
            QgsProcessingParameterField(
                name=self.IN_START_FIELD,
                description="Start ID Field (can be used for joining)",
                parentLayerParameterName=self.IN_START,
                defaultValue=None,
                optional=True,
            ),
            QgsProcessingParameterFeatureSource(
                name=self.IN_END,
                description="Input End Point layer",
                types=[QgsProcessing.TypeVectorPoint],
            ),
            QgsProcessingParameterField(
                name=self.IN_END_FIELD,
                description="End ID Field (can be used for joining)",
                parentLayerParameterName=self.IN_END,
                defaultValue=None,
                optional=True,
            ),
            QgsProcessingParameterEnum(
                self.IN_PROFILE,
                "Travel mode",
                PROFILES,
                defaultValue=PROFILES[0]
            ),
            QgsProcessingParameterEnum(
                self.IN_PREFERENCE,
                "Travel preference",
                PREFERENCES,
                defaultValue=PREFERENCES[0]
            ),
            QgsProcessingParameterEnum(
                self.IN_MODE,
                "Layer mode",
                self.MODE_SELECTION,
                defaultValue=self.MODE_SELECTION[0]
            )
        ]

    # TODO: preprocess parameters to options the range cleanup below:
    # https://www.qgis.org/pyqgis/master/core/Processing/QgsProcessingAlgorithm.html#qgis.core.QgsProcessingAlgorithm.preprocessParameters
    def processAlgorithm(self, parameters, context, feedback):
        ors_client = self._get_ors_client_from_provider(parameters[self.IN_PROVIDER], feedback)

        profile = dict(enumerate(PROFILES))[parameters[self.IN_PROFILE]]

        preference = dict(enumerate(PREFERENCES))[parameters[self.IN_PREFERENCE]]

        mode = dict(enumerate(self.MODE_SELECTION))[parameters[self.IN_MODE]]

        # Get parameter values
        source = self.parameterAsSource(
            parameters,
            self.IN_START,
            context
        )

        if source_field_name := parameters[self.IN_START_FIELD]:
            source_field = source.fields().field(source_field_name)
        else:
            source_field = None


        destination = self.parameterAsSource(
            parameters,
            self.IN_END,
            context
        )

        if destination_field_name := parameters[self.IN_START_FIELD]:
            destination_field = destination.fields().field(destination_field_name)
        else:
            destination_field = None

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

        if source_field_name and destination_field_name:
           sink_fields = directions_core.get_fields(source_field.type(), destination_field.type())
        else:
            sink_fields = directions_core.get_fields()

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUT, context, sink_fields,
                                               QgsWkbTypes.LineString,
                                               QgsCoordinateReferenceSystem.fromEpsgId(4326))

        counter = 0
        for coordinates, values in directions_core.get_request_point_features(route_dict, mode):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            params = directions_core.build_default_parameters(preference, coordinates=coordinates)

            try:
                response = ors_client.request('/v2/directions/' + profile + '/geojson', {}, post_json=params)
            except (exceptions.ApiError,
                    exceptions.InvalidKey,
                    exceptions.GenericServerError) as e:
                msg = f"Route from {values[0]} to {values[1]} caused a {e.__class__.__name__}:\n{str(e)}"
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

    @staticmethod
    def _get_route_dict(source, source_field, destination, destination_field):
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
        x_former_source = transform.transformToWGS(source.sourceCrs())
        route_dict['start'] = dict(
            geometries=[x_former_source.transform(feat.geometry().asPoint()) for feat in source_feats],
            values=[feat.attribute(source_field.name()) if source_field else feat.id() for feat in source_feats],
        )

        destination_feats = list(destination.getFeatures())
        x_former_destination = transform.transformToWGS(destination.sourceCrs())
        route_dict['end'] = dict(
            geometries=[x_former_destination.transform(feat.geometry().asPoint()) for feat in destination_feats],
            values=[feat.attribute(destination_field.name()) if destination_field else feat.id() for feat in destination_feats] ,
        )

        return route_dict
