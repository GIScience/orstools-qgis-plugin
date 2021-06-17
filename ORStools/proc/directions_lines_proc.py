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
class ORSDirectionsLinesAlgorithm(ORSBaseProcessingAlgorithm):
    """Algorithm class for Directions Lines."""
    def __init__(self):
        super().__init__()
        self.ALGO_NAME = 'directions_from_polylines_layer'
        self.GROUP = "Directions"
        self.IN_LINES = "INPUT_LINE_LAYER"
        self.IN_FIELD = "INPUT_LAYER_FIELD"
        self.IN_PROFILE = "INPUT_PROFILE"
        self.IN_PREFERENCE = "INPUT_PREFERENCE"
        self.IN_OPTIMIZE = "INPUT_OPTIMIZE"
        self.IN_MODE = "INPUT_MODE"
        self.PARAMETERS = [
            QgsProcessingParameterFeatureSource(
                name=self.IN_LINES,
                description="Input Line layer",
                types=[QgsProcessing.TypeVectorLine],
            ),
            QgsProcessingParameterField(
                name=self.IN_FIELD,
                description="Layer ID Field",
                parentLayerParameterName=self.IN_LINES,
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
                self.IN_OPTIMIZE,
                "Traveling Salesman",
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

        # Get parameter values
        source = self.parameterAsSource(
            parameters,
            self.IN_LINES,
            context
        )

        # parameters[self.IN_FIELD] returns a PyQt5.QtCore.QVariant with "NULL" as content
        # in case of absence of self.IN_FIELD.
        # qgis overwrites this type's __bool__ in
        # https://github.com/qgis/QGIS/blob/master/python/PyQt/PyQt5/QtCore.py:
        # def __bool__(self):
        #     return not self.isNull()
        # The check below works because of that.
        source_field_name = parameters[self.IN_FIELD]
        get_fields_options = dict()
        if source_field_name:
            get_fields_options.update(
                    from_type=source.fields().field(source_field_name).type(),
                    from_name=source_field_name
                    )

        sink_fields = directions_core.get_fields(**get_fields_options, line=True)

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUT, context, sink_fields,
                                               source.wkbType(),
                                               QgsCoordinateReferenceSystem.fromEpsgId(4326))
        count = source.featureCount()

        for num, (line, field_value) in enumerate(self._get_sorted_lines(source, source_field_name)):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            try:
                if optimization_mode is not None:
                    params = get_params_optimize(line, profile, optimization_mode)
                    response = ors_client.request('/optimization', {}, post_json=params)

                    sink.addFeature(directions_core.get_output_features_optimization(
                        response,
                        profile,
                        from_value=field_value
                    ))
                else:
                    params = directions_core.build_default_parameters(preference, point_list=line)
                    response = ors_client.request('/v2/directions/' + profile + '/geojson', {}, post_json=params)

                    sink.addFeature(directions_core.get_output_feature_directions(
                        response,
                        profile,
                        preference,
                        from_value=field_value
                    ))
            except (exceptions.ApiError,
                    exceptions.InvalidKey,
                    exceptions.GenericServerError) as e:
                msg = f"Feature ID {num} caused a {e.__class__.__name__}:\n{str(e)}"
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
        x_former = transform.transformToWGS(layer.sourceCrs())

        for feat in sorted(layer.getFeatures(), key=lambda f: f.id()):
            line = None
            field_value = feat[field_name] if field_name else None

            if layer.wkbType() == QgsWkbTypes.MultiLineString:
                # TODO: only takes the first polyline geometry from the multiline geometry currently
                # Loop over all polyline geometries
                line = [x_former.transform(QgsPointXY(point)) for point in feat.geometry().asMultiPolyline()[0]]

            elif layer.wkbType() == QgsWkbTypes.LineString:
                line = [x_former.transform(QgsPointXY(point)) for point in feat.geometry().asPolyline()]

            yield line, field_value
