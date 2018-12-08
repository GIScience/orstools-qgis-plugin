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

from PyQt5.QtGui import QIcon

from qgis.core import (QgsMessageLog,
                       QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingAlgRunnerTask,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterString,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSink,
                       )
from ORStools import ICON_DIR
from ORStools.core import client, isochrones_core, PROFILES, UNITS
from ORStools.utils import convert, transform, logger


class ORSisochronesAlgo(QgsProcessingAlgorithm):
    # TODO: create base algorithm class common to all modules

    ALGO_NAME = 'isochrones'

    IN_POINTS = "INPUT_POINT_LAYER"
    IN_PROFILE = "INPUT_PROFILE"
    IN_METRIC = 'INPUT_METRIC'
    IN_RANGES = 'INPUT_RANGES'
    IN_KEY = 'INPUT_APIKEY'
    IN_SIMPLIFY = 'INPUT_SIMPLIFY'
    OUT = 'OUTPUT'

    def initAlgorithm(self, configuration, p_str=None, Any=None, *args, **kwargs):

        # self.addParameter(
        #     QgsProcessingParameterString(
        #         name=self.IN_KEY,
        #         description="API key from https://openrouteservice.org/dev",
        #     )
        # )

        # Init ORS client
        self.clnt = client.Client()

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                name=self.IN_POINTS,
                description="Point layer to calculate isochrones for",
                types=[QgsProcessing.TypeVectorPoint],
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.IN_PROFILE,
                "Transport mode to use for the isochrones",
                PROFILES
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                name=self.IN_METRIC,
                description="Dimension",
                options=UNITS,
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
                description="Output isochrones",
            )
        )

    def name(self):
        return self.ALGO_NAME

    def shortHelpString(self):
        """Displays the sidebar bar in the algorithm window"""
        pass
        # file=os.path.realpath(__file__)
        # file = os.path.join(os.path.dirname(file),'ContourGeneratorAlgorithm.help')
        # if not os.path.exists(file):
        #     return ''
        # with open(file) as helpf:
        #     help=helpf.read()
        # return help

    def helpUrl(self):
        """will be connected to the Help button in the Algorithm window"""
        pass

    def displayName(self):
        return 'Generate ' + self.ALGO_NAME.capitalize()

    def icon(self):
        return QIcon(os.path.join(ICON_DIR, 'icon_isochrones.png'))

    def createInstance(self):
        return ORSisochronesAlgo()

    # TODO: preprocess parameters to avoid the range clenaup below:
    # https://www.qgis.org/pyqgis/master/core/Processing/QgsProcessingAlgorithm.html#qgis.core.QgsProcessingAlgorithm.preprocessParameters

    def processAlgorithm(self, parameters, context, feedback):
        _params = dict()

        _params['profile'] = PROFILES[self.parameterAsEnum(parameters, self.IN_PROFILE, context)]
        _params['range_type'] = UNITS[self.parameterAsEnum(parameters, self.IN_METRIC, context)]

        _factor = 60 if _params['range_type'] == 'time' else 1
        _ranges_raw = self.parameterAsString(parameters, self.IN_RANGES, context)
        _ranges_proc = [x * _factor for x in map(int, _ranges_raw.split(','))]
        _params['range'] = convert.comma_list(_ranges_proc)

        _source = self.parameterAsSource(parameters, self.IN_POINTS, context)
        if _source.wkbType() == 4:
            raise QgsProcessingException("TypeError: Multipoint Layers are not accepted. Please convert to single geometry layer.")

        # Make the actual requests
        for num, properties in enumerate(self.getFeatureParameters(_source)):
            _params['locations'], _params['id'] = properties

            feedback.pushInfo("Calculating isochrone {}".format(num))

            # This is the line making the request
            response = self.clnt.request('/isochrones', _params)

    def getFeatureParameters(self, layer):
        """generator to yield geometry and id"""

        # Reproject layer if necessary
        layer_crs = layer.sourceCrs().authid()
        if not layer_crs.endswith('4326'):
            layer = transform.transformToWGS(layer, layer_crs)

        locations_ids = []
        feats = layer.getFeatures()
        self.feature_count = layer.featureCount()
        for feat in feats:
            geom = feat.geometry().asPoint()
            coords = [geom.x(), geom.y()]

            yield (convert.build_coords(coords), str(feat.id()))

