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
import math

from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand
from qgis.core import (
    QgsProject,
    QgsPointXY,
    QgsCoordinateReferenceSystem,
    Qgis,
    QgsCoordinateTransform,
    QgsWkbTypes,
    QgsAnnotation,
    QgsMarkerSymbol,
)
from qgis.PyQt.QtCore import Qt, pyqtSignal, QEvent
from qgis.PyQt.QtGui import QColor, QMouseEvent
from qgis.PyQt.QtWidgets import (
    QApplication,
)

from ORStools import ROUTE_COLOR
from ORStools.utils import transform, router
from ORStools.utils.exceptions import ApiError


class LineTool(QgsMapToolEmitPoint):
    """Line Map tool to capture mapped lines."""

    def __init__(self, dlg):
        """
        :param canvas: current map canvas
        :type canvas: QgsMapCanvas
        """
        self.dlg = dlg
        QgsMapToolEmitPoint.__init__(self, self.dlg.canvas)

        self.crsSrc = self.dlg.canvas.mapSettings().destinationCrs()
        self.previous_point = None
        self.points = []
        self.last_point = None
        self.reset()

        # connect live preview button to reload rubber band
        self.dlg.toggle_preview.toggled.connect(self._toggle_preview)

        # connect profile enums to reload rubber band
        self.dlg.routing_preference_combo.currentIndexChanged.connect(self._toggle_preview)
        self.dlg.routing_travel_combo.currentIndexChanged.connect(self._toggle_preview)

        self.pointPressed.connect(lambda point: self._on_movetool_map_press(point))
        self.pointReleased.connect(lambda event, idx: self._on_movetool_map_release(event, idx))
        self.mouseMoved.connect(lambda pos: self.change_cursor_on_hover(pos))

        self.last_click = "single-click"
        self.moving = None
        self.moved_idxs = 0
        self.error_idxs = 0
        self.click_dist = 25
        self.move_i = 0
        self.idx = 0

    def reset(self):
        """reset rubber band and captured points."""
        self.last_point = None
        self.points = []

    pointReleased = pyqtSignal(["QEvent", "int"])

    doubleClicked = pyqtSignal()

    def deactivate(self):
        super(LineTool, self).deactivate()
        self.deactivated.emit()

    pointPressed = pyqtSignal(["QPoint"])

    mouseMoved = pyqtSignal(["QPoint"])

    def canvasMoveEvent(self, e: QEvent) -> None:
        hovering = self.check_annotation_hover(e.pos())
        if hovering:
            QApplication.setOverrideCursor(Qt.OpenHandCursor)
        else:
            if not self.moving:
                QApplication.restoreOverrideCursor()

    def check_annotation_hover(self, pos: QMouseEvent) -> int:
        click = [pos.x(), pos.y()]
        dists = {}
        for i, anno in enumerate(self.dlg.annotations):
            x, y = anno.mapPosition()
            point = self.dlg.canvas.getCoordinateTransform().transform(x, y)  # die ist es
            p = [point.x(), point.y()]

            distance = 0.0
            for j in range(len(click)):
                distance += (click[j] - p[j]) ** 2
            distance = math.sqrt(distance)

            if distance > 0:
                dists[distance] = anno
        if dists and min(dists) < self.click_dist:
            idx = dists[min(dists)]
            return idx

    def keyPressEvent(self, event: QEvent) -> None:
        if event.key() == Qt.Key_Escape:
            self.dlg._clear_listwidget()
        elif event.key() == Qt.Key_D:
            if self.last_point:
                index = int(self.last_point["annotation"].document().toPlainText())
                if self.dlg.annotations:
                    self.dlg.project.annotationManager().removeAnnotation(
                        self.dlg.annotations.pop(index)
                    )
                    self.dlg.routing_fromline_list.takeItem(index)
                    self.dlg._reindex_list_items()
                    self.last_point = None
                    self.error_idxs += 1
                    if self.dlg.annotations and self.points:
                        self.save_last_point(
                            self.points[index - 1], self.dlg.annotations[index - 1]
                        )
            if self.dlg.routing_fromline_list.count() < 1:
                self.dlg._clear_listwidget()

    def canvasPressEvent(self, event: QEvent) -> None:
        hovering = self.check_annotation_hover(event.pos())
        if hovering:
            self.mouseMoved.disconnect()
            QApplication.setOverrideCursor(Qt.ClosedHandCursor)
            if self.dlg.rubber_band:
                self.dlg.rubber_band.reset()
            self.move_i = self.dlg.annotations.index(hovering)
            self.dlg.project.annotationManager().removeAnnotation(
                self.dlg.annotations.pop(self.move_i)
            )
            self.moving = True

    def canvasReleaseEvent(self, event: QEvent) -> None:
        if event.button() == Qt.RightButton:
            self.dlg.show()
            return

        point = self.toMapCoordinates(event.pos())
        self.points.append(point)

        if self.last_click == "single-click":
            if self.moving:
                try:
                    self.moving = False
                    QApplication.restoreOverrideCursor()
                    crs = self.dlg.canvas.mapSettings().destinationCrs()

                    annotation = self.dlg._linetool_annotate_point(point, self.move_i, crs=crs)
                    self.dlg.annotations.insert(self.move_i, annotation)
                    self.dlg.project.annotationManager().addAnnotation(annotation)

                    transformer = transform.transformToWGS(crs)
                    point_wgs = transformer.transform(point)

                    items = [
                        self.dlg.routing_fromline_list.item(x).text()
                        for x in range(self.dlg.routing_fromline_list.count())
                    ]
                    backup = items.copy()
                    items[self.move_i] = (
                        f"Point {self.move_i}: {point_wgs.x():.6f}, {point_wgs.y():.6f}"
                    )

                    self.dlg.routing_fromline_list.clear()
                    for i, x in enumerate(items):
                        coords = x.split(":")[1]
                        item = f"Point {i}:{coords}"
                        self.dlg.routing_fromline_list.addItem(item)
                    self.create_rubber_band()
                    self.save_last_point(point, annotation)
                    self.mouseMoved.connect(lambda pos: self.change_cursor_on_hover(pos))

                except ApiError as e:
                    if self.get_error_code(e) == 2010:
                        self.moving = False
                        self.dlg.routing_fromline_list.clear()
                        for i, x in enumerate(backup):
                            coords = x.split(":")[1]
                            item = f"Point {i}:{coords}"
                            self.dlg.routing_fromline_list.addItem(item)
                        self.dlg._reindex_list_items()
                        self.radius_message_box()
                        self.mouseMoved.connect(lambda pos: self.change_cursor_on_hover(pos))
                    else:
                        raise e
                except Exception as e:
                    if "Connection refused" in str(e):
                        self.api_key_message_bar()
                    else:
                        raise e
            # Not moving release
            else:
                try:
                    if not self.dlg.isVisible():
                        self.idx -= self.error_idxs
                        self.dlg.create_vertex(point, self.idx)
                        self.idx += 1
                        self.error_idxs = 0

                        if self.dlg.routing_fromline_list.count() > 1:
                            self.create_rubber_band()
                            self.moving = False
                except ApiError as e:
                    if self.get_error_code(e) == 2010:
                        self.error_idxs += 1
                        num = len(self.dlg.routing_fromline_list) - 1

                        if num < 2:
                            self.dlg.routing_fromline_list.clear()
                            self.dlg._clear_annotations()
                        else:
                            self.dlg.routing_fromline_list.takeItem(num)
                            self.dlg._reindex_list_items()
                            self.create_rubber_band()

                        self.radius_message_box()
                    else:
                        raise e
                except Exception as e:
                    if "Connection refused" in str(e):
                        self.api_key_message_bar()
                    else:
                        raise e

        self.last_click = "single-click"

    def canvasDoubleClickEvent(self, e: QEvent) -> None:
        """
        Populate line list widget with coordinates, end point moving and show dialog again.
        """
        self.dlg.show()
        self.last_click = "double-click"

    def create_rubber_band(self) -> None:
        if self.dlg.rubber_band:
            self.dlg.rubber_band.reset()
        else:
            self.dlg.rubber_band = QgsRubberBand(self.dlg.canvas, QgsWkbTypes.LineGeometry)
        color = QColor(ROUTE_COLOR)
        color.setAlpha(100)
        self.dlg.rubber_band.setStrokeColor(color)
        self.dlg.rubber_band.setWidth(5)
        if self.dlg.toggle_preview.isChecked() and self.dlg.routing_fromline_list.count() > 1:
            route_layer = router.route_as_layer(self.dlg)
            if route_layer:
                feature = next(route_layer.getFeatures())
                self.dlg.rubber_band.addGeometry(feature.geometry(), route_layer)
                self.dlg.rubber_band.show()
            else:
                self.dlg._clear_annotations()
        else:
            dest_crs = self.dlg.canvas.mapSettings().destinationCrs()
            original_crs = QgsCoordinateReferenceSystem("EPSG:4326")
            transform = QgsCoordinateTransform(original_crs, dest_crs, QgsProject.instance())
            items = [
                self.dlg.routing_fromline_list.item(x).text()
                for x in range(self.dlg.routing_fromline_list.count())
            ]
            split = [x.split(":")[1] for x in items]
            coords = [tuple(map(float, coord.split(", "))) for coord in split]
            points_xy = [QgsPointXY(x, y) for x, y in coords]
            reprojected_point = [transform.transform(point) for point in points_xy]
            for point in reprojected_point:
                if point == reprojected_point[-1]:
                    self.dlg.rubber_band.addPoint(point, True)
                else:
                    self.dlg.rubber_band.addPoint(point, False)
            self.dlg.rubber_band.show()

    def get_error_code(self, e: QEvent) -> int:
        json_start_index = e.message.find("{")
        json_end_index = e.message.rfind("}") + 1
        json_str = e.message[json_start_index:json_end_index]
        error_dict = json.loads(json_str)
        return error_dict["error"]["code"]

    def radius_message_box(self) -> None:
        self.dlg._iface.messageBar().pushMessage(
            self.tr("Please use a different point"),
            self.tr("""Could not find routable point within a radius of 350.0 meters of specified coordinate. 
            Use a different point closer to a road."""),
            level=Qgis.MessageLevel.Warning,
            duration=3,
        )

    def api_key_message_bar(self) -> None:
        self.dlg._iface.messageBar().pushMessage(
            self.tr("Connection refused"),
            self.tr("""Are your provider settings correct and the provider ready?"""),
            level=Qgis.MessageLevel.Warning,
            duration=3,
        )

    def _toggle_preview(self) -> None:
        if self.dlg.routing_fromline_list.count() > 0:
            state = not self.dlg.toggle_preview.isChecked()
            try:
                self.create_rubber_band()
            except ApiError as e:
                self.dlg.toggle_preview.setChecked(state)
                if self.get_error_code(e) == 2010:
                    self.radius_message_box()
                else:
                    raise e
            except Exception as e:
                self.toggle_preview.setChecked(state)
                if "Connection refused" in str(e):
                    self.api_key_message_bar()
                else:
                    raise e

    def save_last_point(self, point: QgsPointXY, annotation: QgsAnnotation) -> None:
        """Saves tha last point and makes it deletable."""
        self.last_point = {"point": point, "annotation": annotation}

        for old_annotation in self.dlg.annotations:
            color = old_annotation.markerSymbol().symbolLayer(0).color().name()
            if color == "#ffff00":
                symbol = QgsMarkerSymbol.createSimple({"color": "red"})
                old_annotation.setMarkerSymbol(symbol)

        symbol = QgsMarkerSymbol.createSimple({"color": "yellow"})
        annotation.setMarkerSymbol(symbol)
