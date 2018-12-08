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

from PyQt5.QtWidgets import (QAction,
                             QDialog,
                             QApplication,
                             QComboBox,
                             QPushButton,
                             QMenu,
                             QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
from qgis.core import (QgsProject,
                       QgsMapLayer,
                       QgsWkbTypes,
                       )

from ORStools import ICON_DIR, PLUGIN_NAME, ENV_VARS, __version__, DEFAULT_COLOR
from ORStools.utils import exceptions, pointtool
from ORStools.core import (client,
                           isochrones_core,
                           directions_core,
                           matrix_core,
                           geocode_core,
                           PROFILES,
                           PREFERENCES,
                           UNITS)
from ORStools.gui import (isochrones_gui)
from .ORStoolsDialogUI import Ui_ORStoolsDialogBase
from .ORStoolsDialogConfig import ORStoolsDialogConfigMain
from .ORStoolsDialogAdvanced import ORStoolsDialogAdvancedMain


def on_config_click(parent):
    """Pop up config window. Outside of classes because it's accessed by both.
    """
    config_dlg = ORStoolsDialogConfigMain(parent=parent)
    config_dlg.exec_()


class ORStoolsDialogMain:
    """Defines all mandatory QGIS things about dialog."""

    def __init__(self, iface):
        """

        :param iface: the current QGIS interface
        :type iface: Qgis.Interface
        """
        self.iface = iface

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
        self.actions[2].triggered.connect(self._on_about_click)

    def unload(self):
        self.iface.webMenu().removeAction(self.menu.menuAction())
        self.iface.removeWebToolBarIcon(self.actions[0])
        QApplication.restoreOverrideCursor()
        del self.dlg
        del self.advanced

    def _on_about_click(self):
        info = '<b>ORS Tools</b> provides access to <a href="https://openrouteservice.org" style="color: {}">openrouteservice</a> routing functionalities.<br><br>' \
               'Author: Nils Nolde<br>' \
               'Email: <a href="mailto:Nils Nolde <nils@gis-ops.com>">nils@gis-ops.com</a><br>' \
               'Web: <a href="https://gis-ops.com">gis-ops.com</a><br>' \
               'Repo: <a href="https://github.com/nilsnolde/ORStools">github.com/nilsnolde/ORStools</a><br>' \
               'Version: {}'.format(DEFAULT_COLOR, __version__)

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
        # If not checked, GUI will be rebuild every time!

        if self.first_start:
            self.first_start = False
            self.dlg = ORStoolsDialog(self.iface, self.iface.mainWindow())  # setting parent enables modal view
            # Connect acvanced dialog
            self.dlg.routing_advanced_button.clicked.connect(self._on_advanced_click)

        # Connect Advanced dialog; makes sure that dialog is re-populated every time plugin starts
        self.advanced = ORStoolsDialogAdvancedMain(parent=self.dlg)
        self.dlg.show()
        result = self.dlg.exec_()
        if result:
            try:
                clnt = client.Client(self.iface)
                feat_counter = 0

                if self.dlg.tabWidget.currentIndex() == 2:
                    m = matrix_core.matrix(self.dlg, clnt, self.iface)
                    m.matrix_calc()

                elif self.dlg.tabWidget.currentIndex() == 1:
                    iso_gui = isochrones_gui.IsochronesGui(self.dlg)
                    params = iso_gui.getParameters()
                    for properties in iso_gui.getFeatureParameters(self.dlg.iso_layer_check.isChecked()):
                        params['locations'], params['id'] = properties
                        response = isochrones_request(clnt, params)

                        # Update progress bar
                        feat_counter += 1
                        self.dlg.progressBar.setValue(int(feat_counter/iso_gui.feature_count * 100))

                elif self.dlg.tabWidget.currentIndex() == 0:
                    route = directions_core.directions(self.dlg, clnt, self.iface)
                    route.directions_calc()

                # Update quota; handled in client module after successful request
                self.dlg.quota_text.setText(self.get_quota() + 'req')
            except exceptions.Timeout:
                self.iface.messageBar().pushCritical('Time out',
                                                      'The connection exceeded the '
                                                      'timeout limit of 60 seconds')

            except (exceptions.ApiError,
                    exceptions.OverQueryLimit) as e:
                self.iface.messageBar().pushCritical("{}: ".format(type(e).__name__),
                                                     "{}".format(str(e)))
            finally:
                # TODO: features requested up to the error need to be rendered
                self.dlg.progressBar.setValue(0)
                self.dlg.progressBar.close()
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

        #### Set up signals/slots ####

        # Config/Advanced dialogs
        self.config_button.clicked.connect(lambda: on_config_click(self))

        # # Apply button, to update remaining quota
        # self.global_buttons.Apply.clicked.connect(self._on_apply_click)

        # Matrix tab
        self.matrix_start_combo.currentIndexChanged.connect(self._layerSelectedChanged)
        self.matrix_end_combo.currentIndexChanged.connect(self._layerSelectedChanged)
        # self.matrix_start_refresh.clicked.connect(self._layerTreeChanged)
        # self.matrix_end_refresh.clicked.connect(self._layerTreeChanged)

        # Isochrone tab
        self.iso_location_button.clicked.connect(self._initMapTool)
        self.iso_unit_combo.currentIndexChanged.connect(self._unitChanged)
        self.iso_layer_check.stateChanged.connect(self._accessLayerChanged)
        # self.iso_layer_refresh.clicked.connect(self._layerTreeChanged)

        # Routing tab
        self.routing_start_frommap_button.clicked.connect(self._initMapTool)
        # self.routing_via_map_button.clicked.connect(self._initMapTool)
        self.routing_end_frommap_button.clicked.connect(self._initMapTool)
        self.start_buttongroup.buttonReleased[int].connect(self._mappingMethodChanged)
        self.end_buttongroup.buttonReleased[int].connect(self._mappingMethodChanged)
        # self.routing_via_clear_button.clicked.connect(self._clearVia)
        self.project.layerWasAdded.connect(self._layerTreeChanged)
        self.project.layersRemoved.connect(self._layerTreeChanged)
        # self.routing_start_fromlayer_refresh.clicked.connect(self._layerTreeChanged)
        # self.routing_end_fromlayer_refresh.clicked.connect(self._layerTreeChanged)
        self.routing_start_fromlayer_combo.currentIndexChanged[int].connect(self._layerSelectedChanged)
        self.routing_end_fromlayer_combo.currentIndexChanged[int].connect(self._layerSelectedChanged)

        # Populate combo boxes
        self.routing_travel_combo.addItems(PROFILES)
        self.iso_travel_combo.addItems(PROFILES)
        self.matrix_travel_combo.addItems(PROFILES)
        self.routing_preference_combo.addItems(PREFERENCES)
        self.iso_unit_combo.addItems(UNITS)
        self._layerTreeChanged()

    # def _on_apply_click(self):
    #     """Update remaining quota from env variables"""
    #     text = os.environ['ORS_REMAINING'] + "/" + os.environ['ORS_QUOTA']

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
                      self.routing_end_fromlayer_combo,
                      self.iso_layer_combo,
                      self.matrix_start_combo,
                      self.matrix_end_combo]

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

        # if button == self.routing_via_map_button.objectName():
        #     self.routing_via_label.setText("{0:.5f},{1:.5f}".format(x, y))

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