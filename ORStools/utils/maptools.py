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
from qgis._gui import QgsMapCanvas, QgsMapMouseEvent
from qgis.core import QgsWkbTypes
from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor

from ORStools import DEFAULT_COLOR


class LineTool(QgsMapToolEmitPoint):
    """Line Map tool to capture mapped lines."""

    def __init__(self, canvas: QgsMapCanvas) -> None:
        """
        :param canvas: current map canvas
        :type canvas: QgsMapCanvas
        """
        self.canvas = canvas
        QgsMapToolEmitPoint.__init__(self, self.canvas)

        self.rubberBand = QgsRubberBand(
            mapCanvas=self.canvas, geometryType=QgsWkbTypes.LineGeometry
        )
        self.rubberBand.setStrokeColor(QColor(DEFAULT_COLOR))
        self.rubberBand.setWidth(3)

        self.crsSrc = self.canvas.mapSettings().destinationCrs()
        self.previous_point = None
        self.points = []
        self.reset()

    def reset(self) -> None:
        """reset rubber band and captured points."""

        self.points = []
        self.rubberBand.reset(geometryType=QgsWkbTypes.LineGeometry)

    pointDrawn = pyqtSignal(["QgsPointXY", "int"])

    def canvasReleaseEvent(self, e: QgsMapMouseEvent) -> None:
        """Add marker to canvas and shows line."""
        new_point = self.toMapCoordinates(e.pos())
        self.points.append(new_point)

        # noinspection PyUnresolvedReferences
        self.pointDrawn.emit(new_point, self.points.index(new_point))
        self.showLine()

    def showLine(self) -> None:
        """Builds rubber band from all points and adds it to the map canvas."""
        self.rubberBand.reset(geometryType=QgsWkbTypes.LineGeometry)
        for point in self.points:
            if point == self.points[-1]:
                self.rubberBand.addPoint(point, True)
            self.rubberBand.addPoint(point, False)
        self.rubberBand.show()

    doubleClicked = pyqtSignal()

    # noinspection PyUnusedLocal
    def canvasDoubleClickEvent(self, e: QgsMapMouseEvent) -> None:
        """Ends line drawing and deletes rubber band and markers from map canvas."""
        # noinspection PyUnresolvedReferences
        self.doubleClicked.emit()
        self.canvas.scene().removeItem(self.rubberBand)

    def deactivate(self) -> None:
        super(LineTool, self).deactivate()
        self.deactivated.emit()
