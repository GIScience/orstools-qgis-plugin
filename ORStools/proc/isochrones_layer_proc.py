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

import os.path
from copy import deepcopy

from PyQt5.QtGui import QIcon

from qgis.core import (QgsWkbTypes,
                       QgsCoordinateReferenceSystem,
                       QgsField,
                       QgsProcessing,
                       QgsProcessingUtils,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterString,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSink
                       )
from . import HELP_DIR
from ORStools import RESOURCE_PREFIX, __help__
from ORStools.common import client, isochrones_core, PROFILES, DIMENSIONS
from ORStools.utils import convert, transform, exceptions, configmanager, logger


class ORSisochronesLayerAlgo(QgsProcessingAlgorithm):
    # TODO: create base algorithm class common to all modules

    ALGO_NAME = 'isochrones_from_layer'
    ALGO_NAME_LIST = ALGO_NAME.split('_')

    IN_PROVIDER = "INPUT_PROVIDER"
    IN_POINTS = "INPUT_POINT_LAYER"
    IN_FIELD = "INPUT_FIELD"
    IN_PROFILE = "INPUT_PROFILE"
    IN_METRIC = 'INPUT_METRIC'
    IN_RANGES = 'INPUT_RANGES'
    IN_KEY = 'INPUT_APIKEY'
    IN_DIFFERENCE = 'INPUT_DIFFERENCE'
    OUT = 'OUTPUT'

    # Save some important references
    isochrones = isochrones_core.Isochrones()
    dest_id = None
    crs_out = QgsCoordinateReferenceSystem.fromEpsgId(4326)
    # difference = None

    def initAlgorithm(self, configuration, p_str=None, Any=None, *args, **kwargs):

        providers = [provider['name'] for provider in configmanager.read_config()['providers']]
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
                name=self.IN_POINTS,
                description="Input Point layer",
                types=[QgsProcessing.TypeVectorPoint]
            )
        )

        # self.addParameter(
        #     QgsProcessingParameterBoolean(
        #         name=self.IN_DIFFERENCE,
        #         description="Dissolve and calculate isochrone difference",
        #     )
        # )

        self.addParameter(
            QgsProcessingParameterField(
                name=self.IN_FIELD,
                description="Input layer ID Field (mutually exclusive with Point option)",
                parentLayerParameterName=self.IN_POINTS,
                optional=True
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
                name=self.IN_METRIC,
                description="Dimension",
                options=DIMENSIONS,
                defaultValue=DIMENSIONS[0]
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                name=self.IN_RANGES,
                description="Comma-separated ranges [mins or m]",
                defaultValue="5, 10"
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                name=self.OUT,
                description="Isochrones",
                createByDefault=False
            )
        )

    def group(self):
        return "Isochrones"

    def groupId(self):
        return 'isochrones'

    def name(self):
        return self.ALGO_NAME

    def shortHelpString(self):
        """Displays the sidebar help in the algorithm window"""

        file = os.path.join(
            HELP_DIR,
            'algorithm_isochrone_layer.help'
        )
        with open(file, encoding='utf-8') as helpf:
            msg = helpf.read()

        return msg

    def helpUrl(self):
        """will be connected to the Help button in the Algorithm window"""
        return __help__

    def displayName(self):
        return " ".join(map(lambda x: x.capitalize(), self.ALGO_NAME_LIST))

    def icon(self):
        return QIcon(RESOURCE_PREFIX + 'icon_isochrones.png')

    def createInstance(self):
        return ORSisochronesLayerAlgo()

    # TODO: preprocess parameters to options the range cleanup below:
    # https://www.qgis.org/pyqgis/master/core/Processing/QgsProcessingAlgorithm.html#qgis.core.QgsProcessingAlgorithm.preprocessParameters

    def processAlgorithm(self, parameters, context, feedback):
        # Init ORS client
        providers = configmanager.read_config()['providers']
        provider = providers[self.parameterAsEnum(parameters, self.IN_PROVIDER, context)]
        clnt = client.Client(provider)
        clnt.overQueryLimit.connect(lambda : feedback.reportError("OverQueryLimit: Retrying..."))

        params = dict()
        params['attributes'] = ['total_pop']

        profile = PROFILES[self.parameterAsEnum(parameters, self.IN_PROFILE, context)]
        params['range_type'] = dimension = DIMENSIONS[self.parameterAsEnum(parameters, self.IN_METRIC, context)]

        factor = 60 if params['range_type'] == 'time' else 1
        ranges_raw = self.parameterAsString(parameters, self.IN_RANGES, context)
        ranges_proc = [x * factor for x in map(int, ranges_raw.split(','))]
        params['range'] = ranges_proc

        # self.difference = self.parameterAsBool(parameters, self.IN_DIFFERENCE, context)
        source = self.parameterAsSource(parameters, self.IN_POINTS, context)

        # Make the actual requests
        requests = []
        if source.wkbType() == 4:
            raise QgsProcessingException("TypeError: Multipoint Layers are not accepted. Please convert to single geometry layer.")

        # Get ID field properties
        id_field_name = self.parameterAsString(parameters, self.IN_FIELD, context)
        id_field_id = source.fields().lookupField(id_field_name)

        # LookupField will return -1 if the name cannot be found.
        # Try the first field in this case.
        if id_field_id == -1: 
            id_field_id = 0

        # Populate iso_layer instance with parameters
        try:
            id_field = source.fields().field(id_field_id)
            id_field_name = source.fields().field(id_field_id).name()
            self.isochrones.set_parameters(profile, dimension, factor, id_field.type(), id_field_name)
        except KeyError: # Scratch layers don't neccessarily have fields
            self.isochrones.set_parameters(profile, dimension, factor)

        for properties in self.get_sorted_feature_parameters(source):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            # Get transformed coordinates and feature
            params['locations'], feat = properties
            try:
                params['id'] = feat[id_field_name]
            except KeyError:
                params['id'] = None
            requests.append(deepcopy(params))

        (sink, self.dest_id) = self.parameterAsSink(parameters, self.OUT, context,
                                                    self.isochrones.get_fields(),
                                                    QgsWkbTypes.Polygon,  # Needs Multipolygon if difference parameter will ever be reactivated
                                                    self.crs_out)

        for num, params in enumerate(requests):
            if feedback.isCanceled():
                break

            # If feature causes error, report and continue with next
            try:
                # Populate features from response
                response = clnt.request('/v2/isochrones/' + profile, {}, post_json=params)

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

    def postProcessAlgorithm(self, context, feedback):
        """Style polygon layer in post-processing step."""
        # processed_layer = self.isochrones.calculate_difference(self.dest_id, context)
        processed_layer= QgsProcessingUtils.mapLayerFromString(self.dest_id, context)
        self.isochrones.stylePoly(processed_layer)

        return {self.OUT: self.dest_id}

    def get_sorted_feature_parameters(self, layer):
        """
        Generator to yield geometry and id of features sorted by feature ID. Careful: feat.id() is not necessarily
        permanent

        :param layer: source input layer.
        :type layer: QgsProcessingParameterFeatureSource
        """
        # First get coordinate transformer
        xformer = transform.transformToWGS(layer.sourceCrs())

        for feat in sorted(layer.getFeatures(), key=lambda f: f.id()):
            x_point = xformer.transform(feat.geometry().asPoint())

            yield [[round(x_point.x(), 6), round(x_point.y(), 6)]], feat

