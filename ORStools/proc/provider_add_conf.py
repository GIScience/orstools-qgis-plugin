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
    QgsProcessingParameterNumber,
    QgsProcessingParameterBoolean,
    QgsProcessingContext,
    QgsProcessingFeedback,
)

from ORStools.utils import logger
from ..proc import ENDPOINTS


class ORSProviderAddAlgo(QgsProcessingAlgorithm):
    def __init__(self):
        super().__init__()
        self.PARAMETERS: list = [
            QgsProcessingParameterString(
                name="ors_provider_name",
                description=self.tr("Set unique name for your ors provider"),
            ),
            QgsProcessingParameterString(
                name="ors_provider_api_key",
                description=self.tr("Set api key for your ors provider"),
                optional=True,
            ),
            QgsProcessingParameterString(
                name="ors_provider_url",
                description=self.tr("Set url to ors api"),
            ),
            QgsProcessingParameterNumber(
                name="ors_provider_timeout",
                description=self.tr("Set custom timeout (in seconds)"),
                defaultValue=60,
            ),
            QgsProcessingParameterBoolean(
                name="ors_provider_overwrite",
                description=self.tr("If True, existing provider is overwritten"),
                defaultValue=False,
            ),
            # TODO: Service Endpoints
            # QgsProcessingParameterString(
            #     name="otp_endpoint_directions",
            #     description=self.tr("Endpoint for directions on your provider"),
            #     defaultValue="directions",
            #     optional=True
            # ),
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
        provider_url = self.parameterAsString(parameters, "ors_provider_url", context)
        provider_api_key = self.parameterAsString(parameters, "ors_provider_api_key", context)
        provider_timeout = self.parameterAsInt(parameters, "ors_provider_timeout", context)
        provider_overwrite = self.parameterAsBoolean(parameters, "ors_provider_timeout", context)

        current_config = s.value("ORStools/config")
        feedback.pushInfo(str(ENDPOINTS))
        logger.log(str(ENDPOINTS), 2)
        if provider_name in [x["name"] for x in current_config["providers"]]:
            if provider_overwrite:
                msg = f"A provider with the name '{provider_name}' already exists. Replacement not yet implemented."
            else:
                # ignoring reset of settings for now.
                msg = f"A provider with the name '{provider_name}' already exists. Please mark overwrite checkbox."
            feedback.pushInfo(msg)
            logger.log(msg, 2)
            return {"OUTPUT": msg}
        else:
            existing_config = s.value("ORStools/config")
            s.setValue(
                "ORStools/config",
                {
                    "providers": existing_config["providers"]
                    + [
                        {
                            "base_url": provider_url,
                            "key": provider_api_key,
                            "name": provider_name,
                            "timeout": provider_timeout,
                            "endpoints": ENDPOINTS,  # TODO: customize"new config added: "
                        }
                    ]
                },
            )
            s.sync()  # this gives no feedback whatsover, so checking manually is necessary:
            try:
                with open(s.fileName(), "a"):
                    pass
                msg = f"config has been added: {provider_name}"
            except IOError as e:
                msg = f"config couldn't be added: {e} | {s.fileName()}"

            return {
                "OUTPUT": msg,
                "CONFIG": s.value("ORStools/config", {"providers": []})["providers"],
            }

    def createInstance(self):
        return self.__class__()

    def name(self):
        return "config_add_provider"

    def displayName(self) -> str:
        """
        Algorithm name shown in QGIS toolbox
        :return:
        """
        return self.tr("Set Provider Config via Algorithm (e.g. headless)")

    def tr(self, string: str, context=None) -> str:
        context = context or self.__class__.__name__
        return QCoreApplication.translate(context, string)
        # return string #disabling QCoreApplication.translate due to Qt

    def flags(self):
        return (
            super().flags() | QgsProcessingAlgorithm.FlagHideFromToolbox
        )  # prior 3.36 but seems to work in 3.42, too
