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
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterString,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSink
                       )

from ORStools import ICON_DIR
from ORStools.core import PROFILES, UNITS


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

        self.addParameter(
            QgsProcessingParameterString(
                name=self.IN_KEY,
                description="API key from https://openrouteservice.org/dev",
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.IN_POINTS,
                "Point layer to calculate isochrones for",
                [QgsProcessing.TypeVectorPoint]
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
                description="Isochrones or equidistants",
                options=UNITS,
                defaultValue=UNITS[0],
            )
        )

        self.addParameter(
            QgsProcessingParameterString(
                name=self.IN_RANGES,
                description="Range in comma-separated minutes or meters",
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

    def displayName(self):
        return 'Generate ' + self.ALGO_NAME.capitalize()

    def icon(self):
        return QIcon(os.path.join(ICON_DIR, 'icon.png'))

    def createInstance(self):
        return ORSisochronesAlgo()