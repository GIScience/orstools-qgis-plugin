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

from typing import Dict, List


from qgis._core import (
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsProject,
    QgsProcessingParameterBoolean,
)
from qgis.core import (
    QgsWkbTypes,
    QgsCoordinateReferenceSystem,
    QgsProcessing,
    QgsProcessingParameterField,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterEnum,
    QgsPointXY,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingContext,
    QgsProcessingFeedback,
)

from ORStools.common import directions_core, PROFILES, PREFERENCES, OPTIMIZATION_MODES, EXTRA_INFOS
from ORStools.utils import transform, exceptions, logger
from .base_processing_algorithm import ORSBaseProcessingAlgorithm
from ..utils.processing import get_params_optimize


# noinspection PyPep8Naming
class ORSDirectionsPointsLayerAlgo(ORSBaseProcessingAlgorithm):
    """Algorithm class for Directions Lines."""

    def __init__(self):
        super().__init__()
        self.ALGO_NAME: str = "directions_from_points_1_layer"
        self.GROUP: str = "Directions"
        self.IN_POINTS: str = "INPUT_POINT_LAYER"
        self.IN_FIELD: str = "INPUT_LAYER_FIELD"
        self.IN_PREFERENCE: str = "INPUT_PREFERENCE"
        self.IN_OPTIMIZE: str = "INPUT_OPTIMIZE"
        self.IN_MODE: str = "INPUT_MODE"
        self.IN_SORTBY: str = "INPUT_SORTBY"
        self.EXTRA_INFO: str = "EXTRA_INFO"
        self.CSV_FACTOR: str = "CSV_FACTOR"
        self.CSV_COLUMN: str = "CSV_COLUMN"
        self.EXPORT_ORDER: str = "EXPORT_ORDER"
        self.PARAMETERS: List = [
            QgsProcessingParameterFeatureSource(
                name=self.IN_POINTS,
                description=self.tr("Input (Multi)Point layer"),
                types=[QgsProcessing.SourceType.TypeVectorPoint],
            ),
            QgsProcessingParameterField(
                name=self.IN_FIELD,
                description=self.tr("Layer ID Field (can be used for joining)"),
                parentLayerParameterName=self.IN_POINTS,
                defaultValue=None,
                optional=True,
            ),
            QgsProcessingParameterField(
                name=self.IN_SORTBY,
                description=self.tr("Sort Points by"),
                parentLayerParameterName=self.IN_POINTS,
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
                self.IN_OPTIMIZE,
                self.tr("Traveling Salesman (omits other configurations)"),
                OPTIMIZATION_MODES,
                defaultValue=None,
                optional=True,
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
            QgsProcessingParameterBoolean(self.EXPORT_ORDER, self.tr("Export order of jobs")),
        ]

    def processAlgorithm(
        self, parameters: dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, str]:
        ors_client = self._get_ors_client_from_provider(parameters[self.IN_PROVIDER], feedback)

        profile = dict(enumerate(PROFILES))[parameters[self.IN_PROFILE]]

        preference = dict(enumerate(PREFERENCES))[parameters[self.IN_PREFERENCE]]

        optimization_mode = parameters[self.IN_OPTIMIZE]

        options = self.parseOptions(parameters, context)

        csv_column = self.parameterAsString(parameters, self.CSV_COLUMN, context)

        csv_factor = self.parameterAsDouble(parameters, self.CSV_FACTOR, context)
        if csv_factor > 0:
            options["profile_params"] = {
                "weightings": {"csv_factor": round(csv_factor, 2), "csv_column": csv_column}
            }

        extra_info = self.parameterAsEnums(parameters, self.EXTRA_INFO, context)
        extra_info = [EXTRA_INFOS[i] for i in extra_info]

        # Get parameter values
        source = self.parameterAsSource(parameters, self.IN_POINTS, context)

        source_field_name = parameters[self.IN_FIELD]
        get_fields_options = dict()
        if source_field_name:
            get_fields_options.update(
                from_type=source.fields().field(source_field_name).type(),
                from_name=source_field_name,
            )

        sink_fields = directions_core.get_fields(
            **get_fields_options, line=True, extra_info=extra_info
        )

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUT,
            context,
            sink_fields,
            QgsWkbTypes.Type.LineString,
            QgsCoordinateReferenceSystem.fromEpsgId(4326),
        )

        sort_by = parameters[self.IN_SORTBY]

        if sort_by:

            def sort(f):
                return f.attribute(sort_by)
        else:

            def sort(f):
                return f.id()

        count = source.featureCount()

        input_points = list()
        from_values = list()
        x_former = transform.transformToWGS(source.sourceCrs())

        if QgsWkbTypes.flatType(source.wkbType()) == QgsWkbTypes.Type.Point:
            points = list()
            for feat in sorted(source.getFeatures(), key=sort):
                points.append(x_former.transform(QgsPointXY(feat.geometry().asPoint())))
            input_points.append(points)
            from_values.append(None)
        elif QgsWkbTypes.flatType(source.wkbType()) == QgsWkbTypes.Type.MultiPoint:
            # loop through multipoint features
            for feat in sorted(source.getFeatures(), key=sort):
                for point in feat.geometry().asMultiPoint():
                    input_points.append(x_former.transform(QgsPointXY(point)))
                from_values.append(feat[source_field_name] if source_field_name else None)
            input_points = [input_points]

        for num, (points, from_value) in enumerate(zip(input_points, from_values)):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            try:
                if optimization_mode is not None:
                    params = get_params_optimize(points, profile, optimization_mode)
                    response = ors_client.request("/optimization", {}, post_json=params)

                    sink.addFeature(
                        directions_core.get_output_features_optimization(
                            response, profile, from_value=from_value
                        )
                    )

                    # Export layer of points with optimization order
                    export_value = self.parameterAsBool(parameters, self.EXPORT_ORDER, context)
                    if export_value:
                        items = list()
                        for route in response["routes"]:
                            for i, step in enumerate(route["steps"]):
                                location = step["location"]
                                items.append(location)

                        point_layer = QgsVectorLayer(
                            "point?crs=epsg:4326&field=ID:integer", "Steps", "memory"
                        )

                        point_layer.updateFields()
                        for idx, coords in enumerate(items):
                            x, y = coords
                            feature = QgsFeature()
                            feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))
                            feature.setAttributes([idx])

                            point_layer.dataProvider().addFeature(feature)
                        QgsProject.instance().addMapLayer(point_layer)

                else:
                    params = directions_core.build_default_parameters(
                        preference, point_list=points, options=options, extra_info=extra_info
                    )
                    response = ors_client.request(
                        "/v2/directions/" + profile + "/geojson", {}, post_json=params
                    )

                    if extra_info:
                        feats = directions_core.get_extra_info_features_directions(
                            response, extra_info
                        )
                        for feat in feats:
                            sink.addFeature(feat)
                    else:
                        sink.addFeature(
                            directions_core.get_output_feature_directions(
                                response, profile, preference, from_value=from_value
                            )
                        )
            except (exceptions.ApiError, exceptions.InvalidKey, exceptions.GenericServerError) as e:
                msg = f"Feature ID {from_value} caused a {e.__class__.__name__}:\n{str(e)}"
                feedback.reportError(msg)
                logger.log(msg)
                continue

            feedback.setProgress(int(100.0 / count * num))

        return {self.OUT: dest_id}

    def displayName(self) -> str:
        """
        Algorithm name shown in QGIS toolbox
        :return:
        """
        return self.tr("Directions from 1 Point-Layer")
