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

import os.path

from PyQt5.QtWidgets import (QAction,
                             QDialog,
                             QApplication,
                             QComboBox,
                             QPushButton)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
from qgis.core import (QgsProject,
                       QgsLayerTreeLayer,
                       QgsMapLayer,
                       QgsWkbTypes
                       )

from OSMtools import ICON_DIR, PLUGIN_NAME
from OSMtools.utils import exceptions, configmanager, pointtool
from OSMtools.core import (client,
                           directions,
                           isochrones,
                           matrix,
                           geocode,
                           PROFILES,
                           PREFERENCES,
                           UNITS)
from .OSMtoolsDialogUI import Ui_OSMtoolsDialogBase


class OSMtoolsDialogMain:
    """Defines all mandatory QGIS things about dialog."""

    def __init__(self, iface):
        """

        :param iface: the current QGIS interface
        :type iface: Qgis.Interface
        """
        self._iface = iface
        self.dlg = OSMtoolsDialog(self._iface)

    def initGui(self):
        self.action = QAction(QIcon(os.path.join(ICON_DIR, 'osmtools.png')),
                              PLUGIN_NAME,  # tr text
                              self._iface.mainWindow()  # parent
                              )

        self._iface.addPluginToMenu(PLUGIN_NAME,
                                    self.action)
        self._iface.addToolBarIcon(self.action)
        self.action.triggered.connect(self.run)

    def unload(self):
        try:
            QApplication.restoreOverrideCursor()
            self._iface.removePluginMenu(PLUGIN_NAME, self.action)
            self._iface.removeToolBarIcon(self.action)
        except:
            pass

    def run(self):
        self.dlg.show()
        result = self.dlg.exec_()
        if result:
            try:
                clnt = client.Client(self._iface)

                if self.dlg.tabWidget.currentIndex() == 2:
                    pass
                    m = matrix.matrix(self.dlg, clnt, self._iface)
                    m.matrix_calc()
                if self.dlg.tabWidget.currentIndex() == 1:
                    pass
                    iso = isochrones.isochrones(self.dlg, clnt, self._iface)
                    iso.isochrones_calc()
                if self.dlg.tabWidget.currentIndex() == 0:
                    pass
                    route = directions.directions(self.dlg, clnt, self._iface)
                    route.directions_calc()
            except exceptions.Timeout:
                self._iface.messageBar().pushCritical('Time out',
                                                      'The connection exceeded the '
                                                      'timeout limit of 60 seconds')

            except (exceptions.OverQueryLimit,
                    exceptions.ApiError,
                    exceptions.TransportError,
                    exceptions.OverQueryLimit) as e:
                self._iface.messageBar().pushCritical("{}: ".format(type(e)),
                                                      "{}".format(str(e)))

            except Exception:
                raise
            finally:
                self.dlg.close()


class OSMtoolsDialog(QDialog, Ui_OSMtoolsDialogBase):
    """Define the custom behaviour of Dialog"""

    def __init__(self, iface, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self._iface = iface
        self.project = QgsProject.instance()  # invoke a QgsProject instance

        # Programmtically invoke ORS logo
        header_pic = QPixmap(os.path.join(ICON_DIR, "openrouteservice.png"))
        pixmap = header_pic.scaled(150, 50,
                                   aspectRatioMode=Qt.KeepAspectRatio,
                                   transformMode=Qt.SmoothTransformation
                                   )
        self.header_pic.setPixmap(pixmap)

        # Read API key file
        self.key_text.setText(configmanager.read()['api_key'])
        self.api_key = self.key_text.text()

        #### Set up signals/slots ####

        # API key text line
        self.key_text.textChanged.connect(self._keyWriter)

        # Matrix tab
        self.matrix_start_combo.currentIndexChanged.connect(self._layerSelectedChanged)
        self.matrix_end_combo.currentIndexChanged.connect(self._layerSelectedChanged)
        self.matrix_start_refresh.clicked.connect(self._layerTreeChanged)
        self.matrix_end_refresh.clicked.connect(self._layerTreeChanged)

        # Isochrone tab
        self.iso_location_button.clicked.connect(self._initMapTool)
        self.iso_unit_combo.currentIndexChanged.connect(self._unitChanged)
        self.iso_layer_check.stateChanged.connect(self._accessLayerChanged)
        self.iso_layer_refresh.clicked.connect(self._layerTreeChanged)

        # Routing tab
        self.routing_start_frommap_button.clicked.connect(self._initMapTool)
        self.routing_via_map_button.clicked.connect(self._initMapTool)
        self.routing_end_frommap_button.clicked.connect(self._initMapTool)
        self.start_buttongroup.buttonReleased[int].connect(self._mappingMethodChanged)
        self.end_buttongroup.buttonReleased[int].connect(self._mappingMethodChanged)
        self.routing_via_clear_button.clicked.connect(self._clearVia)
        self.project.layerWasAdded.connect(self._layerTreeChanged)
        self.project.layersRemoved.connect(self._layerTreeChanged)
        self.routing_start_fromlayer_refresh.clicked.connect(self._layerTreeChanged)
        self.routing_end_fromlayer_refresh.clicked.connect(self._layerTreeChanged)
        self.routing_start_fromlayer_combo.currentIndexChanged[int].connect(self._layerSelectedChanged)
        self.routing_end_fromlayer_combo.currentIndexChanged[int].connect(self._layerSelectedChanged)

        # Populate combo boxes
        self.routing_travel_combo.addItems(PROFILES)
        self.iso_travel_combo.addItems(PROFILES)
        self.matrix_travel_combo.addItems(PROFILES)
        self.routing_preference_combo.addItems(PREFERENCES)
        self.iso_unit_combo.addItems(UNITS)
        self._layerTreeChanged()

    def _accessLayerChanged(self):
        for child in self.sender().parentWidget().children():
            if not child.objectName() == self.sender().objectName():
                child.setEnabled(self.sender().isChecked())

    def _layerTreeChanged(self):
        """
        Re-populate layers for dropdowns dynamically when layers were 
        added/removed.
        """

        # First get all point layers in map canvas
        layer_names = []
        root = self.project.layerTreeRoot()
        for child in root.children():
            if isinstance(child, QgsLayerTreeLayer):
                layer = child.layer()
                # Handle weird project startup behaviour of QGIS (apparently 
                # doesn't find layers on project startup and throws AttributeError)
                try:
                    if layer.type() == QgsMapLayer.VectorLayer and layer.wkbType() == QgsWkbTypes.Type(1):
                        layer_names.append(layer.name())
                except AttributeError:
                    continue

        comboboxes = [self.routing_start_fromlayer_combo,
                      self.routing_end_fromlayer_combo,
                      self.iso_layer_combo,
                      self.matrix_start_combo,
                      self.matrix_end_combo]

        for box in comboboxes:
            old_text = box.currentText()
            box.clear()
            for layer in layer_names:
                box.addItem(layer)
            # Make sure the old layer is still shown when this slot is triggered
            new_text_id = box.findText(old_text)
            box.setCurrentIndex(0) if new_text_id == -1 else box.setCurrentIndex(new_text_id)
            # box.setCurrentIndex(new_text_id)

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

        condition = self.routing_start_fromlayer_radio.isChecked() and self.routing_end_fromlayer_radio.isChecked()
        self.routing_twolayer_rowbyrow.setEnabled(condition)
        self.routing_twolayer_allbyall.setEnabled(condition)

    def _layerSelectedChanged(self, index):
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
            layer_selected = \
            [lyr for lyr in self.project.mapLayers().values() if lyr.name() == sending_widget.currentText()][0]
            for widget in parent_widget.findChildren(QComboBox):
                if widget.objectName() != sending_widget_name:
                    old_text = widget.currentText()
                    widget.clear()
                    widget.addItems([field.name() for field in layer_selected.fields()])
                    new_text_id = widget.findText(old_text)
                    widget.setCurrentIndex(0) if new_text_id == -1 else widget.setCurrentIndex(new_text_id)

    def _clearVia(self):
        """
        Clears the 'via' coordinates label.
        """
        self.routing_via_label.setText("Long,Lat")

    def _keyWriter(self):
        """
        Writes key to text file when api key text field changes.
        """
        configmanager.write('api_key',
                            self.key_text.text())

    def _unitChanged(self):
        """
        Connector to change unit label text when changing unit
        """
        if self.iso_unit_combo.currentText() == 'time':
            self.iso_unit_label.setText('mins')
            self.iso_range_unit_label.setText('mins')
        else:
            self.iso_unit_label.setText('m')
            self.iso_range_unit_label.setText('m')

    def _initMapTool(self):
        """
        Initialize the mapTool to select coordinates in map canvas.
        """

        self.showMinimized()
        sending_button = self.sender().objectName()
        self.mapTool = pointtool.PointTool(self._iface.mapCanvas(), sending_button)
        self._iface.mapCanvas().setMapTool(self.mapTool)
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

        if button == self.routing_start_frommap_button.objectName():
            self.routing_start_frommap_label.setText("{0:.5f},{1:.5f}".format(x, y))

        if button == self.routing_end_frommap_button.objectName():
            self.routing_end_frommap_label.setText("{0:.5f},{1:.5f}".format(x, y))

        if button == self.routing_via_map_button.objectName():
            self.routing_via_label.setText("{0:.5f},{1:.5f}".format(x, y))

        if button == self.iso_location_button.objectName():
            clt = client.Client(self._iface)
            loc_dict = geocode.reverse_geocode(clt,
                                               point)

            out_str = u"{0:.6f}\n{1:.6f}\n{2}\n{3}\n{4}".format(loc_dict.get('Lon', ""),
                                                                loc_dict.get('Lat', ""),
                                                                loc_dict.get('CITY', "NA"),
                                                                loc_dict.get('STATE', "NA"),
                                                                loc_dict.get('COUNTRY', "NA")
                                                                )
            self.iso_location_label.setText(out_str)

        QApplication.restoreOverrideCursor()
        self.mapTool.canvasClicked.disconnect()
        self._iface.mapCanvas().unsetMapTool(self.mapTool)
        if self.windowState() == Qt.WindowMinimized:
            # Window is minimised. Restore it.
            self.setWindowState(Qt.WindowMaximized)
            self.activateWindow()