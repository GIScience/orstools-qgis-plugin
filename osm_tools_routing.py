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
import os.path
import itertools
import json

import osm_tools_aux
import osm_tools_geocode
import osm_tools_pointtool

class routing:
    def __init__(self, dlg):
        self.dlg = dlg
        self.url = r"https://api.openrouteservice.org/directions?"
        
        # GUI init
        self.dlg.start_layer.clear()
        self.dlg.end_layer.clear()
        self.dlg.mode_travel.clear()
        self.dlg.mode_routing.clear()           
        self.dlg.mode_travel.addItem('driving-car')
        self.dlg.mode_travel.addItem('driving-hgv')
        self.dlg.mode_travel.addItem('cycling-regular')
        self.dlg.mode_travel.addItem('cycling-road')
        self.dlg.mode_travel.addItem('cycling-safe')
        self.dlg.mode_travel.addItem('cycling-mountain')
        self.dlg.mode_travel.addItem('cycling-tour')
        self.dlg.mode_travel.addItem('foot-walking')
        self.dlg.mode_travel.addItem('foot-hiking')
            
        self.dlg.mode_routing.addItem('fastest')
        self.dlg.mode_routing.addItem('shortest')
        
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
        
        self.iface = qgis.utils.iface
        
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Connect events to signals
        self.dlg.start_radio_map.toggled.connect(self.startPopBox)
        self.dlg.end_radio_map.toggled.connect(self.endPopBox)
        self.dlg.start_layer.currentIndexChanged.connect(self.startPopBox)
        self.dlg.end_layer.currentIndexChanged.connect(self.endPopBox)
        self.dlg.mode_travel.currentIndexChanged.connect(self.valueChanged)
        self.dlg.mode_routing.currentIndexChanged.connect(self.valueChanged)
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
        
    
    # Event for API key change
    def keyWriter(self):
        with open(os.path.join(self.script_dir, "apikey.txt"), 'w') as key:
            self.api_key = self.dlg.api_key.text()
            return key.write(self.dlg.api_key.text())
            
    
    # Connect to PointTool and set as mapTool
    def initMapTool(self):
        self.dlg.showMinimized()
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
            
        self.dlg.showNormal()
        
    def route(self):
        
        # Create memory routing layer with fields
        layer_out = QgsVectorLayer("LineString?crs=EPSG:4326", "Route_ORS", "memory")
        layer_out_prov = layer_out.dataProvider()
        layer_out_prov.addAttributes([QgsField("DISTANCE", QVariant.Double)])
        layer_out_prov.addAttributes([QgsField("TIME_H", QVariant.Int)])
        layer_out_prov.addAttributes([QgsField("TIME_MIN", QVariant.Int)])
        layer_out_prov.addAttributes([QgsField("TIME_SEC", QVariant.Int)])
        layer_out_prov.addAttributes([QgsField("MODE", QVariant.String)])
        layer_out_prov.addAttributes([QgsField("PREF", QVariant.String)])
        layer_out_prov.addAttributes([QgsField("FROM_ID", QVariant.String)])
        layer_out_prov.addAttributes([QgsField("TO_ID", QVariant.String)])
        layer_out_prov.addAttributes([QgsField("FROM_LAT", QVariant.Double)])
        layer_out_prov.addAttributes([QgsField("FROM_LONG", QVariant.Double)])
        layer_out_prov.addAttributes([QgsField("TO_LAT", QVariant.Double)])
        layer_out_prov.addAttributes([QgsField("TO_LONG", QVariant.Double)])
        
        layer_out.updateFields()
        
        start_features = []
        end_features = []
        start_ids = []
        end_ids = []

        # Create start features
        if self.dlg.start_radio_layer.isChecked():
            # Exit if CRS != WGS84
            if osm_tools_aux.CheckCRS(self, self.layer_start.crs().authid()) == False:
                return
            start_feat = self.layer_start.getFeatures()
            field_id = self.layer_start.fieldNameIndex(self.dlg.start_layer_id.currentText())
            for feat in start_feat:
                x, y = feat.geometry().asPoint()
                start_features.append(",".join([str(x), str(y)]))
                start_ids.append(feat.attributes()[field_id])
        else:
            start_features.append(self.dlg.add_start.text())
            point_list = [float(x) for x in start_features[0].split(",")]
            point_geom = QgsGeometry.fromPoint(QgsPoint(point_list[0], point_list[1]))
            _point_geo = osm_tools_geocode.Geocode(self.dlg)
            loc_dict = _point_geo.reverseGeocode(point_geom)
            
            if loc_dict:       
                start_ids.append(loc_dict.get('CITY', start_features[0]))
            else:
                return
            
        # Create end features
        if self.dlg.end_radio_layer.isChecked():
            # Exit if CRS != WGS84
            if osm_tools_aux.CheckCRS(self, self.layer_end.crs().authid()) == False:
                return
            end_feat = self.layer_end.getFeatures()
            field_id = self.layer_end.fieldNameIndex(self.dlg.end_layer_id.currentText())
            for feat in end_feat:
                x, y = feat.geometry().asPoint()
                end_features.append(",".join([str(x), str(y)]))
                end_ids.append(feat.attributes()[field_id])
        else:            
            end_features.append(self.dlg.add_end.text())
            point_list = [float(x) for x in end_features[0].split(",")]
            point_geom = QgsGeometry.fromPoint(QgsPoint(point_list[0], point_list[1]))
            _point_geo = osm_tools_geocode.Geocode(self.dlg)
            loc_dict = _point_geo.reverseGeocode(point_geom)
            
            if loc_dict:       
                end_ids.append(loc_dict.get('CITY', end_features[0]))
            else:
                return
            
        # Rules for creating routing features
        if len(start_features) == 1:
            if len(end_features) == 1:
                route_features = list(zip(start_features, end_features))
                route_ids = list(zip(start_ids, end_ids))
            else:
                route_features = list(zip(itertools.cycle(start_features), end_features))
                route_ids = list(zip(itertools.cycle(start_ids), end_ids))
        else:
            if len(end_features) == 1:
                route_features = list(zip(start_features, itertools.cycle(end_features)))
                route_ids = list(zip(start_ids, itertools.cycle(end_ids)))
            else:
                if self.dlg.radio_one.isChecked():
                    route_features = list(zip(start_features, end_features))
                    route_ids = list(zip(start_ids, end_ids))
                else:
                    route_features = list(itertools.product(start_features, end_features))
                    route_ids = list(itertools.product(start_ids, end_ids))
                    
        # Convert tuple list into list list
        route_features = [list(feat) for feat in route_features]

        # Read route details from GUI
        route_via = ",".join(self.dlg.add_via.text().split("\n")[:-1])
        
        # Set up progress bar
        route_count = len(route_features)
        progressMessageBar = self.iface.messageBar().createMessage("Requesting routes from ORS...")
        progress = QProgressBar()
        progress.setMaximum(100)
        progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        progressMessageBar.layout().addWidget(progress)
        self.iface.messageBar().pushWidget(progressMessageBar, self.iface.messageBar().INFO)
        
        for i, route in enumerate(route_features):
            # Skip route if start and end are identical
            if route[0] == route[-1]:
                continue
            else:
#                try:
                # Insert via point if present and make string    
                if route_via != "":
                    route.insert(1, route_via)
                    
                route_string = "|".join(route)
                # Create URL
                req = "{}api_key={}&coordinates={}&profile={}&preference={}&instructions=False&geometry_format=geojson&units=m".format(self.url_ors, 
                                                    self.api_key, 
                                                   route_string,
                                                    self.mode_travel,
                                                    self.mode_routing
                                                    )
                
                #print req
                
                # Get response from API and read into element tree
                response = requests.get(req)
                root = json.loads(response.text)
                
                # Check if there was an HTTP error and terminate
                http_status = response.status_code
                try:
                    if http_status > 200:
                        osm_tools_aux.CheckStatus(http_status, req)
                        return
                except: 
                    #qgis.utils.iface.messageBar().clearWidgets()
                    return
                    
                feat_out = QgsFeature()
                
                # Read all coordinates
                coords_list = []
                for coords in root['routes'][0]['geometry']['coordinates']:
#                        coords_tuple = tuple([float(coord) for coord in coords.text.split(" ")])
                    qgis_coords = QgsPoint(coords[0], coords[1])
                    coords_list.append(qgis_coords)
                
                # Read total time
                time_path = root['routes'][0]['summary']['duration']
                
                if time_path/3600 >= 1:
                    hours = int(time_path)/3600
                    rest = time_path%3600
                    if rest/60 >= 1:
                        minutes = int(rest)/60
                        seconds = rest%60
                    else:
                        minutes = 0
                        seconds = rest
                else:
                    hours = 0
                    minutes = int(time_path)/60
                    seconds = time_path%60
                        
                                         
                # Read total distance
                distance = root['routes'][0]['summary']['distance'] / 1000
                
                # Read X and Y
                route_start_x, route_start_y = [float(coord) for coord in route[0].split(",")]
                route_end_x, route_end_y = [float(coord) for coord in route[-1].split(",")]
                    
                # Set feature geometry and attributes
                feat_out.setGeometry(QgsGeometry.fromPolyline(coords_list))
                feat_out.setAttributes([distance,
                                        hours,
                                        minutes,
                                        seconds,
                                        self.mode_travel,
                                        self.mode_routing,
                                        route_ids[i][0],
                                        route_ids[i][1],
                                        route_start_y,
                                        route_start_x,
                                        route_end_y,
                                        route_end_x])
                
                layer_out_prov.addFeatures([feat_out])
                
                percent = (i/float(route_count)) * 100
                
                progress.setValue(percent)
                    
#                except (AttributeError, TypeError):
#                    msg = "Request is not valid! Check parameters. TIP: Coordinates must plot within 1 km of a road."
#                    qgis.utils.iface.messageBar().pushMessage(msg, level = qgis.gui.QgsMessageBar.CRITICAL)
#                    return
                
        layer_out.updateExtents()
        
        qgis.utils.iface.messageBar().clearWidgets() 
        QgsMapLayerRegistry.instance().addMapLayer(layer_out)
        
        QgsMapLayerRegistry.instance().addMapLayer(layer_out)