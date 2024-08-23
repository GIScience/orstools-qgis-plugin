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

from qgis.core import QgsMessageLog, Qgis

from ORStools import PLUGIN_NAME


def log(message: str, level_in: int = 0):
    """
    Writes to QGIS inbuilt logger accessible through panel.

    :param message: logging message to write, error or URL.
    :type message: str

    :param level_in: integer representation of logging level.
    :type level_in: int
    """
    if level_in == 0:
        level = Qgis.MessageLevel.Info
    elif level_in == 1:
        level = Qgis.MessageLevel.Warning
    elif level_in == 2:
        level = Qgis.MessageLevel.Critical
    else:
        level = Qgis.MessageLevel.Info

    QgsMessageLog.logMessage(message, PLUGIN_NAME.strip(), level)
