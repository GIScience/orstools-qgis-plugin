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
from PyQt4.QtCore import *
from PyQt4.QtGui import *
# Initialize Qt resources from file resources.py
import resources_rc
# Import the code for the dialog
from osm_tools_dialog import OSMtoolsDialog
import os.path

import osm_tools_access
import osm_tools_routing

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
        :type iface: QgsInterface
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

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&OSM Tools')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'OSMtools')
        self.toolbar.setObjectName(u'OSMtools')
        
        #custom __init__ declarations
        self.dlg = OSMtoolsDialog()
        
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


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)
            
        return action
    
    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/OSMtools/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'OSM Tools'),
            callback=self.run,
            parent=self.iface.mainWindow())
        
        self.dlg.api_key.textChanged.connect(self.keyWriter)
        
        self.dlg.key_order.setText("<a href = 'https://developers.openrouteservice.org/portal/apis/'>Get Key!</a>") 
        self.dlg.key_order.connect(self.dlg.key_order, SIGNAL("linkActivated(QString)"), self.OpenURL) 
        self.dlg.header_2.linkActivated.connect(self.OpenURL)
        self.dlg.header_3.linkActivated.connect(self.OpenURL)
        
        
    def OpenURL(self, URL): 
          QDesktopServices().openUrl(QUrl(URL))
                
    
    def unload(self):        
        self.dlg.close()
        QApplication.restoreOverrideCursor()
        
        
    def run(self):
        """Run method that performs all the real work"""
        
        # Populate the api key lineEdit widget
        with open(os.path.join(self.script_dir, "apikey.txt")) as key:
            self.dlg.api_key.setText(key.read())
        
        # Initiate analysis classes
        self.access_anal = osm_tools_access.accessAnalysis(self.dlg)
        self.route_anal = osm_tools_routing.routing(self.dlg)
        
        self.dlg.setFixedSize(self.dlg.size())
        
        self.dlg.show()
        
        # show the dialog
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            if self.dlg.tabWidget.currentIndex() == 1 and self.dlg.use_layer.isChecked():
                self.access_anal.iterAnalysis()
            
            elif self.dlg.tabWidget.currentIndex() == 0:
                self.route_anal.route()
        else:
            self.unload()
                
    def keyWriter(self):
        with open(os.path.join(self.script_dir, "apikey.txt"), 'w') as key:
            return key.write(self.dlg.api_key.text())