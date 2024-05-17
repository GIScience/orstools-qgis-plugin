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
    QgsCoordinateReferenceSystem,
    QgsProcessing,
    QgsProcessingUtils,
    QgsProcessingException,
    QgsProcessingParameterField,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterString,
    QgsProcessingParameterEnum,
    QgsProcessingParameterNumber,
    QgsProcessingContext,
    QgsProcessingFeedback,
)

from ORStools.common import isochrones_core, PROFILES, DIMENSIONS, LOCATION_TYPES
from ORStools.proc.base_processing_algorithm import ORSBaseProcessingAlgorithm
from ORStools.utils import transform, exceptions, logger


# noinspection PyPep8Naming
class ORSIsochronesLayerAlgo(ORSBaseProcessingAlgorithm):
    def __init__(self):
        super().__init__()
        self.ALGO_NAME = "isochrones_from_layer"
        self.GROUP = "Isochrones"

        self.IN_POINTS: str = "INPUT_POINT_LAYER"
        self.IN_FIELD: str = "INPUT_FIELD"
        self.IN_METRIC: str = "INPUT_METRIC"
        self.IN_RANGES: str = "INPUT_RANGES"
        self.IN_KEY: str = "INPUT_APIKEY"
        self.IN_DIFFERENCE: str = "INPUT_DIFFERENCE"
        self.USE_SMOOTHING: str = "USE_SMOOTHING"
        self.IN_SMOOTHING: str = "INPUT_SMOOTHING"
        self.LOCATION_TYPE: str = "LOCATION_TYPE"
        self.PARAMETERS: list = [
            QgsProcessingParameterFeatureSource(
                name=self.IN_POINTS,
                description=self.tr("Input Point layer"),
                types=[QgsProcessing.SourceType.TypeVectorPoint],
            ),
            # QgsProcessingParameterBoolean(
            #     name=self.IN_DIFFERENCE,
            #     description=self.tr("Dissolve and calculate isochrone difference"),
            # )
            QgsProcessingParameterField(
                name=self.IN_FIELD,
                description=self.tr("Input layer ID Field (mutually exclusive with Point option)"),
                parentLayerParameterName=self.IN_POINTS,
                optional=True,
            ),
            QgsProcessingParameterEnum(
                name=self.IN_METRIC,
                description=self.tr("Dimension"),
                options=DIMENSIONS,
                defaultValue=DIMENSIONS[0],
            ),
            QgsProcessingParameterString(
                name=self.IN_RANGES,
                description=self.tr("Comma-separated ranges [min or m]"),
                defaultValue="5, 10",
            ),
            QgsProcessingParameterNumber(
                name=self.IN_SMOOTHING,
                description=self.tr("Smoothing factor between 0 [detailed] and 100 [generalized]"),
                defaultValue=None,
                minValue=0,
                maxValue=100,
                optional=True,
            ),
            QgsProcessingParameterEnum(
                name=self.LOCATION_TYPE,
                description=self.tr("Location Type"),
                options=LOCATION_TYPES,
                defaultValue=LOCATION_TYPES[0],
            ),
        ]

    # Save some important references
    # TODO bad style, refactor
    isochrones = isochrones_core.Isochrones()
    dest_id = None
    crs_out = QgsCoordinateReferenceSystem.fromEpsgId(4326)
    # difference = None

    # TODO: preprocess parameters to options the range cleanup below:
    # https://www.qgis.org/pyqgis/master/core/Processing/QgsProcessingAlgorithm.html#qgis.core.QgsProcessingAlgorithm.prepareAlgorithm
    def processAlgorithm(
        self, parameters: dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, str]:
        ors_client = self._get_ors_client_from_provider(parameters[self.IN_PROVIDER], feedback)

        profile = dict(enumerate(PROFILES))[parameters[self.IN_PROFILE]]
        dimension = dict(enumerate(DIMENSIONS))[parameters[self.IN_METRIC]]
        location_type = dict(enumerate(LOCATION_TYPES))[parameters[self.LOCATION_TYPE]]

        factor = 60 if dimension == "time" else 1
        ranges_raw = parameters[self.IN_RANGES]
        ranges_proc = [x * factor for x in map(float, ranges_raw.split(","))]
        # round to the nearest second or meter
        ranges_proc = list(map(int, ranges_proc))
        smoothing = parameters[self.IN_SMOOTHING]

        # self.difference = self.parameterAsBool(parameters, self.IN_DIFFERENCE, context)
        source = self.parameterAsSource(parameters, self.IN_POINTS, context)

        # get smoothness parameter value
        options = self.parseOptions(parameters, context)

        # Make the actual requests
        requests = []
        if QgsWkbTypes.flatType(source.wkbType()) == QgsWkbTypes.Type.MultiPoint:
            raise QgsProcessingException(
                "TypeError: Multipoint Layers are not accepted. Please convert to single geometry layer."
            )

        # Get ID field properties
        id_field_name = parameters[self.IN_FIELD]
        parameter_options = list()
        if id_field_name:
            id_field = source.fields().field(id_field_name)
            parameter_options = [id_field.type(), id_field_name]

        self.isochrones.set_parameters(profile, dimension, factor, *parameter_options)

        for locations, id_value in self.get_sorted_feature_parameters(source, id_field_name):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            params = {
                "locations": locations,
                "range_type": dimension,
                "range": ranges_proc,
                "attributes": ["total_pop"],
                "id": id_value,
                "options": options,
                "location_type": location_type,
            }

            # only include smoothing if set
            if smoothing is not None:
                params["smoothing"] = smoothing

            requests.append(params)

        (sink, self.dest_id) = self.parameterAsSink(
            parameters,
            self.OUT,
            context,
            self.isochrones.get_fields(),
            QgsWkbTypes.Type.Polygon,
            # Needs Multipolygon if difference parameter will ever be
            # reactivated
            self.crs_out,
        )

        for num, params in enumerate(requests):
            if feedback.isCanceled():
                break

            # If feature causes error, report and continue with next
            try:
                # Populate features from response
                response = ors_client.request("/v2/isochrones/" + profile, {}, post_json=params)

                for isochrone in self.isochrones.get_features(response, params["id"]):
                    sink.addFeature(isochrone)

            except (exceptions.ApiError, exceptions.InvalidKey, exceptions.GenericServerError) as e:
                msg = f"Feature ID {params['id']} caused a {e.__class__.__name__}:\n{str(e)}"
                feedback.reportError(msg)
                logger.log(msg, 2)
                continue
            feedback.setProgress(int(100.0 / source.featureCount() * num))

        return {self.OUT: self.dest_id}

    # noinspection PyUnusedLocal
    def postProcessAlgorithm(
        self, context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, str]:
        """Style polygon layer in post-processing step."""
        # processed_layer = self.isochrones.calculate_difference(self.dest_id, context)
        processed_layer = QgsProcessingUtils.mapLayerFromString(self.dest_id, context)
        self.isochrones.stylePoly(processed_layer)

        return {self.OUT: self.dest_id}

    @staticmethod
    def get_sorted_feature_parameters(
        layer: QgsProcessingParameterFeatureSource, id_field_name: str
    ):
        """
        Generator to yield geometry and id of features sorted by feature ID. Careful: feat.id() is not necessarily
        permanent

        :param layer: source input layer.
        :param id_field_name: layer field containing id values
        """
        # First get coordinate transformer
        x_former = transform.transformToWGS(layer.sourceCrs())

        for feat in sorted(layer.getFeatures(), key=lambda f: f.id()):
            x_point = x_former.transform(feat.geometry().asPoint())
            id_value = feat[id_field_name] if id_field_name else None

            yield [[round(x_point.x(), 6), round(x_point.y(), 6)]], id_value

    def displayName(self) -> str:
        """
        Algorithm name shown in QGIS toolbox
        :return:
        """
        return self.tr("Isochrones from Point-Layer")
