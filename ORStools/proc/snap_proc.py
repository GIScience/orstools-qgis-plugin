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

from qgis.core import QgsProcessingParameterFeatureSource, QgsProcessing, QgsProcessingParameterNumber
from ORStools.proc.base_processing_algorithm import ORSBaseProcessingAlgorithm


# noinspection PyPep8Naming
class ORSSnapAlgo(ORSBaseProcessingAlgorithm):
    def __init__(self):
        super().__init__()
        self.IN_POINTS = "IN_POINTS"
        self.RADIUS = "RADIUS"
        self.PARAMETERS: list = [
            QgsProcessingParameterFeatureSource(
                name=self.IN_POINTS,
                description=self.tr("Input Point layer"),
                types=[QgsProcessing.SourceType.TypeVectorPoint],
            ),
            QgsProcessingParameterNumber(
                name=self.RADIUS,
                description=self.tr("Search Radius [m]"),
            ),

        ]