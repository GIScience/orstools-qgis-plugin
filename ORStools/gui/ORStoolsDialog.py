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

import os
from datetime import datetime
from typing import Optional

from qgis.PyQt.QtWidgets import QCheckBox

from ..utils.router import route_as_layer

try:
    import processing
except ModuleNotFoundError:
    pass

import webbrowser

from qgis.PyQt import uic
from qgis._core import Qgis
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsTextAnnotation,
    QgsMapLayerProxyModel,
    QgsFeature,
    QgsPointXY,
    QgsGeometry,
    QgsCoordinateReferenceSystem,
    QgsSettings,
    Qgis,  # noqa: F811
    QgsAnnotation,
    QgsCoordinateTransform,
)
from qgis.gui import QgsMapCanvasAnnotationItem, QgsCollapsibleGroupBox, QgisInterface
from qgis.PyQt.QtCore import QSizeF, QPointF, QCoreApplication
from qgis.PyQt.QtGui import QTextDocument
from qgis.PyQt.QtWidgets import QAction, QDialog, QApplication, QMenu, QMessageBox, QDialogButtonBox
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
    QWidget,
    QRadioButton,
)

from ORStools import (
    PLUGIN_NAME,
    DEFAULT_COLOR,
    __version__,
    __email__,
    __web__,
    __help__,
)
from ORStools.common import (
    PROFILES,
    PREFERENCES,
)
from ORStools.utils import maptools, configmanager, transform, gui
from .ORStoolsDialogConfig import ORStoolsDialogConfigMain

MAIN_WIDGET, _ = uic.loadUiType(gui.GuiUtils.get_ui_file_path("ORStoolsDialogUI.ui"))


def on_config_click(parent):
    """Pop up provider config window. Outside of classes because it's accessed by multiple dialogs.

    :param parent: Sets parent window for modality.
    :type parent: QDialog
    """
    config_dlg = ORStoolsDialogConfigMain(parent=parent)
    config_dlg.exec()


def on_help_click() -> None:
    """Open help URL from button/menu entry."""
    webbrowser.open(__help__)


def on_about_click(parent: QWidget) -> None:
    """Slot for click event of About button/menu entry."""

    # ruff will add trailing comma to last string line which breaks pylupdate5
    # fmt: off
    info = QCoreApplication.translate(
        "@default",
        '<b>ORS Tools</b> provides access to <a href="https://openrouteservice.org"'
        ' style="color: {0}">openrouteservice</a> routing functionalities.'
        "<br><br>"
        "<center>"
        '<a href="https://heigit.org/de/willkommen"><img src=":/plugins/ORStools/img/logo_heigit_300.png"/>'
        "</a><br><br>"
        "</center>"
        "Author: HeiGIT gGmbH<br>"
        'Email: <a href="mailto:Openrouteservice <{1}>">{1}</a><br>'
        'Web: <a href="{2}">{2}</a><br>'
        'Repo: <a href="https://github.com/GIScience/orstools-qgis-plugin">'
        "github.com/GIScience/orstools-qgis-plugin</a><br>"
        "Version: {3}"
    ).format(DEFAULT_COLOR, __email__, __web__, __version__)
    # fmt: on

    QMessageBox.information(
        parent, QCoreApplication.translate("@default", "About {}").format(PLUGIN_NAME), info
    )


class ORStoolsDialogMain:
    """Defines all mandatory QGIS things about dialog."""

    def __init__(self, iface: QgisInterface) -> None:
        """

        :param iface: the current QGIS interface
        :type iface: Qgis.Interface
        """
        self.iface = iface
        self.project = QgsProject.instance()

        self.first_start = True
        # Dialogs
        self.dlg = None
        self.menu = None
        self.actions = None

    # noinspection PyUnresolvedReferences
    def initGui(self) -> None:
        """Called when plugin is activated (on QGIS startup or when activated in Plugin Manager)."""

        icon_plugin = gui.GuiUtils.get_icon("icon_orstools.png")

        self.actions = [
            QAction(
                icon_plugin,
                PLUGIN_NAME,  # tr text
                self.iface.mainWindow(),  # parent
            ),
            # Config dialog
            QAction(
                gui.GuiUtils.get_icon("icon_settings.png"),
                self.tr("Provider Settings"),
                self.iface.mainWindow(),
            ),
            # About dialog
            QAction(
                gui.GuiUtils.get_icon("icon_about.png"), self.tr("About"), self.iface.mainWindow()
            ),
            # Help page
            QAction(
                gui.GuiUtils.get_icon("icon_help.png"), self.tr("Help"), self.iface.mainWindow()
            ),
        ]

        # Create menu
        self.menu = QMenu(PLUGIN_NAME)
        self.menu.setIcon(icon_plugin)
        self.menu.addActions(self.actions)

        # Add menu to Web menu and make sure it exists and add icon to toolbar
        self.iface.addPluginToWebMenu("_tmp", self.actions[2])
        self.iface.webMenu().addMenu(self.menu)
        self.iface.removePluginWebMenu("_tmp", self.actions[2])
        self.iface.addWebToolBarIcon(self.actions[0])

        # Connect slots to events
        self.actions[0].triggered.connect(self._init_gui_control)
        self.actions[1].triggered.connect(lambda: on_config_click(parent=self.iface.mainWindow()))
        self.actions[2].triggered.connect(lambda: on_about_click(parent=self.iface.mainWindow()))
        self.actions[3].triggered.connect(on_help_click)

        # Add keyboard shortcut
        self.iface.registerMainWindowAction(self.actions[0], "Ctrl+R")

    def unload(self) -> None:
        """Called when QGIS closes or plugin is deactivated in Plugin Manager"""

        self.iface.webMenu().removeAction(self.menu.menuAction())
        self.iface.removeWebToolBarIcon(self.actions[0])
        QApplication.restoreOverrideCursor()

        # Remove action for keyboard shortcut
        self.iface.unregisterMainWindowAction(self.actions[0])

        del self.dlg

    # @staticmethod
    # def get_quota(provider):
    #     """
    #     Update remaining quota from env variables.
    #
    #     :returns: remaining quota text to be displayed in GUI.
    #     :rtype: str
    #     """
    #
    #     # Dirty hack out of laziness.. Prone to errors
    #     text = []
    #     for var in sorted(provider['ENV_VARS'].keys(), reverse=True):
    #         text.append(os.environ[var])
    #     return '/'.join(text)

    def _init_gui_control(self) -> None:
        """Slot for main plugin button. Initializes the GUI and shows it."""

        # Only populate GUI if it's the first start of the plugin within the QGIS session
        # If not checked, GUI would be rebuilt every time!
        if self.first_start:
            self.first_start = False
            self.dlg = ORStoolsDialog(
                self.iface, self.iface.mainWindow()
            )  # setting parent enables modal view
            # Make sure plugin window stays open when OK is clicked by reconnecting the accepted() signal
            self.dlg.global_buttons.accepted.disconnect(self.dlg.accept)
            self.dlg.global_buttons.accepted.connect(self.run_gui_control)
            self.dlg.avoidpolygon_dropdown.setFilters(QgsMapLayerProxyModel.Filter.PolygonLayer)

        # Populate provider box on window startup, since can be changed from multiple menus/buttons
        providers = configmanager.read_config()["providers"]
        self.dlg.provider_combo.clear()
        for provider in providers:
            self.dlg.provider_combo.addItem(provider["name"], provider)

        self.dlg.show()

    def run_gui_control(self) -> None:
        """Slot function for OK button of main dialog."""
        if self.dlg.routing_fromline_list.count() == 0:
            return
        basepath = os.path.dirname(__file__)

        # add ors svg path
        my_new_path = os.path.join(basepath, "img/svg")
        svg_paths = QgsSettings().value("svg/searchPathsForSVG") or []
        if my_new_path not in svg_paths:
            svg_paths.append(my_new_path)
            QgsSettings().setValue("svg/searchPathsForSVG", svg_paths)

        # Associate annotations with map layer, so they get deleted when layer is deleted
        for annotation in self.dlg.annotations:
            # Has the potential to be pretty cool: instead of deleting, associate with mapLayer
            # , you can change order after optimization
            # Then in theory, when the layer is remove, the annotation is removed as well
            # Doesn't work though, the annotations are still there when project is re-opened
            # annotation.setMapLayer(layer_out)
            self.project.annotationManager().removeAnnotation(annotation)
        self.dlg.annotations = []
        self.dlg.rubber_band.reset()

        layer_out = route_as_layer(self.dlg)

        # style output layer
        qml_path = os.path.join(basepath, "linestyle.qml")
        layer_out.loadNamedStyle(qml_path, True)
        layer_out.triggerRepaint()

        self.project.addMapLayer(layer_out)

        self.dlg._clear_listwidget()
        self.dlg.line_tool = maptools.LineTool(self.dlg)

    def tr(self, string: str) -> str:
        return QCoreApplication.translate(str(self.__class__.__name__), string)


class ORStoolsDialog(QDialog, MAIN_WIDGET):
    """Define the custom behaviour of Dialog"""

    def __init__(self, iface: QgisInterface, parent=None) -> None:
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

        # Set things around the custom map tool
        self.line_tool = None
        self.canvas = self._iface.mapCanvas()
        self.last_maptool = self.canvas.mapTool()
        self.annotations = []

        # Set up env variables for remaining quota
        os.environ["ORS_QUOTA"] = "None"
        os.environ["ORS_REMAINING"] = "None"

        # Populate combo boxes
        self.routing_travel_combo.addItems(PROFILES)
        self.routing_preference_combo.addItems(PREFERENCES)

        # Change OK and Cancel button names
        self.global_buttons.button(QDialogButtonBox.StandardButton.Ok).setText(self.tr("Apply"))
        self.global_buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(self.tr("Close"))

        # Set up signals/slots

        # Config/Help dialogs
        self.provider_config.clicked.connect(lambda: on_config_click(self))
        self.help_button.clicked.connect(on_help_click)
        self.about_button.clicked.connect(lambda: on_about_click(parent=self._iface.mainWindow()))
        self.provider_refresh.clicked.connect(self._on_prov_refresh_click)

        # Routing tab
        self.routing_fromline_map.clicked.connect(self._on_linetool_init)
        self.routing_fromline_clear.clicked.connect(self._clear_listwidget)
        self.save_vertices.clicked.connect(self._save_vertices_to_layer)

        # Batch
        self.pushButton_routing_points.clicked.connect(
            lambda: processing.execAlgorithmDialog(f"{PLUGIN_NAME}:directions_from_points_2_layers")
        )
        self.pushButton_routing_point.clicked.connect(
            lambda: processing.execAlgorithmDialog(f"{PLUGIN_NAME}:directions_from_points_1_layer")
        )
        self.pushButton_routing_line.clicked.connect(
            lambda: processing.execAlgorithmDialog(f"{PLUGIN_NAME}:directions_from_polylines_layer")
        )
        self.pushButton_iso_point.clicked.connect(
            lambda: processing.execAlgorithmDialog(f"{PLUGIN_NAME}:isochrones_from_point")
        )
        self.pushButton_iso_layer.clicked.connect(
            lambda: processing.execAlgorithmDialog(f"{PLUGIN_NAME}:isochrones_from_layer")
        )
        self.pushButton_matrix.clicked.connect(
            lambda: processing.execAlgorithmDialog(f"{PLUGIN_NAME}:matrix_from_layers")
        )
        self.pushButton_snap_point.clicked.connect(
            lambda: processing.execAlgorithmDialog(f"{PLUGIN_NAME}:snap_from_point_layer")
        )
        self.pushButton_snap_layer.clicked.connect(
            lambda: processing.execAlgorithmDialog(f"{PLUGIN_NAME}:snap_from_point")
        )
        self.pushButton_export.clicked.connect(
            lambda: processing.execAlgorithmDialog(f"{PLUGIN_NAME}:export_network_from_map")
        )

        # Reset index of list items every time something is moved or deleted
        self.routing_fromline_list.model().rowsMoved.connect(self._reindex_list_items)
        self.routing_fromline_list.model().rowsRemoved.connect(self._reindex_list_items)

        # Add icons to buttons
        self.routing_fromline_map.setIcon(gui.GuiUtils.get_icon("icon_add.png"))
        self.routing_fromline_clear.setIcon(gui.GuiUtils.get_icon("icon_clear.png"))
        self.save_vertices.setIcon(gui.GuiUtils.get_icon("icon_save.png"))
        self.provider_refresh.setIcon(gui.GuiUtils.get_icon("icon_refresh.png"))
        self.provider_config.setIcon(gui.GuiUtils.get_icon("icon_settings.png"))
        self.about_button.setIcon(gui.GuiUtils.get_icon("icon_about.png"))
        self.help_button.setIcon(gui.GuiUtils.get_icon("icon_help.png"))

        # Connect signals to the color_duplicate_items function
        self.routing_fromline_list.model().rowsRemoved.connect(
            lambda: self.color_duplicate_items(self.routing_fromline_list)
        )
        self.routing_fromline_list.model().rowsInserted.connect(
            lambda: self.color_duplicate_items(self.routing_fromline_list)
        )

        self.load_provider_combo_state()
        self.provider_combo.activated.connect(self.save_selected_provider_state)

        advanced_boxes = self.advances_group.findChildren(QgsCollapsibleGroupBox)
        for box in advanced_boxes:
            box.collapsedStateChanged.connect(self.reload_rubber_band)
            for child in box.findChildren((QRadioButton, QCheckBox)):
                if isinstance(child, QCheckBox) and not child.objectName() == "export_jobs_order":
                    child.stateChanged.connect(self.reload_rubber_band)
                elif isinstance(child, QRadioButton):
                    child.toggled.connect(self.reload_rubber_band)

        self.rubber_band = None

    def _save_vertices_to_layer(self) -> None:
        """Saves the vertices list to a temp layer"""
        items = [
            self.routing_fromline_list.item(x).text()
            for x in range(self.routing_fromline_list.count())
        ]

        if len(items) > 0:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
            point_layer = QgsVectorLayer(
                "point?crs=epsg:4326&field=ID:integer", f"Vertices_{timestamp}", "memory"
            )
            point_layer.updateFields()
            for idx, x in enumerate(items):
                coords = x.split(":")[1]
                x, y = (float(i) for i in coords.split(", "))
                feature = QgsFeature()
                feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))
                feature.setAttributes([idx])

                point_layer.dataProvider().addFeature(feature)
            QgsProject.instance().addMapLayer(point_layer)
            self.canvas.refresh()

        self._iface.messageBar().pushMessage(
            self.tr("Success"), self.tr("Vertices saved to layer."), level=Qgis.MessageLevel.Success
        )

    def _on_prov_refresh_click(self) -> None:
        """Populates provider dropdown with fresh list from config.yml"""

        providers = configmanager.read_config()["providers"]
        self.provider_combo.clear()
        for provider in providers:
            self.provider_combo.addItem(provider["name"], provider)

    def _clear_listwidget(self) -> None:
        """Clears the contents of the QgsListWidget and the annotations."""
        items = self.routing_fromline_list.selectedItems()
        if items:
            rows = [self.routing_fromline_list.row(item) for item in items]
            # if items are selected, only clear those
            for row in sorted(rows, reverse=True):
                if self.annotations:
                    self.project.annotationManager().removeAnnotation(self.annotations.pop(row))
                self.routing_fromline_list.takeItem(row)
                self.line_tool.error_idxs += 1
        else:
            # else clear all items and annotations
            self.routing_fromline_list.clear()
            self._clear_annotations()
            QApplication.restoreOverrideCursor()
            self.canvas.setMapTool(self.last_maptool)
            # Remove blue lines (rubber band)
            if self.rubber_band:
                self.rubber_band.reset()
            self.line_tool = maptools.LineTool(self)

    def _linetool_annotate_point(
        self, point: QgsPointXY, idx: int, crs: Optional[QgsCoordinateReferenceSystem] = None
    ) -> QgsAnnotation:
        if not crs:
            crs = QgsProject.instance().crs()

        annotation = QgsTextAnnotation()

        c = QTextDocument()
        html = "<strong>" + str(idx) + "</strong>"
        c.setHtml(html)

        annotation.setDocument(c)

        annotation.setFrameSizeMm(QSizeF(8, 5))
        annotation.setFrameOffsetFromReferencePointMm(QPointF(1.3, 1.3))
        annotation.setMapPositionCrs(crs)
        annotation.setMapPosition(point)

        return QgsMapCanvasAnnotationItem(annotation, self.canvas).annotation()

    def _clear_annotations(self) -> None:
        """Clears annotations"""
        for annotation_item in self.canvas.annotationItems():
            annotation = annotation_item.annotation()
            if annotation in self.project.annotationManager().annotations():
                self.project.annotationManager().removeAnnotation(annotation)
        self.annotations = []
        if self.rubber_band:
            self.rubber_band.reset()

    def _on_linetool_init(self) -> None:
        """Hides GUI dialog, inits line maptool and add items to line list box."""
        self.hide()
        if self.line_tool:
            self.canvas.setMapTool(self.line_tool)
        else:
            self.line_tool = maptools.LineTool(self)
            self.canvas.setMapTool(self.line_tool)

    def create_vertex(self, point, idx):
        """Adds an item to QgsListWidget and annotates the point in the map canvas"""
        map_crs = self.canvas.mapSettings().destinationCrs()

        transformer = transform.transformToWGS(map_crs)
        point_wgs = transformer.transform(point)
        self.routing_fromline_list.addItem(f"Point {idx}: {point_wgs.x():.6f}, {point_wgs.y():.6f}")

        crs = self.canvas.mapSettings().destinationCrs()
        annotation = self._linetool_annotate_point(point, idx, crs)
        self.annotations.append(annotation)
        self.project.annotationManager().addAnnotation(annotation)

    def _reindex_list_items(self) -> None:
        """Resets the index when an item in the list is moved"""
        items = [
            self.routing_fromline_list.item(x).text()
            for x in range(self.routing_fromline_list.count())
        ]
        self.routing_fromline_list.clear()
        self._clear_annotations()
        crs = QgsCoordinateReferenceSystem(f"EPSG:{4326}")
        project_crs = self.canvas.mapSettings().destinationCrs()
        for idx, x in enumerate(items):
            coords = x.split(":")[1]
            item = f"Point {idx}:{coords}"
            x, y = (float(i) for i in coords.split(", "))
            point = QgsPointXY(x, y)

            self.routing_fromline_list.addItem(item)
            transform = QgsCoordinateTransform(crs, project_crs, QgsProject.instance())
            point = transform.transform(point)
            annotation = self._linetool_annotate_point(point, idx)
            self.annotations.append(annotation)
            self.project.annotationManager().addAnnotation(annotation)
        try:
            self.line_tool.create_rubber_band()
        except Exception as e:
            if "Connection refused" in str(e):
                self.api_key_message_bar()
            else:
                raise e

    def color_duplicate_items(self, list_widget):
        item_dict = {}
        for index in range(list_widget.count()):
            item = list_widget.item(index)
            text = item.text()
            if text in item_dict:
                item_dict[text].append(index)
            else:
                item_dict[text] = [index]

        for indices in item_dict.values():
            if len(indices) > 1:
                for index in indices:
                    item = list_widget.item(index)
                    item.setBackground(QColor("lightsalmon"))

    def reload_rubber_band(self) -> None:
        """Reloads the rubber band of the linetool."""
        if self.line_tool is not None:
            self.line_tool.create_rubber_band()

    def save_selected_provider_state(self) -> None:
        s = QgsSettings()
        s.setValue("ORSTools/gui/provider_combo", self.provider_combo.currentIndex())

    def load_provider_combo_state(self):
        s = QgsSettings()
        index = s.value("ORSTools/gui/provider_combo")
        if index:
            self.provider_combo.setCurrentIndex(int(index))

    def show(self):
        """Load the saved state when the window is shown"""
        super().show()
        self.load_provider_combo_state()
