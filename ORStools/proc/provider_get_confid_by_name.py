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

from qgis.PyQt.QtCore import QCoreApplication

from qgis.core import (
    QgsSettings,
    QgsProcessingAlgorithm,
    QgsProcessingParameterString,
    QgsProcessingContext,
    QgsProcessingFeedback,
)

from ORStools.utils import logger


class ORSProviderGetConfIdAlgo(QgsProcessingAlgorithm):
    def __init__(self):
        super().__init__()
        self.PARAMETERS: list = [
            QgsProcessingParameterString(
                name="ors_provider_name",
                description=self.tr("Specify unique name for your ors provider"),
            ),
        ]

    def group(self):
        return "Configuration"

    def groupId(self):
        return "configuration"

    def initAlgorithm(self, config={}):
        for parameter in self.PARAMETERS:
            self.addParameter(parameter)

    def processAlgorithm(
        self, parameters: dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, str]:
        s = QgsSettings()
        provider_name = self.parameterAsString(parameters, "ors_provider_name", context)
        current_config = s.value("ORStools/config")

        msg = self.tr(f"Config with specified name not found! - {provider_name}")
        result = -1

        if provider_name in [x["name"] for x in current_config["providers"]]:
            found = [
                int(j)
                for j, y in {str(i): x for i, x in enumerate(current_config["providers"])}.items()
                if y["name"] == provider_name
            ]
            if len(found) > 0:
                result = found[0]
                msg = self.tr(f"The provider with name: {provider_name} has the ID {str(result)}")

        feedback.pushInfo(msg)
        feedback.pushInfo(f"This is the full list of providers: {current_config["providers"]}")
        logger.log(msg, 2)
        return {"OUTPUT": result}

    def createInstance(self):
        return self.__class__()

    def name(self):
        return "config_get_provider_id_by_name"

    def displayName(self) -> str:
        """
        Algorithm name shown in QGIS toolbox
        :return:
        """
        return self.tr("Get Provider Config ID via Algorithm (e.g. headless)")

    def tr(self, string: str, context=None) -> str:
        context = context or self.__class__.__name__
        return QCoreApplication.translate(context, string)
