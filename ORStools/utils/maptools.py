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

from qgis.gui import QgsMapToolEmitPoint

from PyQt5.QtCore import pyqtSignal


class LineTool(QgsMapToolEmitPoint):
    """Line Map tool to capture mapped lines."""

    def __init__(self, canvas):
        """
        :param canvas: current map canvas
        :type canvas: QgsMapCanvas
        """
        self.canvas = canvas
        QgsMapToolEmitPoint.__init__(self, self.canvas)

        self.crsSrc = self.canvas.mapSettings().destinationCrs()
        self.previous_point = None
        self.points = []
        self.reset()

    def reset(self):
        """reset rubber band and captured points."""

        self.points = []
        # self.rubberBand.reset(geometryType=QgsWkbTypes.LineGeometry)

    pointReleased = pyqtSignal(["QgsPointXY", "int"])

    def canvasReleaseEvent(self, e):
        """Add marker to canvas and shows line."""
        new_point = self.toMapCoordinates(e.pos())
        self.points.append(new_point)

        # noinspection PyUnresolvedReferences
        self.pointReleased.emit(new_point, self.points.index(new_point))

    # noinspection PyUnusedLocal
    def canvasDoubleClickEvent(self, e):
        """Ends line drawing and deletes rubber band and markers from map canvas."""
        # noinspection PyUnresolvedReferences
        self.doubleClicked.emit()
        self.canvas.scene().removeItem(self.rubberBand)
        del self.rubberBand
        # self.canvas.scene().removeItem(self.rubberBand)

    doubleClicked = pyqtSignal()

    def deactivate(self):
        super(LineTool, self).deactivate()
        self.deactivated.emit()

    pointPressed = pyqtSignal(["QPoint"])

    def canvasPressEvent(self, e):
        # Make tooltip look like marker
        self.pointPressed.emit(e.pos())

    mouseMoved = pyqtSignal(["QPoint"])

    def canvasMoveEvent(self, e):
        self.mouseMoved.emit(e.pos())
