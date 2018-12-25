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

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QCursor, QPixmap, QColor
from PyQt5.QtWidgets import QApplication

from qgis.core import QgsWkbTypes
from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand, QgsVertexMarker

from ORStools import RESOURCE_PREFIX, DEFAULT_COLOR
from ORStools.utils import transform


class PointTool(QgsMapToolEmitPoint):
    """Point Map tool to capture mapped coordinates."""

    def __init__(self, canvas, button):
        """
        :param canvas: current map canvas
        :type: QgsMapCanvas

        :param button: name of 'Map!' button pressed.
        :type button: str
        """
        QgsMapToolEmitPoint.__init__(self, canvas)
        self.canvas = canvas
        self.button = button
        self.cursor = QCursor(QPixmap(RESOURCE_PREFIX + 'icon_locate.png').scaledToWidth(48), 24, 24)
    
    canvasClicked = pyqtSignal(['QgsPointXY', 'QString'])
    def canvasReleaseEvent(self, event):
        #Get the click and emit a transformed point
        
        # mapSettings() was only introduced in QGIS 2.4, keep compatibility
        crsSrc = self.canvas.mapSettings().destinationCrs()
    
        point_oldcrs = event.mapPoint()
        
        xform = transform.transformToWGS(crsSrc)
        point_newcrs = xform.transform(point_oldcrs)
        
        QApplication.restoreOverrideCursor()
        
        self.canvasClicked.emit(point_newcrs, self.button)

    def activate(self):
        QApplication.setOverrideCursor(self.cursor)


class LineTool(QgsMapToolEmitPoint):
    """Line Map tool to capture mapped lines."""

    def __init__(self, canvas):
        """
        :param canvas: current map canvas
        :type canvas: QgsMapCanvas
        """
        self.canvas = canvas
        QgsMapToolEmitPoint.__init__(self, self.canvas)

        self.rubberBand = QgsRubberBand(self.canvas, False)
        self.rubberBand.setStrokeColor(QColor(DEFAULT_COLOR))
        self.rubberBand.setWidth(3)

        crsSrc = self.canvas.mapSettings().destinationCrs()
        self.transformer = transform.transformToWGS(crsSrc)
        self.previous_point = None
        self.points = []
        self.markers = []
        self.reset()

    def reset(self):
        """reset rubberband and captured points."""
        self.points = []
        # self.isEmittingPoint = False
        self.rubberBand.reset(QgsWkbTypes.LineGeometry)

    def add_marker(self, point):
        """
        Adds a clicked marker to the map canvas.

        :param point: point clicked by the user.
        :type point: QgsPointXY
        """
        new_marker = QgsVertexMarker(self.canvas)
        new_marker.setCenter(point)
        new_marker.setIconType(QgsVertexMarker.ICON_CROSS)
        new_marker.setIconSize(10)
        new_marker.setFillColor(QColor('#485bea'))
        new_marker.setColor(QColor('#000000'))

        self.markers.append(new_marker)

    pointDrawn = pyqtSignal(["QgsPointXY", "int"])
    def canvasReleaseEvent(self, e):
        """Add marker to canvas and shows line."""
        new_point = self.toMapCoordinates(e.pos())
        self.add_marker(new_point)

        self.points.append(new_point)
        self.pointDrawn.emit(self.transformer.transform(new_point), self.points.index(new_point))
        self.showLine()

    def showLine(self):
        """Builds rubberband from all points and adds it to the map canvas."""
        self.rubberBand.reset(QgsWkbTypes.LineGeometry)
        for point in self.points:
            if point == self.points[-1]:
                self.rubberBand.addPoint(point, True)
            self.rubberBand.addPoint(point, False)
        self.rubberBand.show()

    doubleClicked = pyqtSignal(['int'])
    def canvasDoubleClickEvent(self, e):
        """Ends line drawing and deletes rubberband and markers from map canvas."""
        self.doubleClicked.emit(len(self.points))
        self.canvas.scene().removeItem(self.rubberBand)
        if self.markers:
            for marker in self.markers:
                self.canvas.scene().removeItem(marker)

    def deactivate(self):
        super(LineTool, self).deactivate()
        self.deactivated.emit()
