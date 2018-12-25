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
                             QMenu,
                             QMessageBox,
                             QDialogButtonBox)
from PyQt5.QtGui import QIcon

from qgis.core import (QgsProject,
                       QgsVectorLayer)
from qgis.gui import QgsFilterLineEdit

from . import resources_rc

from ORStools import RESOURCE_PREFIX, PLUGIN_NAME, ENV_VARS, DEFAULT_COLOR, __version__, __email__, __web__, __help__
from ORStools.utils import exceptions, maptools, logger, configmanager, convert
from ORStools.core import (client,
                           directions_core,
                           PROFILES,
                           PREFERENCES,
                           DIMENSIONS)
from ORStools.gui import directions_gui

from .ORStoolsDialogUI import Ui_ORStoolsDialogBase
from .ORStoolsDialogConfig import ORStoolsDialogConfigMain
from .ORStoolsDialogAdvanced import ORStoolsDialogAdvancedMain


def on_config_click(parent):
    """Pop up provider config window. Outside of classes because it's accessed by multiple dialogs.

    :param parent: Sets parent window for modality.
    :type parent: QDialog
    """
    config_dlg = ORStoolsDialogConfigMain(parent=parent)
    config_dlg.exec_()


def on_help_click():
    """Open help URL from button/menu entry."""
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
        """Called when plugin is activated (on QGIS startup or when activated in Plugin Manager)."""

        def create_icon(f):
            """
            internal function to create action icons

            :param f: file name of icon.
            :type f: str

            :returns: icon object to insert to QAction
            :rtype: QIcon
            """
            return QIcon(RESOURCE_PREFIX + f)

        icon_plugin = create_icon('icon_orstools.png')

        self.actions = [
            QAction(
                icon_plugin,
                PLUGIN_NAME,  # tr text
                self.iface.mainWindow()  # parent
            ),
            # Config dialog
            QAction(
                create_icon('icon_settings.png'),
                'Provider Settings',
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
        self.actions[0].triggered.connect(self._init_gui_control)
        self.actions[1].triggered.connect(lambda: on_config_click(parent=self.iface.mainWindow()))
        self.actions[3].triggered.connect(on_help_click)
        # Connect other dialogs
        self.actions[2].triggered.connect(self._on_about_click)

    def unload(self):
        """Called when QGIS closes or plugin is deactivated in Plugin Manager"""

        self.iface.webMenu().removeAction(self.menu.menuAction())
        self.iface.removeWebToolBarIcon(self.actions[0])
        QApplication.restoreOverrideCursor()
        del self.dlg
        del self.advanced

    def _on_about_click(self):
        """Slot for click event of About button/menu entry."""

        info = '<b>ORS Tools</b> provides access to <a href="https://openrouteservice.org" style="color: {0}">openrouteservice</a> routing functionalities.<br><br>' \
               '<center><a href=\"https://gis-ops.com\"><img src=\":/plugins/ORStools/img/logo_gisops_300.png\"/></a> <br><br></center>' \
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

    def _on_advanced_click(self):
        """Slot for click event of advanced dialog button."""

        self.advanced.exec_()

    @staticmethod
    def get_quota():
        """
        Update remaining quota from env variables.

        :returns: remaining quota text to be displayed in GUI.
        :rtype: str
        """

        # Dirty hack out of laziness.. Prone to errors
        text = []
        for var in sorted(ENV_VARS.keys(), reverse=True):
            text.append(os.environ[var])
        return '/'.join(text)

    def _init_gui_control(self):
        """Slot for main plugin button. Initializes the GUI and shows it."""

        # Only populate GUI if it's the first start of the plugin within the QGIS session
        # If not checked, GUI would be rebuilt every time!
        if self.first_start:
            self.first_start = False
            self.dlg = ORStoolsDialog(self.iface, self.iface.mainWindow())  # setting parent enables modal view
            self.dlg.routing_advanced_button.clicked.connect(self._on_advanced_click)
            # Make sure plugin window stays open when OK is clicked by reconnecting the accepted() signal
            self.dlg.global_buttons.accepted.disconnect(self.dlg.accept)
            self.dlg.global_buttons.accepted.connect(self.run_gui_control)

        # Populate provider box on window startup, since can be changed from multiple menus/buttons
        providers = configmanager.read_config()['providers']
        self.dlg.provider_combo.clear()
        for provider in providers:
            self.dlg.provider_combo.addItem(provider['name'], provider)

        # Populate Advanced dialog; makes sure that dialog is re-populated every time plugin starts,
        # but stays alive during one session
        self.advanced = ORStoolsDialogAdvancedMain(parent=self.dlg)
        self.dlg.show()

    def run_gui_control(self):
        """Slot function for OK button of main dialog."""

        layer_out = QgsVectorLayer("LineString?crs=EPSG:4326", "Route_ORS", "memory")
        layer_out.dataProvider().addAttributes(directions_core.get_fields())
        layer_out.updateFields()

        provider = self.dlg.provider_combo.currentData()
        clnt = client.Client(provider)
        clnt_msg = ''

        directions = directions_gui.Directions(self.dlg, self.advanced)
        params = directions.get_basic_paramters()
        from_id = None
        to_id = None
        try:
            if self.dlg.routing_tab.currentIndex() == 0:
                x_start = self.dlg.routing_frompoint_start_x.value()
                y_start = self.dlg.routing_frompoint_start_y.value()
                x_end = self.dlg.routing_frompoint_end_x.value()
                y_end = self.dlg.routing_frompoint_end_y.value()

                params['coordinates'] = convert.build_coords([[x_start,y_start],
                                                              [x_end, y_end]])
                from_id = convert.comma_list([x_start, y_start])
                to_id = convert.comma_list([x_end, y_end])

            elif self.dlg.routing_tab.currentIndex() == 1:
                params['coordinates'] = convert.build_coords(directions.get_request_line_feature())

            response = clnt.request(provider['endpoints']['directions'], params)
            layer_out.dataProvider().addFeature(directions_core.get_output_feature(
                response,
                params['profile'],
                params['preference'],
                directions.avoid,
                from_id,
                to_id
            ))

            layer_out.updateExtents()
            self.project.addMapLayer(layer_out)

            # Update quota; handled in client module after successful request
            self.dlg.quota_text.setText(self.get_quota() + ' calls')
        except exceptions.Timeout as e:
            msg = "The connection has timed out!"
            logger.log(msg, 2)
            self.dlg.debug_text.setText(msg)

        except (exceptions.ApiError,
                exceptions.InvalidKey,
                exceptions.GenericServerError) as e:
            msg = (e.__class__.__name__,
                   str(e))

            logger.log("{}: ({})".format(*msg, 2))
            clnt_msg += "<b>{}</b>: ({})<br>".format(*msg)
        finally:
            # Set URL in debug window
            clnt_msg += '<a href="{0}">{0}</a><br>'.format(clnt.url)
            self.dlg.debug_text.setHtml(clnt_msg)

class ORStoolsDialog(QDialog, Ui_ORStoolsDialogBase):
    """Define the custom behaviour of Dialog"""

    def __init__(self, iface, parent=None):
        """
        :param iface: QGIS interface
        :type iface: QgisInterface

        :param parent: parent window for modality.
        :type parent: QDialog/QApplication
        """
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self._iface = iface
        self.project = QgsProject.instance()  # invoke a QgsProject instance

        self.point_tool = None
        self.line_tool = None
        self.last_maptool = self._iface.mapCanvas().mapTool()
        self.clear_buttons = [self.routing_frompoint_end_clear,
                              self.routing_frompoint_start_clear]

        # Set up env variables for remaining quota
        os.environ["ORS_QUOTA"] = "None"
        os.environ["ORS_REMAINING"] = "None"

        # Populate combo boxes
        self.routing_travel_combo.addItems(PROFILES)
        self.iso_travel_combo.addItems(PROFILES)
        self.routing_preference_combo.addItems(PREFERENCES)
        self.iso_unit_combo.addItems(DIMENSIONS)

        # Change OK and Cancel button names
        self.global_buttons.button(QDialogButtonBox.Ok).setText('Apply')
        self.global_buttons.button(QDialogButtonBox.Cancel).setText('Close')

        #### Set up signals/slots ####

        # Config/Help dialogs
        self.provider_config.clicked.connect(lambda: on_config_click(self))
        self.help_button.clicked.connect(on_help_click)
        self.provider_refresh.clicked.connect(self._on_prov_refresh_click)

        # # Isochrone tab
        # self.iso_location_button.clicked.connect(self._initMapTool)
        # self.iso_unit_combo.currentIndexChanged.connect(self._unitChanged)

        # Routing tab
        self.routing_frompoint_start_map.clicked.connect(self._on_point_click)
        self.routing_frompoint_end_map.clicked.connect(self._on_point_click)
        self.routing_fromline_map.clicked.connect(self._on_line_click)
        self.routing_fromline_remove.clicked.connect(self._on_remove_click)
        self.routing_fromline_clear.clicked.connect(lambda: self.routing_fromline_list.clear())
        for button in self.clear_buttons:
            button.clicked.connect(self._on_clear_click)

    def _on_clear_click(self):
        """Clear the QgsFilterLineEdit widgets associated with the clear buttons"""

        sending_button = self.sender()
        parent_widget = sending_button.parentWidget()
        line_edit_widgets = parent_widget.findChildren(QgsFilterLineEdit)
        for widget in line_edit_widgets:
            widget.clearValue()

    def _on_prov_refresh_click(self):
        """Populates provider dropdown with fresh list from config.yml"""

        providers = configmanager.read_config()['providers']
        self.provider_combo.clear()
        for provider in providers:
            self.provider_combo.addItem(provider['name'], provider)

    def _unitChanged(self):
        """Connector to change unit label text when changing unit"""

        if self.iso_unit_combo.currentText() == 'time':
            self.iso_range_unit_label.setText('mins')
        else:
            self.iso_range_unit_label.setText('m')

    def _on_remove_click(self):
        """remove items from line list box"""

        items = self.routing_fromline_list.selectedItems()
        for item in items:
            row = self.routing_fromline_list.row(item)
            self.routing_fromline_list.takeItem(row)

    def _on_line_click(self):
        """Hides GUI dialog, inits line maptool and add items to line list box."""
        self.hide()
        self.routing_fromline_list.clear()
        self.line_tool = maptools.LineTool(self._iface.mapCanvas())
        self._iface.mapCanvas().setMapTool(self.line_tool)
        self.line_tool.pointDrawn.connect(lambda point, idx: self.routing_fromline_list.addItem("Point {0}: {1:.6f}, {2:.6f}".format(idx, point.x(), point.y())))
        self.line_tool.doubleClicked.connect(self._restore_map_tool)

    def _restore_map_tool(self, points_num):
        """
        Populate line list widget with coordinates, end line drawing and show dialog again.

        :param points_num: number of points drawn so far.
        :type points_num: int
        """
        if points_num < 2:
            self.routing_fromline_list.clear()
        self.line_tool.pointDrawn.disconnect()
        self.line_tool.doubleClicked.disconnect()
        self._iface.mapCanvas().setMapTool(self.last_maptool)
        self.show()

    def _on_point_click(self):
        """
        Initialize the mapTool to select coordinates in map canvas and hide dialog.
        """
        self.hide()
        sending_button = self.sender().objectName()
        self.point_tool = maptools.PointTool(self._iface.mapCanvas(), sending_button)
        self._iface.mapCanvas().setMapTool(self.point_tool)
        self.point_tool.canvasClicked.connect(self._writePointLabel)

    # Write map coordinates to text fields
    def _writePointLabel(self, point, button):
        """
        Writes the selected coordinates from map canvas to its QgsFilterLineEdit widgets.
        
        :param point: Point selected with mapTool.
        :type point: QgsPointXY
        
        :param button: Button which intialized mapTool.
        :param button: QPushButton
        """

        x, y = point

        if button == self.routing_frompoint_start_map.objectName():
            self.routing_frompoint_start_x.setText("{0:.6f}".format(x))
            self.routing_frompoint_start_y.setText("{0:.6f}".format(y))

        if button == self.routing_frompoint_end_map.objectName():
            self.routing_frompoint_end_x.setText("{0:.6f}".format(x))
            self.routing_frompoint_end_y.setText("{0:.6f}".format(y))

        QApplication.restoreOverrideCursor()
        self.point_tool.canvasClicked.disconnect()
        self._iface.mapCanvas().setMapTool(self.last_maptool)
        self.show()