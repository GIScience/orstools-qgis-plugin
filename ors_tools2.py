# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ORStools
                                 A QGIS plugin
 falk
                              -------------------
        begin                : 2017-02-01
        git sha              : $Format:%H$
        copyright            : (C) 2017 by nils
        email                : nils
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QVariant, QObject, SIGNAL, QEvent, Qt, pyqtSignal
from PyQt4.QtGui import QAction, QIcon, QMessageBox, QProgressBar, QComboBox, QDesktopServices
from PyQt4 import QtCore, QtGui
# Initialize Qt resources from file resources.py
import resources_rc
# Import the code for the dialog
from ors_tools_dialog import ORStoolsDialog
import os.path

import ors_tools_pointtool
import ors_tools_access

from qgis.core import *
import qgis.gui
from qgis.gui import QgsMapTool
import qgis.utils
import processing

from collections import OrderedDict
from datetime import datetime
import logging
import numpy as np

logging.basicConfig(format='%(levelname)s:%(message)s', level = logging.INFO)

class ORStools:
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
            'ORStools_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        
        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&ORS Tools')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'ORStools')
        self.toolbar.setObjectName(u'ORStools')
        
        #custom __init__ declarations
        self.dlg = ORStoolsDialog()
        
        self.canvas = qgis.utils.iface.mapCanvas()
        self.mapTool = None
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
        return QCoreApplication.translate('ORStools', message)


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

        icon_path = ':/plugins/ORStools/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Gimme'),
            callback=self.run,
            parent=self.iface.mainWindow())
        
        # Populate the api key lineEdit widget
        with open(os.path.join(self.script_dir, "apikey.txt")) as key:
            self.dlg.api_key.setText(key.read())
        
        # Set up all event connections
        # Populate field ID dynamically when combobox selection changes
        self.dlg.layer.currentIndexChanged.connect(self.popBox)
        self.dlg.check_dissolve.stateChanged.connect(self.popBox)
        self.dlg.access_map.clicked.connect(self.initMapTool)
        self.dlg.api_key.textChanged.connect(self.keyWriter)
        
        self.dlg.key_order.setText("<a href = 'mailto:timothy.ellersiek@geog.uni-heidelberg.de?subject=ORS API key request'>Get Key!</a>") 
        self.dlg.key_order.connect(self.dlg.key_order, SIGNAL("linkActivated(QString)"), self.OpenURL) 
        
        
    def OpenURL(self, URL): 
          QDesktopServices().openUrl(QtCore.QUrl(URL))
                
    
    def unload(self):        
        if self.mapTool != None:
            self.mapTool.canvasClicked.disconnect()
            self.canvas.unsetMapTool(self.mapTool) 
        
    
    # Connect to PointTool and set as mapTool
    def initMapTool(self):
        self.mapTool = ors_tools_pointtool.PointTool(self.canvas)        
        self.iface.mapCanvas().setMapTool(self.mapTool)     
        self.mapTool.canvasClicked.connect(self.getCoords)
        
    
    # Populate field ID
    def popBox(self):
        if self.dlg.check_dissolve.isChecked() == True:
            self.dlg.id_field.setEnabled(True)
            self.dlg.id_field.clear()
            layer_list = [lyr for lyr in QgsMapLayerRegistry.instance().mapLayers().values() if lyr.name() == self.dlg.layer.currentText()]
            if layer_list:
                layer_selected = layer_list[0]
                fields_selected = layer_selected.fields()
                for field in fields_selected:
                    self.dlg.id_field.addItem(field.name())
        else:
            self.dlg.id_field.setEnabled(False)
        return
        
        
    def getCoords(self, point):
        self.access_anal.pointAnalysis(point)
        
        
    def run(self):
        """Run method that performs all the real work"""
        self.dlg.show()
        self.startUp()
        self.dlg.setFixedSize(self.dlg.size())
        self.iface.mapCanvas().setMapTool(self.mapTool)     
        self.access_anal = ors_tools_access.accessAnalysis(self.dlg)
        
        # show the dialog
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            if self.dlg.tabWidget.currentIndex() == 0:
                self.access_anal.iterAnalysis()
        else:
            self.unload()
                
        if self.mapTool != None:
            self.canvas.unsetMapTool(self.mapTool)    
            
        
    def startUp(self):
    
        # Accessibility init
        self.dlg.mode.clear()
        self.dlg.layer.clear()
        self.dlg.method.clear()  
        self.dlg.id_field.clear()
        self.dlg.access_text.clear()
        self.dlg.mode.addItem('Car')
        self.dlg.mode.addItem('Bicycle')
        self.dlg.mode.addItem('Pedestrian')      
        self.dlg.method.addItem('RecursiveGrid')
        self.dlg.method.addItem('TIN')        
        
        # Populate field ID from first layer
        self.popBox()
        
        # Routing init
        self.dlg.add_start.clear()
        self.dlg.add_end.clear()
        self.dlg.add_end.clear()
        self.dlg.mode_travel.clear()
        self.dlg.mode_routing.clear()
        self.dlg.mode_travel.addItem('Car')
        self.dlg.mode_travel.addItem('Bicycle')
        self.dlg.mode_travel.addItem('Pedestrian')
        self.dlg.mode_routing.addItem('Fastest')
        self.dlg.mode_routing.addItem('Shortest')
        
        allLayers = qgis.utils.iface.legendInterface().layers()

        for layer in allLayers:
            layerType = layer.type()
            if layerType == QgsMapLayer.VectorLayer and layer.wkbType() == QGis.WKBPoint:
                self.dlg.layer.addItem(layer.name())

                
    def keyWriter(self):
        with open(os.path.join(self.script_dir, "apikey.txt"), 'w') as key:
            return key.write(self.dlg.api_key.text())
        
        
def CheckCRS(self,crs):
    check = True
    if crs != "EPSG:4326":
        msg = "CRS is {}. Must be EPSG:4326 (WGS84)".format(crs)
        qgis.utils.iface.messageBar().pushMessage(msg, level = qgis.gui.QgsMessageBar.CRITICAL)
        check = False
    return check
    
