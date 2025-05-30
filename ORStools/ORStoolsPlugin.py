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

from qgis.gui import QgisInterface
from qgis.core import QgsApplication, QgsSettings
from qgis.PyQt.QtCore import QTranslator, qVersion, QCoreApplication, QLocale
import os.path

from .gui import ORStoolsDialog
from .proc import provider, ENDPOINTS, DEFAULT_SETTINGS


class ORStools:
    """QGIS Plugin Implementation."""

    # noinspection PyTypeChecker,PyArgumentList,PyCallByClass

    def __init__(self, iface: QgisInterface) -> None:
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        self.dialog = ORStoolsDialog.ORStoolsDialogMain(iface)
        self.provider = provider.ORStoolsProvider()

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        try:
            locale = QgsSettings().value("locale/userLocale")
            if not locale:
                locale = QLocale().name()
            locale = locale[0:2]

            locale_path = os.path.join(self.plugin_dir, "i18n", "orstools_{}.qm".format(locale))

            if os.path.exists(locale_path):
                self.translator = QTranslator()
                self.translator.load(locale_path)

                if qVersion() > "4.3.3":
                    QCoreApplication.installTranslator(self.translator)
        except TypeError:
            pass

        self.add_default_provider_to_settings()

    def initGui(self) -> None:
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        QgsApplication.processingRegistry().addProvider(self.provider)
        self.dialog.initGui()

    def unload(self) -> None:
        """remove menu entry and toolbar icons"""
        QgsApplication.processingRegistry().removeProvider(self.provider)
        self.dialog.unload()

    def add_default_provider_to_settings(self):
        s = QgsSettings()
        settings = s.value("ORStools/config")

        settings_keys = ["ENV_VARS", "base_url", "key", "name", "endpoints"]

        # Add any new settings here for backwards compatibility
        if settings:
            changed = False
            for i, prov in enumerate(settings["providers"]):
                if any([i not in prov for i in settings_keys]):
                    changed = True
                    # Add here, like the endpoints
                    prov["endpoints"] = ENDPOINTS
                    settings["providers"][i] = prov
            if changed:
                s.setValue("ORStools/config", settings)
        else:
            s.setValue("ORStools/config", DEFAULT_SETTINGS)
