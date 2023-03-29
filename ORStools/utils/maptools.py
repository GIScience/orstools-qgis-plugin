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

from qgis.core import (QgsWkbTypes)
from qgis.gui import (QgsMapToolEmitPoint,
                      QgsRubberBand)

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QColor

from ORStools import DEFAULT_COLOR


class LineTool(QgsMapToolEmitPoint):
    """Line Map tool to capture mapped lines."""

    def __init__(self, canvas):
        """
        :param canvas: current map canvas
        :type canvas: QgsMapCanvas
        """
        self.canvas = canvas
        QgsMapToolEmitPoint.__init__(self, self.canvas)

        self.rubberBand = QgsRubberBand(mapCanvas=self.canvas, geometryType=QgsWkbTypes.LineGeometry)
        self.rubberBand.setStrokeColor(QColor(DEFAULT_COLOR))
        self.rubberBand.setWidth(3)

        self.crsSrc = self.canvas.mapSettings().destinationCrs()
        self.previous_point = None
        self.points = []
        self.reset()

    def reset(self):
        """reset rubber band and captured points."""

        self.points = []
        self.rubberBand.reset(geometryType=QgsWkbTypes.LineGeometry)

    pointDrawn = pyqtSignal(["QgsPointXY", "int"])
    def canvasReleaseEvent(self, e):
        """Add marker to canvas and shows line."""
        new_point = self.toMapCoordinates(e.pos())
        self.points.append(new_point)

        # noinspection PyUnresolvedReferences
        self.pointDrawn.emit(new_point, self.points.index(new_point))
        self.showLine()

    def showLine(self):
        """Builds rubber band from all points and adds it to the map canvas."""
        self.rubberBand.reset(geometryType=QgsWkbTypes.LineGeometry)
        for point in self.points:
            if point == self.points[-1]:
                self.rubberBand.addPoint(point, True)
            self.rubberBand.addPoint(point, False)
        self.rubberBand.show()

    doubleClicked = pyqtSignal()

    # noinspection PyUnusedLocal
    def canvasDoubleClickEvent(self, e):
        """Ends line drawing and deletes rubber band and markers from map canvas."""
        # noinspection PyUnresolvedReferences
        self.doubleClicked.emit()
        self.canvas.scene().removeItem(self.rubberBand)

    def deactivate(self):
        super(LineTool, self).deactivate()
        self.deactivated.emit()


# class PointTool(QgsMapToolEmitPoint):
#     """Point Map tool to capture mapped coordinates."""
#
#     def __init__(self, canvas, button):
#         """
#         :param canvas: current map canvas
#         :type: QgsMapCanvas
#
#         :param button: name of 'Map!' button pressed.
#         :type button: str
#         """
#
#         QgsMapToolEmitPoint.__init__(self, canvas)
#         self.canvas = canvas
#         self.button = button
#         self.cursor = QCursor(QPixmap(RESOURCE_PREFIX + 'icon_locate.png').scaledToWidth(48), 24, 24)
#
#     canvasClicked = pyqtSignal(['QgsPointXY', 'QString'])
#     def canvasReleaseEvent(self, event):
#         #Get the click and emit a transformed point
#
#         crsSrc = self.canvas.mapSettings().destinationCrs()
#
#         point_oldcrs = event.mapPoint()
#
#         xform = transform.transformToWGS(crsSrc)
#         point_newcrs = xform.transform(point_oldcrs)
#
#         QApplication.restoreOverrideCursor()
#
#         self.canvasClicked.emit(point_newcrs, self.button)
#
#     def activate(self):
#         QApplication.setOverrideCursor(self.cursor)
