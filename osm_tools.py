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
 (http://openrouteservice.readthedocs.io/en/1.0/api.html), developed and 
 maintained by GIScience team at University of Heidelberg, Germany. By using 
 this plugin you agree to the ORS terms of service
 (http://openrouteservice.readthedocs.io/en/1.0/tos.html#terms-of-service).
 
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt5.QtCore import QSettings, QTranslator, QCoreApplication
from PyQt5.Qt import PYQT_VERSION_STR
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QApplication
import os.path

# Initialize Qt resources from file resources.py
#from ORStools import resources_rc, osm_tools_gui
# Import the code for the dialog
from ORStools.osm_tools_dialog import OSMtoolsDialog
from ORStools import isochrones, osm_tools_client, directions

from qgis.core import *
import qgis.gui
import qgis.utils

import logging

logging.basicConfig(format='%(levelname)s:%(message)s', level = logging.INFO)

class OSMtools():
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInt
    self.dlg.close()
#            self.unload()erface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'OSMtools_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if PYQT_VERSION_STR > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        self.toolbar = self.iface.addToolBar(u'OSMtools')
        self.toolbar.setObjectName(u'OSMtools')
        
        #custom __init__ declarations
        self.dlg = OSMtoolsDialog(self.iface)
        
        self.canvas = qgis.utils.iface.mapCanvas()
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
                
        
    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('OSMtools', message)

    
    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = os.path.join(os.path.dirname(__file__),'icon.png')
        self.action = QAction(QIcon(icon_path),
                            self.tr(u'OSM Tools'), # tr text
                            self.iface.mainWindow() # parent
                            )
        self.iface.addPluginToMenu(u'&OSM Tools',
                                    self.action)
        self.iface.addToolBarIcon(self.action)
        self.action.triggered.connect(self.run)
        
        
        
#        
#        self.dlg.api_key.textChanged.connect(self.keyWriter)
#        
#        self.dlg.key_order.setText("<a href = 'https://go.openrouteservice.org/sign-up/'>Get Key!</a>")     
#        self.dlg.key_order.linkActivated.connect(self.OpenURL) 
#        self.dlg.header_2.linkActivated.connect(self.OpenURL)
#        self.dlg.header_3.linkActivated.connect(self.OpenURL)
        
#        
#    def OpenURL(self, URL): 
#          QDesktopServices().openUrl(QUrl(URL))
#                
#    
            
    def unload(self):        
#        self.dlg.close()
        QApplication.restoreOverrideCursor()
        self.iface.removePluginWebMenu(u"&OSM Tools", self.action)
        self.iface.removeToolBarIcon(self.action)
        del self.toolbar
        
        
    def run(self):
        """Run method that performs all the real work"""
#        
#        # Populate the api key lineEdit widget
#        with open(os.path.join(self.script_dir, "apikey.txt")) as key:
#            self.dlg.api_key.setText(key.read())
#            
#        # Initiate analysis classes
#        self.access_anal = osm_tools_access.accessAnalysis(self.dlg)
#        self.route_anal = osm_too
        
#    def resizeEvent(self, event):
#        pixmap1 = QPixmap(os.path.join(self.script_dir, "openrouteservice.png"))
#        self.pixmap = pixmap1.scaled(self.width(), self.height(),
#                                    aspectRatioMode=Qt.KeepAspectRatio,
#                                    transformMode=Qt.SmoothTransformation
#                                    )
#        self.header_pic.setPixmap(self.pixmap)ls_routing.routing(self.dlg)
#        
#        self.dlg.setFixedSize(self.dlg.size())
        
        
        self.dlg.show()
        
        self.dlg._layerTreeChanged()
        # show the dialog
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            client = osm_tools_client.Client()
            if self.dlg.tabWidget.currentIndex() == 1:
                iso = isochrones.isochrones(self.dlg, client, self.iface)
                iso.main()
            if self.dlg.tabWidget.currentIndex() == 0:
                route = directions.directions(self.dlg, client, self.iface)
                route.directions()
#            self.dlg.close()
#            if self.dlg.tabWidget.currentIndex() == 1 and self.dlg.use_layer.isChecked():
#                self.access_anal.iterAnalysis()
#            
#            elif self.dlg.tabWidget.currentIndex() == 0:
#                self.route_anal.route()
#        else:
#            self.unload()
                 
#    def keyWriter(self):
#        with open(os.path.join(self.script_dir, "apikey.txt"), 'w') as key:
#            return key.write(self.dlg.api_key.text())