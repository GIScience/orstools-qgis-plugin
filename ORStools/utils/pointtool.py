# -*- coding: utf-8 -*-
"""
/***************************************************************************
 OSMtools
                                 A QGIS plugin
 falk
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

import os.path

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QCursor, QPixmap
from PyQt5.QtWidgets import QApplication

from qgis.core import (QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform,
                       QgsProject)
from qgis.gui import QgsMapTool

from ORStools import ICON_DIR


class PointTool(QgsMapTool):   
    def __init__(self, canvas, button):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.button = button
        self.cursor = QCursor(QPixmap(os.path.join(ICON_DIR, 'icon_locate.png')).scaledToWidth(48), 24, 24)
        
        #QApplication.setOverrideCursor(QCursor(QPixmap('/icon_locate.png')))
    
    canvasClicked = pyqtSignal(['QgsPointXY', 'QString'])
    def canvasReleaseEvent(self, event):
        #Get the click and emit a transformed point
        
        # mapSettings() was only introduced in QGIS 2.4, keep compatibility
        try:
            crsSrc = self.canvas.mapSettings().destinationCrs()
        except:
            crsSrc = self.canvas.mapRenderer().destinationCrs()
            
        crsWGS = QgsCoordinateReferenceSystem(4326)
    
        point_oldcrs = event.mapPoint()
        
        xform = QgsCoordinateTransform(crsSrc, crsWGS, QgsProject.instance())
        point_newcrs = xform.transform(point_oldcrs)
        
        QApplication.restoreOverrideCursor()
        
        self.canvasClicked.emit(point_newcrs, self.button)

    def activate(self):
        QApplication.setOverrideCursor(self.cursor)
