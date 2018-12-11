# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ORStools
                                 A QGIS plugin
 QGIS client to query openrouteservice
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

import os
import webbrowser

from PyQt5.QtWidgets import (QAction,
                             QDialog,
                             QApplication,
                             QComboBox,
                             QPushButton,
                             QMenu,
                             QMessageBox)
from PyQt5.QtCore import Qt, QVariant
from PyQt5.QtGui import QPixmap, QIcon
from qgis.core import (QgsProject,
                       QgsMapLayer,
                       QgsWkbTypes,
                       )

from ORStools import ICON_DIR, PLUGIN_NAME, ENV_VARS, ENDPOINTS, DEFAULT_COLOR, __version__, __email__, __web__, __help__
from ORStools.utils import exceptions, pointtool, logger
from ORStools.core import (client,
                           isochrones_core,
                           directions_core,
                           geocode_core,
                           PROFILES,
                           PREFERENCES,
                           DIMENSIONS)
from ORStools.gui import (isochrones_gui,
                          directions_gui)
from .ORStoolsDialogUI import Ui_ORStoolsDialogBase
from .ORStoolsDialogConfig import ORStoolsDialogConfigMain
from .ORStoolsDialogAdvanced import ORStoolsDialogAdvancedMain


def on_config_click(parent):
    """Pop up config window. Outside of classes because it's accessed by both.
    """
    config_dlg = ORStoolsDialogConfigMain(parent=parent)
    config_dlg.exec_()


def on_help_click(self):
    webbrowser.open(__help__)


class ORStoolsDialogMain:
    """Defines all mandatory QGIS things about dialog."""

    def __init__(self, iface):
        """

        :param iface: the current QGIS interface
        :type iface: Qgis.Interface
        """
        self.iface = iface
        self.project = QgsProject.instance()

        self.first_start = True
        # Dialogs
        self.dlg = None
        self.advanced = None
        self.menu = None
        self.actions = None

    def initGui(self):
        def create_icon(f):
            return QIcon(os.path.join(ICON_DIR, f))

        icon_plugin = create_icon('icon_orstools.png')

        self.actions = [
            QAction(
                icon_plugin,
                PLUGIN_NAME,  # tr text
                self.iface.mainWindow()  # parent
            ),
            # Config dialog
            QAction(
                create_icon('icon_settings.svg'),
                'Configuration',
                self.iface.mainWindow()
            ),
            # About dialog
            QAction(
                create_icon('icon_about.png'),
                'About',
                self.iface.mainWindow()
            ),
            # Help page
            QAction(
                create_icon('icon_help.png'),
                'Help',
                self.iface.mainWindow()
            )

        ]

        # Create menu
        self.menu = QMenu(PLUGIN_NAME)
        self.menu.setIcon(icon_plugin)
        self.menu.addActions(self.actions)

        # Add menu to Web menu and icon to toolbar
        self.iface.webMenu().addMenu(self.menu)
        self.iface.addWebToolBarIcon(self.actions[0])

        # Connect slots to events
        self.actions[0].triggered.connect(self.run)
        self.actions[1].triggered.connect(lambda: on_config_click(parent=self.iface.mainWindow()))
        self.actions[3].triggered.connect(on_help_click)
        # Connect other dialogs
        self.actions[2].triggered.connect(self._on_about_click)

    def unload(self):
        self.iface.webMenu().removeAction(self.menu.menuAction())
        self.iface.removeWebToolBarIcon(self.actions[0])
        QApplication.restoreOverrideCursor()
        del self.dlg
        del self.advanced

    def _on_about_click(self):
        info = '<b>ORS Tools</b> provides access to <a href="https://openrouteservice.org" style="color: {0}">openrouteservice</a> routing functionalities.<br><br>' \
               'Author: Nils Nolde<br>' \
               'Email: <a href="mailto:Nils Nolde <{1}>">{1}</a><br>' \
               'Web: <a href="{2}">{2}</a><br>' \
               'Repo: <a href="https://github.com/nilsnolde/ORStools">github.com/nilsnolde/ORStools</a><br>' \
               'Version: {3}'.format(DEFAULT_COLOR, __email__, __web__, __version__)

        QMessageBox.information(
            self.iface.mainWindow(),
            'About {}'.format(PLUGIN_NAME),
            info
        )

    @staticmethod
    def get_quota():
        """Update remaining quota from env variables"""
        # Dirty hack out of laziness.. Prone to errors
        text = []
        for var in sorted(ENV_VARS.keys(), reverse=True):
            text.append(os.environ[var])
        return '/'.join(text)

    def _on_advanced_click(self):
        self.advanced.show()

    def run(self):
        # Only populate GUI if it's the first start of the plugin within the QGIS session
        # If not checked, GUI would be rebuilt every time!
        if self.first_start:
            self.first_start = False
            self.dlg = ORStoolsDialog(self.iface, self.iface.mainWindow())  # setting parent enables modal view
            self.dlg.routing_advanced_button.clicked.connect(self._on_advanced_click)

        # Populate Advanced dialog; makes sure that dialog is re-populated every time plugin starts,
        # but stays alive during one session
        self.advanced = ORStoolsDialogAdvancedMain(parent=self.dlg)
        self.dlg.show()
        result = self.dlg.exec()
        if result:
            layer_out = None
            try:
                clnt = client.Client()

                if self.dlg.tabWidget.currentIndex() == 2:
                    pass

                elif self.dlg.tabWidget.currentIndex() == 1:
                    isochrones = isochrones_core.Isochrones()

                    # Make isochrone request
                    params = isochrones_gui.get_request_parameters(self.dlg)
                    response = clnt.request(ENDPOINTS['isochrones'], params)

                    # Populate layer_out
                    isochrones.set_parameters(
                        layer_name='Isochrones_' + params['locations'],
                        profile=params['profile'],
                        dimension=self.dlg.iso_unit_combo.currentText(),
                        id_field_type=QVariant.Int,
                        id_field_name='ID',
                        factor=60 if params['range_type'] == 'time' else 1,
                    )

                    layer_out = isochrones.get_polygon_layer()
                    for isochrone in isochrones.get_features(response, '0'):
                        layer_out.dataProvider().addFeature(isochrone)
                    layer_out.updateExtents()

                    isochrones.stylePoly(layer_out)

                    self.dlg.progressBar.setValue(100)

                elif self.dlg.tabWidget.currentIndex() == 0:
                    directions = directions_gui.Directions(self.dlg, self.advanced)
                    params = directions.get_basic_paramters()
                    layer_out = directions.get_linestring_layer()

                    # Very ugly way to get the route count
                    route_count = directions.get_route_count()
                    counter = 0

                    for coordinates, values in directions.get_request_features():
                        params['coordinates'] = coordinates

                        response = clnt.request(ENDPOINTS['directions'], params)
                        layer_out.dataProvider().addFeature(directions_core.get_feature(
                            response,
                            params['profile'],
                            params['preference'],
                            directions.avoid,
                            values[0],
                            values[1]
                        ))
                        counter += 1
                        self.dlg.progressBar.setValue(int(counter/route_count) * 100)

                    layer_out.updateExtents()

                # Update quota; handled in client module after successful request
                self.dlg.quota_text.setText(self.get_quota() + ' calls')
            except exceptions.Timeout:
                self.iface.messageBar().pushCritical('Time out',
                                                      'The connection exceeded the '
                                                      'timeout limit of 60 seconds')

            except exceptions.ApiError as e:
                self.iface.messageBar().pushCritical(e.__class__.__name__,
                                                     str(e))
            finally:
                if layer_out.featureCount() > 0:
                    self.project.addMapLayer(layer_out)
                else:
                    QMessageBox.warning(self.iface.mainWindow(),
                                          PLUGIN_NAME,
                                          "No features were generated!")
                self.dlg.progressBar.setValue(0)
                self.dlg.close()


class ORStoolsDialog(QDialog, Ui_ORStoolsDialogBase):
    """Define the custom behaviour of Dialog"""

    def __init__(self, iface, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self._iface = iface
        self.project = QgsProject.instance()  # invoke a QgsProject instance
        self.last_maptool = self._iface.mapCanvas().mapTool()

        # Set up env variables for remaining quota
        os.environ["ORS_QUOTA"] = "None"
        os.environ["ORS_REMAINING"] = "None"

        # Programmtically invoke ORS logo
        header_pic = QPixmap(os.path.join(ICON_DIR, "openrouteservice.png"))
        pixmap = header_pic.scaled(150, 50,
                                   aspectRatioMode=Qt.KeepAspectRatio,
                                   transformMode=Qt.SmoothTransformation
                                   )
        self.header_pic.setPixmap(pixmap)
        # Settings button icon
        self.config_button.setIcon(QIcon(os.path.join(ICON_DIR, 'icon_settings.svg')))
        self.help_button.setIcon(QIcon(os.path.join(ICON_DIR, 'icon_help.png')))

        #### Set up signals/slots ####

        # Config/Advanced dialogs
        self.config_button.clicked.connect(lambda: on_config_click(self))

        # Isochrone tab
        self.iso_location_button.clicked.connect(self._initMapTool)
        self.iso_unit_combo.currentIndexChanged.connect(self._unitChanged)

        # Routing tab
        self.routing_start_frommap_button.clicked.connect(self._initMapTool)
        self.routing_end_frommap_button.clicked.connect(self._initMapTool)
        self.start_buttongroup.buttonReleased[int].connect(self._mappingMethodChanged)
        self.end_buttongroup.buttonReleased[int].connect(self._mappingMethodChanged)
        self.project.layerWasAdded.connect(self._layerTreeChanged)
        self.project.layersRemoved.connect(self._layerTreeChanged)
        self.routing_start_fromlayer_combo.currentIndexChanged[int].connect(self._layerSelectedChanged)
        self.routing_end_fromlayer_combo.currentIndexChanged[int].connect(self._layerSelectedChanged)

        # Populate combo boxes
        self.routing_travel_combo.addItems(PROFILES)
        self.iso_travel_combo.addItems(PROFILES)
        self.routing_preference_combo.addItems(PREFERENCES)
        self.iso_unit_combo.addItems(DIMENSIONS)
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

        # Returns a list of [layer_id, layer_name] for layer == VectorLayer and layer == PointLayer
        layers = [(layer.id(), layer.name()) for layer in self.project.mapLayers().values() if  \
                                                    layer.type() == QgsMapLayer.VectorLayer and \
                                                    layer.wkbType() == QgsWkbTypes.Type(1)]

        comboboxes = [self.routing_start_fromlayer_combo,
                      self.routing_end_fromlayer_combo,]

        for box in comboboxes:
            old_id = box.currentData()
            box.clear()
            for layer_id, layer_name in layers:
                box.addItem(layer_name, layer_id)
            # Make sure the old layer is still shown when this slot is triggered
            new_text_id = box.findData(old_id)
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
            layer_selected = self.project.mapLayer(sending_widget.currentData())
            for widget in parent_widget.findChildren(QComboBox):
                if widget.objectName() != sending_widget_name:
                    old_text = widget.currentText()
                    widget.clear()
                    widget.addItems([field.name() for field in layer_selected.fields()])
                    new_text_id = widget.findText(old_text)
                    widget.setCurrentIndex(0) if new_text_id == -1 else widget.setCurrentIndex(new_text_id)

    # def _clearVia(self):
    #     """
    #     Clears the 'via' coordinates label.
    #     """
    #     self.routing_via_label.setText("Long,Lat")

    def _unitChanged(self):
        """
        Connector to change unit label text when changing unit
        """
        if self.iso_unit_combo.currentText() == 'time':
            self.iso_range_unit_label.setText('mins')
        else:
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
            self.routing_start_frommap_label.setText("{0:.6f},{1:.6f}".format(x, y))

        if button == self.routing_end_frommap_button.objectName():
            self.routing_end_frommap_label.setText("{0:.6f},{1:.6f}".format(x, y))

        if button == self.iso_location_button.objectName():
            loc_dict = geocode_core.reverse_geocode(point)

            out_str = u"{0:.6f}\n{1:.6f}\n{2}\n{3}\n{4}".format(loc_dict.get('Lon', ""),
                                                                loc_dict.get('Lat', ""),
                                                                loc_dict.get('CITY', "NA"),
                                                                loc_dict.get('STATE', "NA"),
                                                                loc_dict.get('COUNTRY', "NA")
                                                                )
            self.iso_location_label.setText(out_str)

        # Restore old behavior
        QApplication.restoreOverrideCursor()
        self.mapTool.canvasClicked.disconnect()
        self._iface.mapCanvas().setMapTool(self.last_maptool)
        if self.windowState() == Qt.WindowMinimized:
            # Window is minimised. Restore it.
            self.setWindowState(Qt.WindowMaximized)
            self.activateWindow()