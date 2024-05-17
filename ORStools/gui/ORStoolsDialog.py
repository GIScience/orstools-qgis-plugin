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

import json
import os
from typing import Optional

import processing
import webbrowser

from qgis._core import Qgis, QgsAnnotation
from qgis._gui import QgisInterface
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
)
from qgis.gui import QgsMapCanvasAnnotationItem

from qgis.PyQt.QtCore import QSizeF, QPointF, QCoreApplication
from qgis.PyQt.QtGui import QIcon, QTextDocument
from qgis.PyQt.QtWidgets import (
    QAction,
    QDialog,
    QApplication,
    QMenu,
    QMessageBox,
    QDialogButtonBox,
    QWidget,
)

from ORStools import (
    RESOURCE_PREFIX,
    PLUGIN_NAME,
    DEFAULT_COLOR,
    __version__,
    __email__,
    __web__,
    __help__,
)
from ORStools.common import (
    client,
    directions_core,
    PROFILES,
    PREFERENCES,
)
from ORStools.gui import directions_gui
from ORStools.utils import exceptions, maptools, logger, configmanager, transform
from .ORStoolsDialogConfig import ORStoolsDialogConfigMain
from .ORStoolsDialogUI import Ui_ORStoolsDialogBase

from . import resources_rc  # noqa: F401


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
        "Version: {3}",
    ).format(DEFAULT_COLOR, __email__, __web__, __version__)

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

        def create_icon(f: str) -> QIcon:
            """
            internal function to create action icons

            :param f: file name of icon.
            :type f: str

            :returns: icon object to insert to QAction
            :rtype: QIcon
            """
            return QIcon(RESOURCE_PREFIX + f)

        icon_plugin = create_icon("icon_orstools.png")

        self.actions = [
            QAction(
                icon_plugin,
                PLUGIN_NAME,  # tr text
                self.iface.mainWindow(),  # parent
            ),
            # Config dialog
            QAction(
                create_icon("icon_settings.png"),
                self.tr("Provider Settings"),
                self.iface.mainWindow(),
            ),
            # About dialog
            QAction(create_icon("icon_about.png"), self.tr("About"), self.iface.mainWindow()),
            # Help page
            QAction(create_icon("icon_help.png"), self.tr("Help"), self.iface.mainWindow()),
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

        layer_out = QgsVectorLayer("LineString?crs=EPSG:4326", "Route_ORS", "memory")
        layer_out.dataProvider().addAttributes(directions_core.get_fields())
        layer_out.updateFields()

        basepath = os.path.dirname(__file__)

        # add ors svg path
        my_new_path = os.path.join(basepath, "img/svg")
        svg_paths = QgsSettings().value("svg/searchPathsForSVG") or []
        if my_new_path not in svg_paths:
            svg_paths.append(my_new_path)
            QgsSettings().setValue("svg/searchPathsForSVG", svg_paths)

        # style output layer
        qml_path = os.path.join(basepath, "linestyle.qml")
        layer_out.loadNamedStyle(qml_path, True)
        layer_out.triggerRepaint()

        # Associate annotations with map layer, so they get deleted when layer is deleted
        for annotation in self.dlg.annotations:
            # Has the potential to be pretty cool: instead of deleting, associate with mapLayer
            # , you can change order after optimization
            # Then in theory, when the layer is remove, the annotation is removed as well
            # Doesn't work though, the annotations are still there when project is re-opened
            # annotation.setMapLayer(layer_out)
            self.project.annotationManager().removeAnnotation(annotation)
        self.dlg.annotations = []

        provider_id = self.dlg.provider_combo.currentIndex()
        provider = configmanager.read_config()["providers"][provider_id]

        # if there are no coordinates, throw an error message
        if not self.dlg.routing_fromline_list.count():
            QMessageBox.critical(
                self.dlg,
                "Missing Waypoints",
                """
                Did you forget to set routing waypoints?<br><br>
                
                Use the 'Add Waypoint' button to add up to 50 waypoints.
                """,
            )
            return

        # if no API key is present, when ORS is selected, throw an error message
        if not provider["key"] and provider["base_url"].startswith(
            "https://api.openrouteservice.org"
        ):
            QMessageBox.critical(
                self.dlg,
                "Missing API key",
                """
                Did you forget to set an <b>API key</b> for openrouteservice?<br><br>
                
                If you don't have an API key, please visit https://openrouteservice.org/sign-up to get one. <br><br> 
                Then enter the API key for openrouteservice provider in Web ► ORS Tools ► Provider Settings or the 
                settings symbol in the main ORS Tools GUI, next to the provider dropdown.""",
            )
            return

        agent = "QGIS_ORStoolsDialog"
        clnt = client.Client(provider, agent)
        clnt_msg = ""

        directions = directions_gui.Directions(self.dlg)
        params = None
        try:
            params = directions.get_parameters()
            if self.dlg.optimization_group.isChecked():
                if len(params["jobs"]) <= 1:  # Start/end locations don't count as job
                    QMessageBox.critical(
                        self.dlg,
                        "Wrong number of waypoints",
                        """At least 3 or 4 waypoints are needed to perform routing optimization. 

Remember, the first and last location are not part of the optimization.
                        """,
                    )
                    return
                response = clnt.request("/optimization", {}, post_json=params)

                if self.dlg.export_jobs_order.isChecked():
                    items = list()
                    for route in response["routes"]:
                        for i, step in enumerate(route["steps"]):
                            location = step["location"]
                            items.append(location)

                    point_layer = QgsVectorLayer(
                        "point?crs=epsg:4326&field=ID:integer", "Steps", "memory"
                    )

                    point_layer.updateFields()
                    for idx, coords in enumerate(items):
                        x, y = coords
                        feature = QgsFeature()
                        feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))
                        feature.setAttributes([idx])

                        point_layer.dataProvider().addFeature(feature)
                    QgsProject.instance().addMapLayer(point_layer)
                    self.dlg._iface.mapCanvas().refresh()

                feat = directions_core.get_output_features_optimization(
                    response, params["vehicles"][0]["profile"]
                )
            else:
                params["coordinates"] = directions.get_request_line_feature()
                profile = self.dlg.routing_travel_combo.currentText()
                # abort on empty avoid polygons layer
                if (
                    "options" in params
                    and "avoid_polygons" in params["options"]
                    and params["options"]["avoid_polygons"] == {}
                ):
                    QMessageBox.warning(
                        self.dlg,
                        "Empty layer",
                        """
The specified avoid polygon(s) layer does not contain any features.
Please add polygons to the layer or uncheck avoid polygons.
                        """,
                    )
                    msg = "The request has been aborted!"
                    logger.log(msg, 0)
                    self.dlg.debug_text.setText(msg)
                    return
                response = clnt.request(
                    "/v2/directions/" + profile + "/geojson", {}, post_json=params
                )
                feat = directions_core.get_output_feature_directions(
                    response, profile, params["preference"], directions.options
                )

            layer_out.dataProvider().addFeature(feat)

            layer_out.updateExtents()
            self.project.addMapLayer(layer_out)

            # Update quota; handled in client module after successful request
            # if provider.get('ENV_VARS'):
            #     self.dlg.quota_text.setText(self.get_quota(provider) + ' calls')
        except exceptions.Timeout:
            msg = "The connection has timed out!"
            logger.log(msg, 2)
            self.dlg.debug_text.setText(msg)
            return

        except (exceptions.ApiError, exceptions.InvalidKey, exceptions.GenericServerError) as e:
            logger.log(f"{e.__class__.__name__}: {str(e)}", 2)
            clnt_msg += f"<b>{e.__class__.__name__}</b>: ({str(e)})<br>"
            raise

        except Exception as e:
            logger.log(f"{e.__class__.__name__}: {str(e)}", 2)
            clnt_msg += f"<b>{e.__class__.__name__}</b>: {str(e)}<br>"
            raise

        finally:
            # Set URL in debug window
            if params:
                clnt_msg += f'<a href="{clnt.url}">{clnt.url}</a><br>Parameters:<br>{json.dumps(params, indent=2)}'
            self.dlg.debug_text.setHtml(clnt_msg)

    def tr(self, string: str) -> str:
        return QCoreApplication.translate(str(self.__class__.__name__), string)


class ORStoolsDialog(QDialog, Ui_ORStoolsDialogBase):
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
        self.last_maptool = self._iface.mapCanvas().mapTool()
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
        self.routing_fromline_clear.clicked.connect(self._on_clear_listwidget_click)
        self.save_vertices.clicked.connect(self._save_vertices_to_layer)

        # Batch
        self.batch_routing_points.clicked.connect(
            lambda: processing.execAlgorithmDialog(f"{PLUGIN_NAME}:directions_from_points_2_layers")
        )
        self.batch_routing_point.clicked.connect(
            lambda: processing.execAlgorithmDialog(f"{PLUGIN_NAME}:directions_from_points_1_layer")
        )
        self.batch_routing_line.clicked.connect(
            lambda: processing.execAlgorithmDialog(f"{PLUGIN_NAME}:directions_from_polylines_layer")
        )
        self.batch_iso_point.clicked.connect(
            lambda: processing.execAlgorithmDialog(f"{PLUGIN_NAME}:isochrones_from_point")
        )
        self.batch_iso_layer.clicked.connect(
            lambda: processing.execAlgorithmDialog(f"{PLUGIN_NAME}:isochrones_from_layer")
        )
        self.batch_matrix.clicked.connect(
            lambda: processing.execAlgorithmDialog(f"{PLUGIN_NAME}:matrix_from_layers")
        )

        # Reset index of list items every time something is moved or deleted
        self.routing_fromline_list.model().rowsMoved.connect(self._reindex_list_items)
        self.routing_fromline_list.model().rowsRemoved.connect(self._reindex_list_items)

        self.annotation_canvas = self._iface.mapCanvas()

    def _save_vertices_to_layer(self) -> None:
        """Saves the vertices list to a temp layer"""
        items = [
            self.routing_fromline_list.item(x).text()
            for x in range(self.routing_fromline_list.count())
        ]

        if len(items) > 0:
            point_layer = QgsVectorLayer(
                "point?crs=epsg:4326&field=ID:integer", "Vertices", "memory"
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
            self._iface.mapCanvas().refresh()

        self._iface.messageBar().pushMessage(
            "Success", "Vertices saved to layer.", level=Qgis.MessageLevel.Success
        )

    def _on_prov_refresh_click(self) -> None:
        """Populates provider dropdown with fresh list from config.yml"""

        providers = configmanager.read_config()["providers"]
        self.provider_combo.clear()
        for provider in providers:
            self.provider_combo.addItem(provider["name"], provider)

    def _on_clear_listwidget_click(self) -> None:
        """Clears the contents of the QgsListWidget and the annotations."""
        items = self.routing_fromline_list.selectedItems()
        if items:
            rows = [self.routing_fromline_list.row(item) for item in items]
            # if items are selected, only clear those
            for row in sorted(rows, reverse=True):
                if self.annotations:
                    self.project.annotationManager().removeAnnotation(self.annotations.pop(row))
                self.routing_fromline_list.takeItem(row)
        else:
            # else clear all items and annotations
            self.routing_fromline_list.clear()
            self._clear_annotations()

        # Remove blue lines (rubber band)
        if self.line_tool:
            self.line_tool.canvas.scene().removeItem(self.line_tool.rubberBand)

    def _linetool_annotate_point(
        self, point: QgsPointXY, idx: int, crs: Optional[QgsCoordinateReferenceSystem] = None
    ) -> QgsAnnotation:
        if not crs:
            crs = self._iface.mapCanvas().mapSettings().destinationCrs()

        annotation = QgsTextAnnotation()

        c = QTextDocument()
        html = "<strong>" + str(idx) + "</strong>"
        c.setHtml(html)

        annotation.setDocument(c)

        annotation.setFrameSizeMm(QSizeF(8, 5))
        annotation.setFrameOffsetFromReferencePointMm(QPointF(1.3, 1.3))
        annotation.setMapPosition(point)
        annotation.setMapPositionCrs(crs)

        return QgsMapCanvasAnnotationItem(annotation, self.annotation_canvas).annotation()

    def _clear_annotations(self) -> None:
        """Clears annotations"""
        for annotation_item in self.annotation_canvas.annotationItems():
            annotation = annotation_item.annotation()
            if annotation in self.project.annotationManager().annotations():
                self.project.annotationManager().removeAnnotation(annotation)
        self.annotations = []

    def _on_linetool_init(self) -> None:
        """Hides GUI dialog, inits line maptool and add items to line list box."""
        # Remove blue lines (rubber band)
        if self.line_tool:
            self.line_tool.canvas.scene().removeItem(self.line_tool.rubberBand)

        self.hide()
        self.routing_fromline_list.clear()
        # Remove all annotations which were added (if any)
        self._clear_annotations()

        self.line_tool = maptools.LineTool(self._iface.mapCanvas())
        self._iface.mapCanvas().setMapTool(self.line_tool)
        self.line_tool.pointDrawn.connect(
            lambda point, idx: self._on_linetool_map_click(point, idx)
        )
        self.line_tool.doubleClicked.connect(self._on_linetool_map_doubleclick)

    def _on_linetool_map_click(self, point: QgsPointXY, idx: int) -> None:
        """Adds an item to QgsListWidget and annotates the point in the map canvas"""
        map_crs = self._iface.mapCanvas().mapSettings().destinationCrs()

        transformer = transform.transformToWGS(map_crs)
        point_wgs = transformer.transform(point)
        self.routing_fromline_list.addItem(f"Point {idx}: {point_wgs.x():.6f}, {point_wgs.y():.6f}")

        annotation = self._linetool_annotate_point(point, idx)
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
        for idx, x in enumerate(items):
            coords = x.split(":")[1]
            item = f"Point {idx}:{coords}"
            x, y = (float(i) for i in coords.split(", "))
            point = QgsPointXY(x, y)

            self.routing_fromline_list.addItem(item)
            annotation = self._linetool_annotate_point(point, idx, crs)
            self.project.annotationManager().addAnnotation(annotation)

    def _on_linetool_map_doubleclick(self) -> None:
        """
        Populate line list widget with coordinates, end line drawing and show dialog again.
        """

        self.line_tool.pointDrawn.disconnect()
        self.line_tool.doubleClicked.disconnect()
        QApplication.restoreOverrideCursor()
        self._iface.mapCanvas().setMapTool(self.last_maptool)
        self.show()
