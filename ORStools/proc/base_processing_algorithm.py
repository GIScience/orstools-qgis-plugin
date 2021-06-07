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
from qgis.core import (QgsProcessingAlgorithm,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingFeedback
                       )
from typing import Any

from PyQt5.QtGui import QIcon

from ORStools import RESOURCE_PREFIX, __help__
from ORStools.utils import configmanager
from ..common import client
from ..utils.processing import read_help_file


# noinspection PyPep8Naming
class ORSBaseProcessingAlgorithm(QgsProcessingAlgorithm):
    """Base algorithm class for ORS algorithms"""

    def __init__(self):
        """
        Default attributes used in all child classes
        """
        super().__init__()
        self.ALGO_NAME = ''
        self.GROUP = ''
        self.IN_PROVIDER = "INPUT_PROVIDER"
        self.OUT = 'OUTPUT'
        self.PARAMETERS = None

    def createInstance(self) -> Any:
        """
        Returns instance of any child class
        """
        return self.__class__()

    def group(self) -> str:
        """
        Returns group name (Directions, Isochrones, Matrix) defined in child class
        """
        return self.GROUP

    def groupId(self) -> str:
        return self.GROUP.lower()

    def name(self) -> str:
        """
        Returns algorithm name defined in child class
        """
        return self.ALGO_NAME

    def shortHelpString(self):
        """
        Displays the sidebar help in the algorithm window
        """
        return read_help_file(file_name=f'{self.ALGO_NAME}.help')

    @staticmethod
    def helpUrl():
        """
        Will be connected to the Help button in the Algorithm window
        """
        return __help__

    def displayName(self) -> str:
        """
        Algorithm name shown in QGIS toolbox
        :return:
        """
        return self.ALGO_NAME.capitalize().replace('_', ' ')

    def icon(self) -> QIcon:
        """
        Icon used for algorithm in QGIS toolbox
        """
        return QIcon(RESOURCE_PREFIX + f'icon_{self.groupId()}.png')

    def provider_parameter(self) -> QgsProcessingParameterEnum:
        """
        Parameter definition for provider, used in all child classes
        """
        providers = [provider['name'] for provider in configmanager.read_config()['providers']]
        return QgsProcessingParameterEnum(
            self.IN_PROVIDER,
            "Provider",
            providers,
            defaultValue=providers[0]
        )

    def output_parameter(self) -> QgsProcessingParameterFeatureSink:
        """
        Parameter definition for output, used in all child classes
        """
        return QgsProcessingParameterFeatureSink(
            name=self.OUT,
            description=self.GROUP,
        )

    @staticmethod
    def _get_ors_client_from_provider(provider: str, feedback: QgsProcessingFeedback) -> client.Client:
        """
        Connects client to provider and returns a client instance for requests to the ors API
        """
        providers = configmanager.read_config()['providers']
        ors_provider = providers[provider]
        ors_client = client.Client(ors_provider)
        ors_client.overQueryLimit.connect(lambda: feedback.reportError("OverQueryLimit: Retrying..."))
        return ors_client

    # noinspection PyUnusedLocal
    def initAlgorithm(self, configuration):
        """
        Combines default and algorithm parameters and adds them in order to the
        algorithm dialog window.
        """
        parameters = [self.provider_parameter()] + self.PARAMETERS + [self.output_parameter()]
        for param in parameters:
            self.addParameter(
                param
            )
