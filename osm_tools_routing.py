# -*- coding: utf-8 -*-
"""
Created on Wed Feb 08 21:14:48 2017

@author: nnolde
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import * 
import qgis.utils

import requests
import xml.etree.ElementTree as ET
import os.path
import re
import itertools

import osm_tools_pointtool

class routing:
    def __init__(self, dlg):
        self.dlg = dlg
        self.url = r"http://openls.geog.uni-heidelberg.de/route?"
        self.ns = {'gml': 'http://www.opengis.net/gml',
                  'xls': "http://www.opengis.net/xls",
                  'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
        
        # GUI init
        self.dlg.start_layer.clear()
        self.dlg.end_layer.clear()
        self.dlg.mode_travel.clear()
        self.dlg.mode_routing.clear()
        self.dlg.mode_travel.addItem('Car')
        self.dlg.mode_travel.addItem('Bicycle')
        self.dlg.mode_travel.addItem('Pedestrian')
        self.dlg.mode_travel.addItem('HeavyVehicle')
        self.dlg.mode_routing.addItem('Fastest')
        self.dlg.mode_routing.addItem('Shortest')
        
        for layer in qgis.utils.iface.legendInterface().layers():
            layerType = layer.type()
            if layerType == QgsMapLayer.VectorLayer and layer.wkbType() == QGis.WKBPoint:
                self.dlg.start_layer.addItem(layer.name())
                self.dlg.end_layer.addItem(layer.name())
                
        self.layer_start = None
        self.layer_end = None
        
        self.startPopBox()
        self.endPopBox()
                  
        # API parameters
        self.api_key = self.dlg.api_key.text()
        self.mode_travel = self.dlg.mode_travel.currentText()
        self.mode_routing = self.dlg.mode_routing.currentText()
        self.speed_max = self.dlg.speed_max.value()
        
        self.iface = qgis.utils.iface
        
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Connect events to signals
        self.dlg.start_radio_map.toggled.connect(self.startPopBox)
        self.dlg.end_radio_map.toggled.connect(self.endPopBox)
        self.dlg.start_layer.currentIndexChanged.connect(self.startPopBox)
        self.dlg.end_layer.currentIndexChanged.connect(self.endPopBox)
        self.dlg.mode_travel.currentIndexChanged.connect(self.valueChanged)
        self.dlg.mode_routing.currentIndexChanged.connect(self.valueChanged)
        self.dlg.speed_max.valueChanged.connect(self.valueChanged)
        self.dlg.add_start_button.clicked.connect(self.initMapTool)
        self.dlg.add_end_button.clicked.connect(self.initMapTool)
        self.dlg.add_via_button.clicked.connect(self.initMapTool)
        self.dlg.add_via_button_clear.clicked.connect(self.clearVia)
        self.dlg.api_key.textChanged.connect(self.keyWriter)
    
    def clearVia(self):
        self.dlg.add_via.setText("Long,Lat")
    
    def startPopBox(self):
        if self.dlg.start_radio_layer.isChecked():
            self.dlg.add_start_button.setEnabled(False)
            self.dlg.start_layer.setEnabled(True)
            self.dlg.start_layer_id.setEnabled(True)
            self.dlg.start_layer_id.clear()
            layer_list = [lyr for lyr in QgsMapLayerRegistry.instance().mapLayers().values() if lyr.name() == self.dlg.start_layer.currentText()]
            if layer_list:
                layer_selected = layer_list[0]
                fields_selected = layer_selected.fields()
                for field in fields_selected:
                    self.dlg.start_layer_id.addItem(field.name())
                
            # Determine selected layer
            for layer in qgis.utils.iface.legendInterface().layers():
                if layer.name() == self.dlg.start_layer.currentText():
                    self.layer_start = layer
                    break
        else:
            self.dlg.start_layer_id.setEnabled(False)
            self.dlg.start_layer.setEnabled(False)
            self.dlg.add_start_button.setEnabled(True)
            
        if self.dlg.end_radio_layer.isChecked() and self.dlg.start_radio_layer.isChecked():
            self.dlg.radio_one.setEnabled(True)
            self.dlg.radio_many.setEnabled(True)
        else:
            self.dlg.radio_one.setEnabled(False)
            self.dlg.radio_many.setEnabled(False)
            
        return
    
        
    def endPopBox(self):
        if self.dlg.end_radio_layer.isChecked():
            self.dlg.add_end_button.setEnabled(False)
            self.dlg.end_layer.setEnabled(True)
            self.dlg.end_layer_id.setEnabled(True)
            self.dlg.end_layer_id.clear()
            layer_list = [lyr for lyr in QgsMapLayerRegistry.instance().mapLayers().values() if lyr.name() == self.dlg.end_layer.currentText()]
            if layer_list:
                layer_selected = layer_list[0]
                fields_selected = layer_selected.fields()
                for field in fields_selected:
                    self.dlg.end_layer_id.addItem(field.name())
                    
            # Determine selected layer
            for layer in qgis.utils.iface.legendInterface().layers():
                if layer.name() == self.dlg.end_layer.currentText():
                    self.layer_end = layer
                    break            
        else:
            self.dlg.end_layer_id.setEnabled(False)
            self.dlg.end_layer.setEnabled(False)
            self.dlg.add_end_button.setEnabled(True)
        
        if self.dlg.end_radio_layer.isChecked() and self.dlg.start_radio_layer.isChecked():
            self.dlg.radio_one.setEnabled(True)
            self.dlg.radio_many.setEnabled(True)
        else:
            self.dlg.radio_one.setEnabled(False)
            self.dlg.radio_many.setEnabled(False)
            
        return
        
    
    # Event for GUI Signals
    def valueChanged(self):
        self.mode_travel = self.dlg.mode_travel.currentText()
        self.mode_routing = self.dlg.mode_routing.currentText()
        self.speed_max = self.dlg.speed_max.value()
        
    
    # Event for API key change
    def keyWriter(self):
        with open(os.path.join(self.script_dir, "apikey.txt"), 'w') as key:
            self.api_key = self.dlg.api_key.text()
            return key.write(self.dlg.api_key.text())
            
    
    # Connect to PointTool and set as mapTool
    def initMapTool(self):
        sending_button = self.dlg.sender().objectName() 
        self.mapTool = osm_tools_pointtool.PointTool(qgis.utils.iface.mapCanvas(), sending_button)        
        self.iface.mapCanvas().setMapTool(self.mapTool)     
        self.mapTool.canvasClicked.connect(self.writeText)

        
    # Write map coordinates to text fields
    def writeText(self, point, button):
        x, y = point
        
        if button == self.dlg.add_start_button.objectName():
            self.dlg.add_start.setText("{0:.5f},{1:.5f}".format(x, y))
            
        if button == self.dlg.add_end_button.objectName():
            self.dlg.add_end.setText("{0:.5f},{1:.5f}".format(x, y))
            
        if button == self.dlg.add_via_button.objectName():
            self.dlg.add_via.setText("{0:.5f},{1:.5f}\n".format(x, y))
            
        
    def route(self):
        
#        if osm_tools.CheckCRS(self, self.layer_start.crs().authid()) == False:
#            return
#        if osm_tools.CheckCRS(self, self.layer_end.crs().authid()) == False:
#            return
        
        # Create memory routing layer with fields
        layer_out = QgsVectorLayer("LineString?crs=EPSG:4326", "Route", "memory")
        layer_out_prov = layer_out.dataProvider()
        layer_out_prov.addAttributes([QgsField("DISTANCE", QVariant.Double)])
        layer_out_prov.addAttributes([QgsField("TIME_H", QVariant.Int)])
        layer_out_prov.addAttributes([QgsField("TIME_MIN", QVariant.Int)])
        layer_out_prov.addAttributes([QgsField("TIME_SEC", QVariant.Int)])
        layer_out_prov.addAttributes([QgsField("MODE", QVariant.String)])
        layer_out_prov.addAttributes([QgsField("PREF", QVariant.String)])
        #layer_out_prov.addAttributes([QgsField("SPEED_MAX", QVariant.String)])
        layer_out_prov.addAttributes([QgsField("FROM_LAT", QVariant.Double)])
        layer_out_prov.addAttributes([QgsField("FROM_LONG", QVariant.Double)])
        layer_out_prov.addAttributes([QgsField("TO_LAT", QVariant.Double)])
        layer_out_prov.addAttributes([QgsField("TO_LONG", QVariant.Double)])
        layer_out_prov.addAttributes([QgsField("FROM_ID", QVariant.String)])
        layer_out_prov.addAttributes([QgsField("TO_ID", QVariant.String)])
        
        layer_out.updateFields()
        
        start_features = []
        end_features = []
        start_ids = []
        end_ids = []

        # Create start features
        if self.dlg.start_radio_layer.isChecked():
            start_feat = self.layer_start.getFeatures()
            field_id = self.layer_start.fieldNameIndex(self.dlg.start_layer_id.currentText())
            for feat in start_feat:
                x, y = feat.geometry().asPoint()
                start_features.append(",".join([str(x), str(y)]))
                start_ids.append(feat.attributes()[field_id])
        else:
            start_features.append(self.dlg.add_start.text())
            start_ids.append(self.dlg.add_start.text())
            
        # Create end features
        if self.dlg.end_radio_layer.isChecked():
            end_feat = self.layer_end.getFeatures()
            field_id = self.layer_end.fieldNameIndex(self.dlg.end_layer_id.currentText())
            for feat in end_feat:
                x, y = feat.geometry().asPoint()
                end_features.append(",".join([str(x), str(y)]))
                end_ids.append(feat.attributes()[field_id])
        else:
            end_features.append(self.dlg.add_end.text())
            end_ids.append(self.dlg.add_end.text())
            
        # Rules for creating routing features
        if len(start_features) == 1:
            if len(end_features) == 1:
                route_features = zip(start_features, end_features)
                route_ids = zip(start_ids, end_ids)
            else:
                route_features = zip(itertools.cycle(start_features), end_features)
                route_ids = zip(itertools.cycle(start_ids), end_ids)
        else:
            if len(end_features) == 1:
                route_features = zip(start_features, itertools.cycle(end_features))
                route_ids = zip(start_ids, itertools.cycle(end_ids))
            else:
                if self.dlg.radio_one.isChecked():
                    route_features = zip(start_features, end_features)
                    route_ids = zip(start_ids, end_ids)
                else:
                    route_features = list(itertools.product(start_features, end_features))
                    route_ids = list(itertools.product(start_ids, end_ids))

        # Read route details from GUI
        route_via = " ".join(self.dlg.add_via.text().split("\n")[:-1])
        
        # Set up progress bar
        route_count = len(route_features)
        progressMessageBar = self.iface.messageBar().createMessage("Requesting routes from ORS...")
        progress = QProgressBar()
        progress.setMaximum(route_count)
        progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        progressMessageBar.layout().addWidget(progress)
        self.iface.messageBar().pushWidget(progressMessageBar, self.iface.messageBar().INFO)
        
        for i, route in enumerate(route_features):
            # Skip route if start and end are identical
            if route[0] == route[1]:
                continue
            else:
                try:
                    # Create URL
                    req = "{}api_key={}&start={}&end={}&routepref={}&weighting={}&maxspeed={}&instructions=False".format(self.url, 
                                                        self.api_key, 
                                                        route[0],
                                                        route[1],
                                                        self.mode_travel,
                                                        self.mode_routing,
                                                        self.speed_max
                                                        )
                    print req
                    if route_via != "":
                        req += "&via={}".format(route_via)
                        
                    # Get response from API and read into element tree
                    response = requests.get(req)
                    root = ET.fromstring(response.content)
                    access_path = root.find("xls:Response/"
                                            "xls:DetermineRouteResponse",
                                            self.ns)
                    
                    feat_out = QgsFeature()
                    
                    # Read all coordinates
                    coords_list = []
                    for coords in access_path.findall("xls:RouteGeometry/gml:LineString/gml:pos", self.ns):
                        coords_tuple = tuple([float(coord) for coord in coords.text.split(" ")])
                        qgis_coords = QgsPoint(coords_tuple[0], coords_tuple[1])
                        coords_list.append(qgis_coords)
                    
                    # Read total time
                    time_path = access_path.find("xls:RouteSummary/xls:TotalTime", self.ns)
                    time_text = time_path.text
                    if 'D' not in time_text:
                        time_text = re.sub(r'(P)', r'P0D', time_text)
                    if 'H' not in time_text:
                        time_text = re.sub(r'(T)', r'T0H', time_text)
                    if 'M' not in time_text:
                        time_text = re.sub(r'(H)', r'H0M', time_text)
                    
                    time_list = list(reversed(re.split('DT|H|M', time_text[1:-1])))
                    while len(time_list) < 4:
                        time_list.append('0')
                    secs, mins, hours, days = [int(x) for x in time_list]
                    hours += (days*24)
                    #hours = "{0:.3f}".format(hours)
                                         
                    # Read total distance
                    distance = float(access_path.find("xls:RouteSummary/xls:TotalDistance", self.ns).get("value"))
                    
                    # Read X and Y
                    route_start_x, route_start_y = [float(coord) for coord in route[0].split(",")]
                    route_end_x, route_end_y = [float(coord) for coord in route[1].split(",")]
                        
                    # Set feature geometry and attributes
                    feat_out.setGeometry(QgsGeometry.fromPolyline(coords_list))
                    feat_out.setAttributes([distance,
                                            hours,
                                            mins,
                                            secs,
                                            self.mode_travel,
                                            self.mode_routing,
                                            route_start_y,
                                            route_start_x,
                                            route_end_y,
                                            route_end_x,
                                            route_ids[i][0],
                                            route_ids[i][1]]) 
                    
                    layer_out_prov.addFeatures([feat_out])
                    
                    progress.setValue(i)    
                except (AttributeError, TypeError):
                    msg = "Request is not valid! Check parameters. TIP: Coordinates must plot within 1 km of a road."
                    qgis.utils.iface.messageBar().pushMessage(msg, level = qgis.gui.QgsMessageBar.CRITICAL)
                    return
                
        layer_out.updateExtents()

        QgsMapLayerRegistry.instance().addMapLayer(layer_out)