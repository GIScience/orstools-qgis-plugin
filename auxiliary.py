# -*- coding: utf-8 -*-
"""
Created on Thu May 04 09:38:00 2017

@author: nnolde
"""
import os.path
import yaml

from PyQt4.QtGui import QProgressBar
from PyQt4.QtCore import Qt

from qgis.core import (QgsVectorLayer,
                       QGis,
                       QgsCoordinateTransform,
                       QgsCoordinateReferenceSystem,
                       QgsProject)

script_dir = os.path.dirname(os.path.abspath(__file__))

def checkCRS(layer, messageBar):
    """
    Check if layer CRS is EPSG:4326.
    
    :param layer: Layer to be inspected.
    :type layer: QgsMapLayer
    
    :param messageBar: QGIS interface message bar.
    :type messageBar: QgsMessageBar
    """
    layer_crs = layer.crs().authid()
    if layer_crs.split(':')[1] != '4326':
        layer = transformToWGS(layer, layer_crs)
        messageBar.pushInfo('CRS conflict',
                                         'The input layer CRS is {}, the output layer '
                                         'CRS will be EPSG:4326'.format(layer_crs))
    
    return layer

def transformToWGS(old_layer, old_crs):
    new_layer = QgsVectorLayer("Polygon?crs=EPSG:4326", old_layer.name(), "memory")
    new_crs = QgsCoordinateReferenceSystem(4326)
    old_crs = QgsCoordinateReferenceSystem(old_crs)
    xform = QgsCoordinateTransform(old_crs, new_crs, QgsProject.instance())
    feats = []
    for f in old_layer.getFeatures():
        g = f.geometry()
        g.transform(xform)
        f.setGeometry(g)
        feats.append(f)
    
    new_layer.dataProvider().addFeatures(feats)
    attrs = old_layer.dataProvider().fields().toList()
    new_layer.dataProvider().addAttributes(attrs)
    new_layer.updateFields()    
    
    return new_layer


def readConfig():
    with open(os.path.join(script_dir, "config.yml")) as f:
        doc = yaml.safe_load(f)
        
    return doc

def writeConfig(key, value):
    
    doc = readConfig()
    doc[key] = value
    with open(os.path.join(script_dir, "config.yml"), 'w') as f:
        yaml.safe_dump(doc, f)
        
        
def pushProgressBar(iface):
    progressMessageBar = iface.messageBar().createMessage("Requesting analysis from ORS...")
    progress = QProgressBar(progressMessageBar)
    progress.setMaximum(100)
    progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
    progressMessageBar.layout().addWidget(progress)
    iface.messageBar().pushWidget(progressMessageBar, level=Qgis.Info)
    
    return progress, progressMessageBar