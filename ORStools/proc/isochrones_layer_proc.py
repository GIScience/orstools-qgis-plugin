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
                       QgsProcessingUtils,
                       QgsProcessingException,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterString,
                       QgsProcessingParameterEnum
                       )

from ORStools.common import isochrones_core, PROFILES, DIMENSIONS
from ORStools.proc.base_processing_algorithm import ORSBaseProcessingAlgorithm
from ORStools.utils import transform, exceptions, logger


# noinspection PyPep8Naming
class ORSIsochronesLayerAlgo(ORSBaseProcessingAlgorithm):
    def __init__(self):
        super().__init__()
        self.ALGO_NAME = 'isochrones_from_layer'
        self.GROUP = 'Isochrones'

        self.IN_POINTS = "INPUT_POINT_LAYER"
        self.IN_FIELD = "INPUT_FIELD"
        self.IN_PROFILE = "INPUT_PROFILE"
        self.IN_METRIC = 'INPUT_METRIC'
        self.IN_RANGES = 'INPUT_RANGES'
        self.IN_KEY = 'INPUT_APIKEY'
        self.IN_DIFFERENCE = 'INPUT_DIFFERENCE'
        self.PARAMETERS = [
            QgsProcessingParameterFeatureSource(
                name=self.IN_POINTS,
                description="Input Point layer",
                types=[QgsProcessing.TypeVectorPoint]
            ),
            # QgsProcessingParameterBoolean(
            #     name=self.IN_DIFFERENCE,
            #     description="Dissolve and calculate isochrone difference",
            # )
            QgsProcessingParameterField(
                name=self.IN_FIELD,
                description="Input layer ID Field (mutually exclusive with Point option)",
                parentLayerParameterName=self.IN_POINTS,
                optional=True
            ),
            QgsProcessingParameterEnum(
                self.IN_PROFILE,
                "Travel mode",
                PROFILES,
                defaultValue=PROFILES[0]
            ),
            QgsProcessingParameterEnum(
                name=self.IN_METRIC,
                description="Dimension",
                options=DIMENSIONS,
                defaultValue=DIMENSIONS[0]
            ),
            QgsProcessingParameterString(
                name=self.IN_RANGES,
                description="Comma-separated ranges [min or m]",
                defaultValue="5, 10"
            )
        ]

    # Save some important references
    # TODO bad style, refactor
    isochrones = isochrones_core.Isochrones()
    dest_id = None
    crs_out = QgsCoordinateReferenceSystem.fromEpsgId(4326)
    # difference = None

    # TODO: preprocess parameters to options the range cleanup below:
    # https://www.qgis.org/pyqgis/master/core/Processing/QgsProcessingAlgorithm.html#qgis.core.QgsProcessingAlgorithm.prepareAlgorithm
    def processAlgorithm(self, parameters, context, feedback):
        ors_client = self._get_ors_client_from_provider(parameters[self.IN_PROVIDER], feedback)

        profile = dict(enumerate(PROFILES))[parameters[self.IN_PROFILE]]
        dimension = dict(enumerate(DIMENSIONS))[parameters[self.IN_METRIC]]

        factor = 60 if dimension == 'time' else 1
        ranges_raw = parameters[self.IN_RANGES]
        ranges_proc = [x * factor for x in map(int, ranges_raw.split(','))]

        # self.difference = self.parameterAsBool(parameters, self.IN_DIFFERENCE, context)
        source = self.parameterAsSource(parameters, self.IN_POINTS, context)

        # Make the actual requests
        requests = []
        if source.wkbType() == 4:
            raise QgsProcessingException(
                "TypeError: Multipoint Layers are not accepted. Please convert to single geometry layer.")

        # Get ID field properties
        id_field_name = parameters[self.IN_FIELD]
        id_field_id = source.fields().indexOf(id_field_name)

        # indexOf will return -1 if the name cannot be found.
        # Try the first field in this case.
        if id_field_id == -1:
            id_field_id = 0

        # Populate iso_layer instance with parameters
        try:
            id_field = source.fields().field(id_field_id)
            id_field_name = source.fields().field(id_field_id).name()
            self.isochrones.set_parameters(profile, dimension, factor, id_field.type(), id_field_name)
        except KeyError:  # Scratch layers don't necessarily have fields
            self.isochrones.set_parameters(profile, dimension, factor)

        for locations, id_value in self.get_sorted_feature_parameters(source, id_field_name):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            requests.append({
                "locations": locations,
                "range_type": dimension,
                "range": ranges_proc,
                "attributes": ['total_pop'],
                "id": id_value,
            })

        (sink, self.dest_id) = self.parameterAsSink(parameters, self.OUT, context,
                                                    self.isochrones.get_fields(),
                                                    QgsWkbTypes.Polygon,
                                                    # Needs Multipolygon if difference parameter will ever be
                                                    # reactivated
                                                    self.crs_out)

        for num, params in enumerate(requests):
            if feedback.isCanceled():
                break

            # If feature causes error, report and continue with next
            try:
                # Populate features from response
                response = ors_client.request('/v2/isochrones/' + profile, {}, post_json=params)

                for isochrone in self.isochrones.get_features(response, params['id']):
                    sink.addFeature(isochrone)

            except (exceptions.ApiError,
                    exceptions.InvalidKey,
                    exceptions.GenericServerError) as e:
                msg = f"Feature ID {params['id']} caused a {e.__class__.__name__}:\n{str(e)}"
                feedback.reportError(msg)
                logger.log(msg, 2)
                continue
            feedback.setProgress(int(100.0 / source.featureCount() * num))

        return {self.OUT: self.dest_id}

    # noinspection PyUnusedLocal
    def postProcessAlgorithm(self, context, feedback):
        """Style polygon layer in post-processing step."""
        # processed_layer = self.isochrones.calculate_difference(self.dest_id, context)
        processed_layer = QgsProcessingUtils.mapLayerFromString(self.dest_id, context)
        self.isochrones.stylePoly(processed_layer)

        return {self.OUT: self.dest_id}

    @staticmethod
    def get_sorted_feature_parameters(layer: QgsProcessingParameterFeatureSource, id_field_name: str):
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
            try:
                id_value = feat[id_field_name]
            except KeyError:
                id_value = None

            yield [[round(x_point.x(), 6), round(x_point.y(), 6)]], id_value
