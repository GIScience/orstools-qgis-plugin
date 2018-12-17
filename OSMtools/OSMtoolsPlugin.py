# -*- coding: utf-8 -*-
"""
/***************************************************************************
 OSMtools
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

from PyQt5.QtWidgets import QMessageBox

import pyplugin_installer

from .gui import OSMtoolsDialog


class OSMtools():
    """QGIS Plugin Implementation."""
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        self.dialog = OSMtoolsDialog.OSMtoolsDialogMain(iface)
        QMessageBox.warning(iface.mainWindow(), "OSM Tools uninstalled", "OSM Tools is deprecated.\n\nORS Tools will be installed instead (Web menu & Web toolbar.")
        self.uninstall()

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        self.dialog.initGui()
        
    def unload(self):
        self.dialog.unload()

    def uninstall(self):
        self.unload()
        pyplugin_installer.instance().uninstallPlugin('OSMtools', quiet=True)
        # pyplugin_installer.instance().installPlugin('ORStools', quiet=False)
        pyplugin_installer.instance().installFromZipFile('/home/nilsnolde/dev/python/ORStools/dist/OSMtools_v0.99-dev.zip')