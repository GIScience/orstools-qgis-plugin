# -*- coding: utf-8 -*-
"""
Created on Mon Feb 06 23:35:16 2017

@author: nnolde
"""
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QCursor, QPixmap,QApplication

from qgis.core import (QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform,
                       QgsProject)
from qgis.gui import QgsMapTool

import os

# Find cursor icon in plugin tree
def resolve(name, basepath=None):
    if not basepath:
      basepath = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(basepath, name)


class PointTool(QgsMapTool):
    def __init__(self, canvas, button):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.button = button
        self.imgdir = resolve('../icon_locate.png')
        self.cursor = QCursor(QPixmap(self.imgdir).scaledToWidth(24), 12, 12)

        #QApplication.setOverrideCursor(QCursor(QPixmap('../icon_locate.png')))

    canvasClicked = pyqtSignal(['QgsPoint', 'QString', 'Qt::MouseButton'])
    def canvasReleaseEvent(self, event):
        #Get the click and emit a transformed point

        # mapSettings() was only introduced in QGIS 2.4, keep compatibility
        try:
            crsSrc = self.canvas.mapSettings().destinationCrs()
        except:
            crsSrc = self.canvas.mapRenderer().destinationCrs()

        crsWGS = QgsCoordinateReferenceSystem(4326)

        point_oldcrs = self.toMapCoordinates(event.pos())

        xform = QgsCoordinateTransform(crsSrc, crsWGS)
        point_newcrs = xform.transform(point_oldcrs)

        QApplication.restoreOverrideCursor()

        self.canvasClicked.emit(point_newcrs, self.button, event.button())

    def activate(self):
        QApplication.setOverrideCursor(self.cursor)

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True
