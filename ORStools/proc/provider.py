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

from qgis.core import QgsProcessingProvider

from qgis.PyQt.QtGui import QIcon

from ORStools import RESOURCE_PREFIX, PLUGIN_NAME, __version__
from .directions_lines_proc import ORSDirectionsLinesAlgo
from .directions_points_layer_proc import ORSDirectionsPointsLayerAlgo
from .directions_points_layers_proc import ORSDirectionsPointsLayersAlgo
from .isochrones_layer_proc import ORSIsochronesLayerAlgo
from .isochrones_point_proc import ORSIsochronesPointAlgo
from .matrix_proc import ORSMatrixAlgo


class ORStoolsProvider(QgsProcessingProvider):
    def __init__(self):
        QgsProcessingProvider.__init__(self)

    def unload(self) -> None:
        """
        Unloads the provider. Any tear-down steps required by the provider
        should be implemented here.
        """
        pass

    # noinspection PyPep8Naming
    def loadAlgorithms(self) -> None:
        """
        Loads all algorithms belonging to this provider.
        """
        #
        self.addAlgorithm(ORSDirectionsPointsLayersAlgo())
        self.addAlgorithm(ORSDirectionsPointsLayerAlgo())
        self.addAlgorithm(ORSDirectionsLinesAlgo())
        self.addAlgorithm(ORSIsochronesLayerAlgo())
        self.addAlgorithm(ORSIsochronesPointAlgo())
        self.addAlgorithm(ORSMatrixAlgo())

    @staticmethod
    def icon() -> QIcon:
        return QIcon(RESOURCE_PREFIX + "icon_orstools.png")

    @staticmethod
    def id() -> str:
        """
        Returns the unique provider id, used for identifying the provider. This
        string should be a unique, short, character only string, eg "qgis" or
        "gdal". This string should not be localised.
        """
        return PLUGIN_NAME.strip()

    @staticmethod
    def name() -> str:
        """
        Returns the provider name, which is used to describe the provider
        within the GUI.

        This string should be short (e.g. "Lastools") and localised.
        """
        return PLUGIN_NAME

    # noinspection PyPep8Naming
    @staticmethod
    def longName() -> str:
        """
        Returns the a longer version of the provider name, which can include
        extra details such as version numbers. E.g. "Lastools LIDAR tools
        (version 2.2.1)". This string should be localised. The default
        implementation returns the same string as name().
        """
        return PLUGIN_NAME + " plugin v" + __version__
