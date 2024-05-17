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

from qgis._core import QgsField
from qgis.core import (
    QgsWkbTypes,
    QgsCoordinateReferenceSystem,
    QgsProcessing,
    QgsProcessingParameterField,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterEnum,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingFeatureSource,
    QgsProcessingContext,
    QgsProcessingFeedback,
)

from ORStools.common import directions_core, PROFILES, PREFERENCES, EXTRA_INFOS
from ORStools.utils import transform, exceptions, logger
from .base_processing_algorithm import ORSBaseProcessingAlgorithm


# noinspection PyPep8Naming
class ORSDirectionsPointsLayersAlgo(ORSBaseProcessingAlgorithm):
    def __init__(self):
        super().__init__()
        self.ALGO_NAME: str = "directions_from_points_2_layers"
        self.GROUP: str = "Directions"
        self.MODE_SELECTION: list = ["Row-by-Row", "All-by-All"]
        self.IN_START: str = "INPUT_START_LAYER"
        self.IN_START_FIELD: str = "INPUT_START_FIELD"
        self.IN_SORT_START_BY: str = "INPUT_SORT_START_BY"
        self.IN_END: str = "INPUT_END_LAYER"
        self.IN_END_FIELD: str = "INPUT_END_FIELD"
        self.IN_SORT_END_BY: str = "INPUT_SORT_END_BY"
        self.IN_PREFERENCE: str = "INPUT_PREFERENCE"
        self.IN_MODE: str = "INPUT_MODE"
        self.EXTRA_INFO: str = "EXTRA_INFO"
        self.CSV_FACTOR: str = "CSV_FACTOR"
        self.CSV_COLUMN: str = "CSV_COLUMN"
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
            QgsProcessingParameterField(
                name=self.IN_SORT_START_BY,
                description=self.tr("Sort Start Points by"),
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
            QgsProcessingParameterField(
                name=self.IN_SORT_END_BY,
                description=self.tr("Sort End Points by"),
                parentLayerParameterName=self.IN_END,
                defaultValue=None,
                optional=True,
            ),
            QgsProcessingParameterEnum(
                self.IN_PREFERENCE,
                self.tr("Travel preference"),
                PREFERENCES,
                defaultValue=PREFERENCES[0],
            ),
            QgsProcessingParameterEnum(
                self.IN_MODE,
                self.tr("Layer mode"),
                self.MODE_SELECTION,
                defaultValue=self.MODE_SELECTION[0],
            ),
            QgsProcessingParameterEnum(
                self.EXTRA_INFO,
                self.tr("Extra Info"),
                options=EXTRA_INFOS,
                allowMultiple=True,
                optional=True,
            ),
            QgsProcessingParameterNumber(
                self.CSV_FACTOR,
                self.tr("Csv Factor (needs Csv Column and csv in Extra Info)"),
                type=QgsProcessingParameterNumber.Double,
                minValue=0,
                maxValue=1,
                defaultValue=None,
                optional=True,
            ),
            QgsProcessingParameterString(
                self.CSV_COLUMN,
                self.tr("Csv Column (needs Csv Factor and csv in Extra Info)"),
                optional=True,
            ),
        ]

    # TODO: preprocess parameters to options the range cleanup below:
    # https://www.qgis.org/pyqgis/master/core/Processing/QgsProcessingAlgorithm.html#qgis.core.QgsProcessingAlgorithm.preprocessParameters
    def processAlgorithm(
        self, parameters: dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, str]:
        ors_client = self._get_ors_client_from_provider(parameters[self.IN_PROVIDER], feedback)

        profile = dict(enumerate(PROFILES))[parameters[self.IN_PROFILE]]

        preference = dict(enumerate(PREFERENCES))[parameters[self.IN_PREFERENCE]]

        mode = dict(enumerate(self.MODE_SELECTION))[parameters[self.IN_MODE]]

        options = self.parseOptions(parameters, context)

        csv_factor = self.parameterAsDouble(parameters, self.CSV_FACTOR, context)
        if csv_factor > 0:
            options["profile_params"] = {"weightings": {"csv_factor": csv_factor}}

        extra_info = self.parameterAsEnums(parameters, self.EXTRA_INFO, context)
        extra_info = [EXTRA_INFOS[i] for i in extra_info]

        # Get parameter values
        source = self.parameterAsSource(parameters, self.IN_START, context)

        source_field_name = parameters[self.IN_START_FIELD]
        source_field = source.fields().field(source_field_name) if source_field_name else None
        sort_start_by = parameters[self.IN_SORT_START_BY]
        if sort_start_by:

            def sort_start(f):
                return f.attribute(sort_start_by)
        else:

            def sort_start(f):
                return f.id()

        destination = self.parameterAsSource(parameters, self.IN_END, context)

        destination_field_name = parameters[self.IN_END_FIELD]
        destination_field = (
            destination.fields().field(destination_field_name) if destination_field_name else None
        )
        sort_end_by = parameters[self.IN_SORT_END_BY]
        if sort_end_by:

            def sort_end(f):
                return f.attribute(sort_end_by)
        else:

            def sort_end(f):
                return f.id()

        route_dict = self._get_route_dict(
            source, source_field, sort_start, destination, destination_field, sort_end
        )

        if mode == "Row-by-Row":
            route_count = min([source.featureCount(), destination.featureCount()])
        else:
            route_count = source.featureCount() * destination.featureCount()

        # get types of set ID fields
        field_types = dict()
        if source_field:
            field_types.update({"from_type": source_field.type()})
        if destination_field:
            field_types.update({"to_type": destination_field.type()})
        sink_fields = directions_core.get_fields(**field_types, extra_info=extra_info)

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUT,
            context,
            sink_fields,
            QgsWkbTypes.Type.LineString,
            QgsCoordinateReferenceSystem.fromEpsgId(4326),
        )

        counter = 0
        for coordinates, values in directions_core.get_request_point_features(route_dict, mode):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            params = directions_core.build_default_parameters(
                preference, coordinates=coordinates, options=options, extra_info=extra_info
            )

            try:
                response = ors_client.request(
                    "/v2/directions/" + profile + "/geojson", {}, post_json=params
                )
            except (exceptions.ApiError, exceptions.InvalidKey, exceptions.GenericServerError) as e:
                msg = f"Route from {values[0]} to {values[1]} caused a {e.__class__.__name__}:\n{str(e)}"
                feedback.reportError(msg)
                logger.log(msg)
                continue

            if extra_info:
                feats = directions_core.get_extra_info_features_directions(response)
                for feat in feats:
                    sink.addFeature(feat)
            else:
                sink.addFeature(
                    directions_core.get_output_feature_directions(
                        response, profile, preference, from_value=values[0], to_value=values[1]
                    )
                )

            counter += 1
            feedback.setProgress(int(100.0 / route_count * counter))

        return {self.OUT: dest_id}

    @staticmethod
    def _get_route_dict(
        source: QgsProcessingFeatureSource,
        source_field: QgsField,
        sort_start,
        destination: QgsProcessingFeatureSource,
        destination_field: QgsField,
        sort_end,
    ) -> dict:
        """
        Compute route_dict from input layer.

        :param source: Input from layer
        :type source: QgsProcessingFeatureSource

        :param source_field: ID field from layer.
        :type source_field: QgsField

        :param destination: Input to layer.
        :type destination: QgsProcessingFeatureSource

        :param destination_field: ID field to layer.
        :type destination_field: QgsField

        :returns: route_dict with coordinates and ID values
        :rtype: dict
        """
        route_dict = dict()
        source_feats = sorted(list(source.getFeatures()), key=sort_start)
        x_former_source = transform.transformToWGS(source.sourceCrs())
        route_dict["start"] = dict(
            geometries=[
                x_former_source.transform(feat.geometry().asPoint()) for feat in source_feats
            ],
            values=[
                feat.attribute(source_field.name()) if source_field else feat.id()
                for feat in source_feats
            ],
        )

        destination_feats = sorted(list(destination.getFeatures()), key=sort_end)
        x_former_destination = transform.transformToWGS(destination.sourceCrs())
        route_dict["end"] = dict(
            geometries=[
                x_former_destination.transform(feat.geometry().asPoint())
                for feat in destination_feats
            ],
            values=[
                feat.attribute(destination_field.name()) if destination_field else feat.id()
                for feat in destination_feats
            ],
        )

        return route_dict

    def displayName(self) -> str:
        """
        Algorithm name shown in QGIS toolbox
        :return:
        """
        return self.tr("Directions from 2 Point-Layers")
