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
                       QgsPointXY,
                       )

from ORStools.common import directions_core, PROFILES, PREFERENCES, OPTIMIZATION_MODES
from ORStools.utils import transform, exceptions, logger
from .base_processing_algorithm import ORSBaseProcessingAlgorithm
from ..utils.processing import get_params_optimize


# noinspection PyPep8Naming
class ORSDirectionsPointsLayerAlgo(ORSBaseProcessingAlgorithm):
    """Algorithm class for Directions Lines."""

    def __init__(self):
        super().__init__()
        self.ALGO_NAME = 'directions_from_points_1_layer'
        self.GROUP = "Directions"
        self.IN_POINTS = "INPUT_POINT_LAYER"
        self.IN_FIELD = "INPUT_LAYER_FIELD"
        self.IN_PREFERENCE = "INPUT_PREFERENCE"
        self.IN_OPTIMIZE = "INPUT_OPTIMIZE"
        self.IN_MODE = "INPUT_MODE"
        self.IN_SORTBY = "INPUT_SORTBY"
        self.PARAMETERS = [
            QgsProcessingParameterFeatureSource(
                name=self.IN_POINTS,
                description=self.tr("Input (Multi)Point layer"),
                types=[QgsProcessing.TypeVectorPoint],
            ),
            QgsProcessingParameterField(
                name=self.IN_FIELD,
                description=self.tr("Layer ID Field"),
                parentLayerParameterName=self.IN_POINTS,
                defaultValue=None,
                optional=True
            ),
            QgsProcessingParameterField(
                name=self.IN_SORTBY,
                description=self.tr("Sort Points by"),
                parentLayerParameterName=self.IN_POINTS,
                defaultValue=None,
                optional=True
            ),
            QgsProcessingParameterEnum(
                self.IN_PREFERENCE,
                self.tr("Travel preference"),
                PREFERENCES,
                defaultValue=PREFERENCES[0]
            ),
            QgsProcessingParameterEnum(
                self.IN_OPTIMIZE,
                self.tr("Traveling Salesman"),
                OPTIMIZATION_MODES,
                defaultValue=None,
                optional=True,
            )
        ]

    def processAlgorithm(self, parameters, context, feedback):
        ors_client = self._get_ors_client_from_provider(parameters[self.IN_PROVIDER], feedback)

        profile = dict(enumerate(PROFILES))[parameters[self.IN_PROFILE]]

        preference = dict(enumerate(PREFERENCES))[parameters[self.IN_PREFERENCE]]

        optimization_mode = parameters[self.IN_OPTIMIZE]

        options = self.parseOptions(parameters, context)

        # Get parameter values
        source = self.parameterAsSource(
            parameters,
            self.IN_POINTS,
            context
        )

        source_field_name = parameters[self.IN_FIELD]
        get_fields_options = dict()
        if source_field_name:
            get_fields_options.update(
                from_type=source.fields().field(source_field_name).type(),
                from_name=source_field_name
            )

        sink_fields = directions_core.get_fields(**get_fields_options, line=True)

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUT, context,
                                               sink_fields,
                                               QgsWkbTypes.LineString,
                                               QgsCoordinateReferenceSystem.fromEpsgId(4326))

        sort_by = parameters[self.IN_SORTBY]

        if sort_by:
            def sort(f): return f.attribute(sort_by)
        else:
            def sort(f): return f.id()

        count = source.featureCount()

        input_points = list()
        from_values = list()
        x_former = transform.transformToWGS(source.sourceCrs())

        if QgsWkbTypes.flatType(source.wkbType()) == QgsWkbTypes.Point:
            points = list()
            for feat in sorted(source.getFeatures(), key=sort):
                points.append(x_former.transform(QgsPointXY(feat.geometry().asPoint())))
            input_points.append(points)
            from_values.append(None)
        elif QgsWkbTypes.flatType(source.wkbType()) == QgsWkbTypes.MultiPoint:
            # loop through multipoint features
            for feat in sorted(source.getFeatures(), key=sort):
                points = list()
                for point in feat.geometry().asMultiPoint():
                    points.append(x_former.transform(QgsPointXY(point)))
                input_points.append(points)
                from_values.append(feat[source_field_name] if source_field_name else None)

        for num, (points, from_value) in enumerate(zip(input_points, from_values)):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            try:
                if optimization_mode is not None:
                    params = get_params_optimize(points, profile, optimization_mode)
                    response = ors_client.request('/optimization', {}, post_json=params)

                    sink.addFeature(directions_core.get_output_features_optimization(
                        response,
                        profile,
                        from_value=from_value
                    ))
                else:
                    params = directions_core.build_default_parameters(preference, point_list=points, options=options)
                    response = ors_client.request('/v2/directions/' + profile + '/geojson', {}, post_json=params)

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
