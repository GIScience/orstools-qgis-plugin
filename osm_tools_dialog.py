# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ORStoolsDialog
                                 A QGIS plugin
 falk
                             -------------------
        begin                : 2017-02-01
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Nils Nolde
        email                : nils.nolde@gmail.com
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

import os.path

from PyQt5.uic import loadUiType
from PyQt5.QtWidgets import (QDialog, 
                             QApplication,
                             QComboBox,
                             QPushButton,                     
                             )
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from qgis.core import (QgsGeometry, 
                       QgsProject, 
                       QgsLayerTreeLayer, 
                       QgsMapLayer,
                       QgsWkbTypes
                       )

from . import osm_tools_pointtool, osm_tools_geocode, osm_tools_aux

FORM_CLASS, _ = loadUiType(os.path.join(
    os.path.dirname(__file__), 'osm_tools_dialog_base.ui'))

profiles = [
        'driving-car',
        'driving-hgv',
        'cycling-regular',
        'cycling-road',
        'cycling-safe',
        'cycling-mountain',
        'cycling-tour',
        'foot-walking',
        'foot-hiking',
        ]

preferences = ['fastest', 'shortest']

units = ['time', 'distance']

class OSMtoolsDialog(QDialog, FORM_CLASS):
    def __init__(self, iface):
        """Constructor."""
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.htmllayerTreeRoot
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.iface = iface
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Read API key file
        self.api_key_dlg.setText(osm_tools_aux.readConfig()['api_key'])
            
        self.api_key = self.api_key_dlg.text()
        self.project = QgsProject.instance()
        
        self.route_mode_combo.addItems(profiles)
        self.access_mode_combo.addItems(profiles)
        self.route_pref_combo.addItems(preferences)
        self.access_unit_combo.addItems(units)
        
        #### Set up signals/slots ####
        
        # API key text line
        self.api_key_dlg.textChanged.connect(self._keyWriter)
        
        # Isochrone tab
        self.access_map_button.clicked.connect(self._initMapTool)
        self.access_unit_combo.currentIndexChanged.connect(self._unitChanged)
        self.access_layer_check.stateChanged.connect(self._accessLayerChanged)
        self.access_layer_refresh.clicked.connect(self._layerTreeChanged) 
        
        # Routing tab
        self.start_map_button.clicked.connect(self._initMapTool)
        self.via_map_button.clicked.connect(self._initMapTool)
        self.end_map_button.clicked.connect(self._initMapTool)
        self.start_buttongroup.buttonReleased[int].connect(self._mappingMethodChanged)
        self.end_buttongroup.buttonReleased[int].connect(self._mappingMethodChanged)
        self.via_clear_button.clicked.connect(self._clearVia)
        self.project.layerWasAdded.connect(self._layerTreeChanged)
        self.project.layersRemoved.connect(self._layerTreeChanged) 
        self.start_layer_refresh.clicked.connect(self._layerTreeChanged) 
        self.end_layer_refresh.clicked.connect(self._layerTreeChanged) 
        self.start_layer_combo.currentIndexChanged[int].connect(self._layerSeletedChanged)
        self.end_layer_combo.currentIndexChanged[int].connect(self._layerSeletedChanged)
        
        # Programmtically invoke ORS logo
        header_pic = QPixmap(os.path.join(self.script_dir, "openrouteservice.png"))
        self.pixmap = header_pic.scaled(150, 50,
                                        aspectRatioMode=Qt.KeepAspectRatio,
                                        transformMode=Qt.SmoothTransformation
                                        )
        self.header_pic.setPixmap(self.pixmap)
        self.header_text.setAlignment(Qt.AlignHCenter)
        self.header_subpic.setAlignment(Qt.AlignHCenter)
        

    def _accessLayerChanged(self):
        for child in self.sender().parentWidget().children():  
            if not child.objectName() == self.sender().objectName():
                child.setEnabled(self.sender().isChecked())
            
    
    def _layerTreeChanged(self):
        """
        Re-populate layers for dropdowns dynamically when layers were 
        added/removed.
        """
        start_layer_id = self.start_layer_combo.currentIndex()
        end_layer_id = self.end_layer_combo.currentIndex()
        access_layer_id = self.access_layer_combo.currentIndex()
        self.start_layer_combo.clear()
        self.end_layer_combo.clear()
        self.access_layer_combo.clear()
        root = self.project.layerTreeRoot()
        for child in root.children():
            if isinstance(child, QgsLayerTreeLayer):
                layer = child.layer()
                if layer.type() == QgsMapLayer.VectorLayer and layer.wkbType() == QgsWkbTypes.Type(1):
                    self.start_layer_combo.addItem(layer.name())
                    self.end_layer_combo.addItem(layer.name())
                    self.access_layer_combo.addItem(layer.name())
        self.start_layer_combo.setCurrentIndex(start_layer_id)
        self.end_layer_combo.setCurrentIndex(end_layer_id)
        self.access_layer_combo.setCurrentIndex(access_layer_id)
                    
                    
    def _mappingMethodChanged(self, index):
        """ Generic method to enable/disable all comboboxes and buttons in the
        children of the parent widget of the calling radio button. 
        
        :param index: Index of the calling radio button within the QButtonGroup.
        :type index: int
        """
        parent_widget = self.sender().button(index).parentWidget()
        parent_widget_name = parent_widget.objectName()
        grandparent_widget = parent_widget.parentWidget()
        
        for parent in grandparent_widget.children():
            if parent.objectName() == parent_widget_name:
                for child in parent.findChildren((QComboBox, QPushButton)):
                    child.setEnabled(True)
            else: 
                for child in parent.findChildren((QComboBox, QPushButton)):
                    child.setEnabled(False)
        
        condition = self.end_layer_radio.isChecked() and self.start_layer_radio.isChecked()
        self.row_by_row.setEnabled(condition)
        self.many_by_many.setEnabled(condition)
        
        
    def _layerSeletedChanged(self, index):
        """
        Populates dropdowns with QgsProject layers.
        
        :param index: Index of previously selected layer in dropdown. -1 if no
            layer was selected.
        :type index: int
        """
        
        if index != -1:
            sending_widget = self.sender()
            sending_widget_name = sending_widget.objectName()
            parent_widget = self.sender().parentWidget()
            layer_selected = [lyr for lyr in self.project.mapLayers().values() if lyr.name() == sending_widget.currentText()][0]
            for widget in parent_widget.findChildren(QComboBox):
                if widget.objectName() != sending_widget_name:   
                    widget.clear()
                    widget.addItems([field.name() for field in layer_selected.fields()])
                
    
    def _clearVia(self):
        """
        Clears the 'via' coordinates label.
        """
        self.via_label.setText("Long,Lat")
            
            
    def _keyWriter(self):
        """
        Writes key to text file when api key text field changes.
        """
        osm_tools_aux.writeConfig('api_key',
                                  self.api_key_dlg.text())
           
            
    def _unitChanged(self):
        """
        Connector to change unit label text when changing unit
        """
        if self.access_unit_combo.currentText() == 'time':
            self.unit_label.setText('mins')
        else:
            self.unit_label.setText('km')


    def _initMapTool(self):
        """
        Initialize the mapTool to select coordinates in map canvas.
        """
        
        self.setWindowState(Qt.WindowMinimized)
        sending_button = self.sender().objectName()
        self.mapTool = osm_tools_pointtool.PointTool(self.iface.mapCanvas(), sending_button)        
        self.iface.mapCanvas().setMapTool(self.mapTool)
        self.mapTool.canvasClicked.connect(self._writeCoordinateLabel)
        
        
    # Write map coordinates to text fields
    def _writeCoordinateLabel(self, point, button):
        """
        Writes the selected coordinates from map canvas to its accompanying label.
        
        :param point: Point selected with mapTool.
        :type point: QgsPointXY
        
        :param button: Button name which intialized mapTool.
        :param button: str
        """
        
        x, y = point
        
        if button == self.start_map_button.objectName():
            self.start_map_label.setText("{0:.5f},{1:.5f}".format(x, y))
            
        if button == self.end_map_button.objectName():
            self.end_map_label.setText("{0:.5f},{1:.5f}".format(x, y))
            
        if button == self.via_map_button.objectName():
            self.via_label.setText("{0:.5f},{1:.5f}".format(x, y))
            
        if button == self.access_map_button.objectName():            
            point_geometry = QgsGeometry.fromPointXY(point)
            loc_dict = osm_tools_geocode.reverseGeocode(point_geometry,
                                                        self.api_key_dlg.text())
            
            out_str = u"{0:.6f}\n{1:.6f}\n{2}\n{3}\n{4}".format(loc_dict.get('Lon', ""),
                                                            loc_dict.get('Lat', ""),
                                                            loc_dict.get('CITY', "NA"),
                                                            loc_dict.get('STATE', "NA"),
                                                            loc_dict.get('COUNTRY', "NA")
                                                            )
            self.access_map_label.setText(out_str)
        
        # Restore normal behavior
        self.showNormal()
        QApplication.restoreOverrideCursor()
        self.mapTool.canvasClicked.disconnect()
        