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
    QgsFeature,
    QgsProcessing,
    QgsFields,
    QgsField,
    QgsProcessingException,
    QgsProcessingParameterField,
    QgsProcessingParameterFeatureSource,
    QgsProcessingContext,
    QgsProcessingFeedback,
)

from qgis.PyQt.QtCore import QVariant

from ORStools.common import PROFILES
from ORStools.utils import transform, exceptions, logger
from .base_processing_algorithm import ORSBaseProcessingAlgorithm


# noinspection PyPep8Naming
class ORSMatrixAlgo(ORSBaseProcessingAlgorithm):
    def __init__(self):
        super().__init__()
        self.ALGO_NAME: str = "matrix_from_layers"
        self.GROUP: str = "Matrix"
        self.IN_START: str = "INPUT_START_LAYER"
        self.IN_START_FIELD: str = "INPUT_START_FIELD"
        self.IN_END: str = "INPUT_END_LAYER"
        self.IN_END_FIELD: str = "INPUT_END_FIELD"
        self.PARAMETERS: list = [
            QgsProcessingParameterFeatureSource(
                name=self.IN_START,
                description=self.tr("Input Start Point layer"),
                types=[QgsProcessing.SourceType.TypeVectorPoint],
            ),
            QgsProcessingParameterField(
                name=self.IN_START_FIELD,
                description=self.tr("Start ID Field (can be used for joining)"),
                parentLayerParameterName=self.IN_START,
                defaultValue=None,
                optional=True,
            ),
            QgsProcessingParameterFeatureSource(
                name=self.IN_END,
                description=self.tr("Input End Point layer"),
                types=[QgsProcessing.SourceType.TypeVectorPoint],
            ),
            QgsProcessingParameterField(
                name=self.IN_END_FIELD,
                description=self.tr("End ID Field (can be used for joining)"),
                parentLayerParameterName=self.IN_END,
                defaultValue=None,
                optional=True,
            ),
        ]

    def processAlgorithm(
        self, parameters: dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, str]:
        ors_client = self._get_ors_client_from_provider(parameters[self.IN_PROVIDER], feedback)

        # Get profile value
        profile = dict(enumerate(PROFILES))[parameters[self.IN_PROFILE]]

        # TODO: enable once core matrix is available
        # options = self.parseOptions(parameters, context)

        # Get parameter values
        source = self.parameterAsSource(parameters, self.IN_START, context)

        source_field_name = parameters[self.IN_START_FIELD]
        source_field = source.fields().field(source_field_name) if source_field_name else None

        destination = self.parameterAsSource(parameters, self.IN_END, context)
        destination_field_name = parameters[self.IN_END_FIELD]
        destination_field = (
            destination.fields().field(destination_field_name) if destination_field_name else None
        )

        # Abort when MultiPoint type
        if (
            QgsWkbTypes.flatType(source.wkbType()) or QgsWkbTypes.flatType(destination.wkbType())
        ) == QgsWkbTypes.Type.MultiPoint:
            raise QgsProcessingException(
                "TypeError: Multipoint Layers are not accepted. Please convert to single geometry layer."
            )

        # Get source and destination features
        sources_features = list(source.getFeatures())
        destination_features = list(destination.getFeatures())
        # Get feature amounts/counts
        sources_amount = source.featureCount()
        destinations_amount = destination.featureCount()

        # Allow for 50 features in source if source == destination
        source_equals_destination = parameters["INPUT_START_LAYER"] == parameters["INPUT_END_LAYER"]
        if source_equals_destination:
            features = sources_features
            x_former = transform.transformToWGS(source.sourceCrs())
            features_points = [x_former.transform(feat.geometry().asPoint()) for feat in features]
        else:
            x_former = transform.transformToWGS(source.sourceCrs())
            sources_features_x_formed = [
                x_former.transform(feat.geometry().asPoint()) for feat in sources_features
            ]

            x_former = transform.transformToWGS(destination.sourceCrs())
            destination_features_x_formed = [
                x_former.transform(feat.geometry().asPoint()) for feat in destination_features
            ]

            features_points = sources_features_x_formed + destination_features_x_formed

        # Get IDs
        sources_ids = (
            list(range(sources_amount))
            if source_equals_destination
            else list(range(sources_amount))
        )
        destination_ids = (
            list(range(sources_amount))
            if source_equals_destination
            else list(range(sources_amount, sources_amount + destinations_amount))
        )

        params = {
            "locations": [[point.x(), point.y()] for point in features_points],
            "sources": sources_ids,
            "destinations": destination_ids,
            "metrics": ["duration", "distance"],
            "id": "Matrix",
            # 'options': options
        }

        # get types of set ID fields
        field_types = dict()
        if source_field:
            field_types.update({"source_type": source_field.type()})
        if destination_field:
            field_types.update({"destination_type": destination_field.type()})

        sink_fields = self.get_fields(**field_types)

        # Make request and catch ApiError
        try:
            response = ors_client.request("/v2/matrix/" + profile, {}, post_json=params)

        except (exceptions.ApiError, exceptions.InvalidKey, exceptions.GenericServerError) as e:
            msg = f"{e.__class__.__name__}: {str(e)}"
            feedback.reportError(msg)
            logger.log(msg)

        (sink, dest_id) = self.parameterAsSink(
            parameters, self.OUT, context, sink_fields, QgsWkbTypes.Type.NoGeometry
        )

        sources_attributes = [
            feat.attribute(source_field_name) if source_field_name else feat.id()
            for feat in sources_features
        ]
        destinations_attributes = [
            feat.attribute(destination_field_name) if destination_field_name else feat.id()
            for feat in destination_features
        ]

        for s, source in enumerate(sources_attributes):
            for d, destination in enumerate(destinations_attributes):
                duration = response["durations"][s][d]
                distance = response["distances"][s][d]
                feat = QgsFeature()
                feat.setAttributes(
                    [
                        source,
                        destination,
                        duration / 3600 if duration is not None else None,
                        distance / 1000 if distance is not None else None,
                    ]
                )

                sink.addFeature(feat)

        return {self.OUT: dest_id}

    # TODO working source_type and destination_type differ in both name and type from get_fields in directions_core.
    #  Change to be consistent
    @staticmethod
    def get_fields(source_type=QVariant.Int, destination_type=QVariant.Int):
        fields = QgsFields()
        fields.append(QgsField("FROM_ID", source_type))
        fields.append(QgsField("TO_ID", destination_type))
        fields.append(QgsField("DURATION_H", QVariant.Double))
        fields.append(QgsField("DIST_KM", QVariant.Double))

        return fields

    def displayName(self) -> str:
        """
        Algorithm name shown in QGIS toolbox
        :return:
        """
        return self.tr("Matrix from Layers")
