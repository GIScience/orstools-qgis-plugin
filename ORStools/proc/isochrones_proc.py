# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ORStools
                                 A QGIS plugin
 falk
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
import webbrowser

from PyQt5.QtGui import QIcon

from qgis.core import (QgsWkbTypes,
                       QgsCoordinateReferenceSystem,
                       QgsProcessing,
                       QgsProcessingUtils,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterString,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSink,
                       )
from . import HELP_DIR
from ORStools import ENDPOINTS, ICON_DIR, __help__
from ORStools.core import client, isochrones_core, PROFILES, DIMENSIONS
from ORStools.utils import convert, transform, exceptions


class ORSisochronesAlgo(QgsProcessingAlgorithm):
    # TODO: create base algorithm class common to all modules

    ALGO_NAME = 'isochrones'

    IN_POINTS = "INPUT_POINT_LAYER"
    IN_FIELD = "INPUT_FIELD"
    IN_PROFILE = "INPUT_PROFILE"
    IN_METRIC = 'INPUT_METRIC'
    IN_RANGES = 'INPUT_RANGES'
    IN_KEY = 'INPUT_APIKEY'
    IN_DIFFERENCE = 'INPUT_DIFFERENCE'
    OUT = 'OUTPUT'

    # Init ORS client
    clnt = client.Client()
    # Save reference to output layer
    isochrones = isochrones_core.Isochrones()
    dest_id = None
    # difference = None

    def initAlgorithm(self, configuration, p_str=None, Any=None, *args, **kwargs):

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                name=self.IN_POINTS,
                description="Input Point layer",
                types=[QgsProcessing.TypeVectorPoint],
            )
        )

        # self.addParameter(
        #     QgsProcessingParameterBoolean(
        #         name=self.IN_DIFFERENCE,
        #         description="Dissolve and calulate isochrone difference",
        #     )
        # )

        self.addParameter(
            QgsProcessingParameterField(
                name=self.IN_FIELD,
                description="ID Field (can be used for joining)",
                parentLayerParameterName=self.IN_POINTS,
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.IN_PROFILE,
                "Travel mode",
                PROFILES
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                name=self.IN_METRIC,
                description="Dimension",
                options=DIMENSIONS,
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                name=self.IN_RANGES,
                description="Comma-separated ranges [mins or m]",
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                name=self.OUT,
                description="Isochrones",
            )
        )

    def name(self):
        return self.ALGO_NAME

    def shortHelpString(self):
        """Displays the sidebar help in the algorithm window"""

        file = os.path.join(
            HELP_DIR,
            'algorithm_isochrone.help'
        )
        with open(file) as helpf:
            msg = helpf.read()

        return msg

    def helpUrl(self):
        """will be connected to the Help button in the Algorithm window"""
        return __help__

    def displayName(self):
        return 'Generate ' + self.ALGO_NAME.capitalize()

    def icon(self):
        return QIcon(os.path.join(ICON_DIR, 'icon_isochrones.png'))

    def createInstance(self):
        return ORSisochronesAlgo()

    # TODO: preprocess parameters to avoid the range clenaup below:
    # https://www.qgis.org/pyqgis/master/core/Processing/QgsProcessingAlgorithm.html#qgis.core.QgsProcessingAlgorithm.preprocessParameters

    def processAlgorithm(self, parameters, context, feedback):
        params = dict()
        params['attributes'] = 'total_pop'

        params['profile'] = profile = PROFILES[self.parameterAsEnum(parameters, self.IN_PROFILE, context)]
        params['range_type'] = dimension = DIMENSIONS[self.parameterAsEnum(parameters, self.IN_METRIC, context)]

        factor = 60 if params['range_type'] == 'time' else 1
        ranges_raw = self.parameterAsString(parameters, self.IN_RANGES, context)
        ranges_proc = [x * factor for x in map(int, ranges_raw.split(','))]
        params['range'] = convert.comma_list(ranges_proc)

        # self.difference = self.parameterAsBool(parameters, self.IN_DIFFERENCE, context)
        source = self.parameterAsSource(parameters, self.IN_POINTS, context)
        if source.wkbType() == 4:
            raise QgsProcessingException("TypeError: Multipoint Layers are not accepted. Please convert to single geometry layer.")

        # Get ID field properties
        id_field_name = self.parameterAsString(parameters, self.IN_FIELD, context)
        id_field_id = source.fields().lookupField(id_field_name)
        id_field = source.fields().field(id_field_id)

        # Populate iso_layer instance with parameters
        self.isochrones.set_parameters(source.sourceName(), profile, dimension, id_field.type(), id_field_name, factor)

        (sink, self.dest_id) = self.parameterAsSink(parameters, self.OUT, context,
                                                    self.isochrones.get_fields(),
                                                    QgsWkbTypes.Polygon,  # Needs Multipolygon if difference parameter will ever be reactivated
                                                    QgsCoordinateReferenceSystem(4326))
        # Make the actual requests
        for num, properties in enumerate(self.get_sorted_feature_parameters(source)):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            # Get transformed coordinates and feature
            params['locations'], feat = properties
            params['id'] = feat[id_field_name]

            feedback.setProgress(int(100.0 / source.featureCount() * num))

            # If feature causes error, report and continue with next
            try:
                # Populate features from response
                response = self.clnt.request(ENDPOINTS[self.ALGO_NAME], params)
            except exceptions.ApiError as e:
                feedback.reportError("Feature ID {} caused a {}:\n{}".format(
                    feat[id_field_name],
                    e.__class__.__name__,
                    str(e))
                )
                continue

            for isochrone in self.isochrones.get_features(response, feat[id_field_name]):
                sink.addFeature(isochrone)

        return {self.OUT: self.dest_id}

    def postProcessAlgorithm(self, context, feedback):

        processed_layer = QgsProcessingUtils.mapLayerFromString(self.dest_id, context)
        self.isochrones.stylePoly(processed_layer)

        return {self.OUT: self.dest_id}


    def get_sorted_feature_parameters(self, layer):
        """generator to yield geometry and id of features sorted by feature ID. Careful: feat.id() is not necessarily
        permanent"""
        # First get coordinate transformer
        xformer = transform.transformToWGS(layer.sourceCrs())

        for feat in sorted(layer.getFeatures(), key=lambda f: f.id()):
            x_point = xformer.transform(feat.geometry().asPoint())

            yield (convert.build_coords([x_point.x(), x_point.y()]), feat)

