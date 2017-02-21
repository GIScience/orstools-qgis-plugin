# -*- coding: utf-8 -*-
"""
Created on Mon Feb 06 15:26:47 2017

@author: nnolde
"""
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import * 
import qgis.utils
import processing

import requests
import xml.etree.ElementTree as ET
import os.path

import ors_tools       
import ors_tools_geocode
import ors_tools_pointtool
        
class accessAnalysis:
    def __init__(self, dlg):
        self.dlg = dlg
        self.url = r"http://openls.geog.uni-heidelberg.de/analyse?"
        self.ns = {'gml': 'http://www.opengis.net/gml',
                  'aas': "http://www.geoinform.fh-mainz.de/aas",
                  'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
                  
        self.mapTool = None

        self.dlg.mode.clear()
        self.dlg.layer.clear()
        self.dlg.method.clear()  
        self.dlg.mode.addItem('Car')
        self.dlg.mode.addItem('Bicycle')
        self.dlg.mode.addItem('Pedestrian')      
        self.dlg.method.addItem('RecursiveGrid')
        self.dlg.method.addItem('TIN') 
        
        for layer in qgis.utils.iface.legendInterface().layers():
            layerType = layer.type()
            if layerType == QgsMapLayer.VectorLayer and layer.wkbType() == QGis.WKBPoint:
                self.dlg.layer.addItem(layer.name())
                  
        # GUI Init
        self.popBox()
        
        # API parameters
        self.api_key = self.dlg.api_key.text()
        self.iso_max = self.dlg.iso_max.value()
        self.iso_int = self.dlg.iso_int.value() * 60
        self.iso_mode = self.dlg.mode.currentText()
        self.iso_method = self.dlg.method.currentText()
        self.iface = qgis.utils.iface
        
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Connect events to signals
        self.dlg.iso_max.valueChanged.connect(self.valueChanged)
        self.dlg.iso_int.valueChanged.connect(self.valueChanged)
        self.dlg.mode.currentIndexChanged.connect(self.valueChanged)
        self.dlg.method.currentIndexChanged.connect(self.valueChanged)
        self.dlg.use_layer.stateChanged.connect(self.enableLayer)
        self.dlg.api_key.textChanged.connect(self.keyWriter)
        
        # Populate field ID dynamically when combobox selection changes
        self.dlg.layer.currentIndexChanged.connect(self.popBox)
        self.dlg.check_dissolve.stateChanged.connect(self.popBox)
        self.dlg.access_map.clicked.connect(self.initMapTool)
    
    
    def enableLayer(self):
        if self.dlg.use_layer.isChecked() == True:
            self.dlg.frame_2.setEnabled(True)
        else:
            self.dlg.frame_2.setEnabled(False)
            
    
    def valueChanged(self):
        self.iso_max = self.dlg.iso_max.value()
        self.iso_int = self.dlg.iso_int.value() * 60
        self.iso_mode = self.dlg.mode.currentText()
        self.iso_method = self.dlg.method.currentText()
        
    
    def keyWriter(self):
        with open(os.path.join(self.script_dir, "apikey.txt"), 'w') as key:
            self.api_key = self.dlg.api_key.text()
            return key.write(self.dlg.api_key.text())
        
        
    # Populate field ID
    def popBox(self):              
        if self.dlg.check_dissolve.isChecked() == True:
            self.dlg.id_field.setEnabled(True)
            self.dlg.id_field.clear()
            layer_list = [lyr for lyr in QgsMapLayerRegistry.instance().mapLayers().values() if lyr.name() == self.dlg.layer.currentText()]
            if layer_list:
                layer_selected = layer_list[0]
                fields_selected = layer_selected.fields()
                for field in fields_selected:
                    self.dlg.id_field.addItem(field.name())
        else:
            self.dlg.id_field.setEnabled(False)
        return
    
        
    # Connect to PointTool and set as mapTool
    def initMapTool(self):
        sending_button = self.dlg.sender().objectName()
        self.mapTool = ors_tools_pointtool.PointTool(qgis.utils.iface.mapCanvas(), sending_button)        
        self.iface.mapCanvas().setMapTool(self.mapTool)     
        self.mapTool.canvasClicked.connect(self.pointAnalysis)
        
        
    def accRequest(self, point_in):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        #geometry_in = QgsGeometry.fromPoint(point_in)
        x, y = point_in.asPoint()
        
        #TODO: 'method' does not seem to be available over get()?! Ask GIScience team
        req = "{}api_key={}&position={},{}&minutes={}&interval={}&routePreference={}".format(self.url, 
                                                                self.api_key, 
                                                                x, 
                                                                y,
                                                                self.iso_max,
                                                                self.iso_int,
                                                                self.iso_mode)
        response = requests.get(req)
        root = ET.fromstring(response.content)
        access_path = root.find("aas:Response/"
                                "aas:AccessibilityResponse/"
                                "aas:AccessibilityGeometry",
                                self.ns)
        
        QApplication.restoreOverrideCursor()
        
        isochrone_list = []
        feat_list = []

        for isochrone in access_path.findall("aas:Isochrone", self.ns):
            feat_out = QgsFeature()
            
            coord_ext_list = []
            coord_int_list = []
            
            # First find the exterior ring
            for coords_ext in isochrone.findall("aas:IsochroneGeometry/"
                                            "gml:Polygon/"
                                            "gml:exterior/"
                                            "gml:LinearRing/"
                                            "gml:pos",
                                            self.ns):
                coords_ext_tuple = tuple([float(coord) for coord in coords_ext.text.split(" ")])
                qgis_coords_ext = QgsPoint(coords_ext_tuple[0], coords_ext_tuple[1])
                coord_ext_list.append(qgis_coords_ext)
            
            # Then find all interior rings
            for ring_int in isochrone.findall("aas:IsochroneGeometry/"
                                        "gml:Polygon/"
                                        "gml:interior",
                                        self.ns):
                int_poly = []
                for coords_int in ring_int.findall("gml:LinearRing/"
                                        "gml:pos",
                                        self.ns):
                    coords_int_tuple = tuple([float(coord) for coord in coords_int.text.split(" ")])
                    qgis_coords_int = QgsPoint(coords_int_tuple[0], coords_int_tuple[1])
                    int_poly.append(qgis_coords_int)
                coord_int_list.append(int_poly)
                    
            feat_out.setGeometry(QgsGeometry.fromPolygon([coord_ext_list] + coord_int_list))
            feat_list.append(feat_out)
            isochrone_list.append(float(isochrone.get("time"))/60)
        
        return feat_list, isochrone_list

        
    def pointAnalysis(self, point):
        point_geometry = QgsGeometry.fromPoint(point)
        feat_list, isochrone_list = self.accRequest(point_geometry)
        
        _point_geocode = ors_tools_geocode.Geocode(self.dlg, self.api_key)
        loc_dict = _point_geocode.reverseGeocode(point_geometry)
            
        out_str = u"Long: {0:.3f}, Lat:{1:.3f}\n{2}\n{3}\n{4}".format(loc_dict.get('Lon', ""),
                                                        loc_dict.get('Lat', ""),
                                                        loc_dict.get('MUNICIPALI', "NA"),
                                                        loc_dict.get('COUNTRYSUB', "NA"),
                                                        loc_dict.get('COUNTRY', "NA")
                                                        )
        self.dlg.access_text.setText(out_str)
        
        layer_out = QgsVectorLayer("Polygon?crs=EPSG:4326", "AA_{0:.3f},{1:.3f}".format(loc_dict['Lon'], loc_dict['Lat']), "memory")
        layer_out_point = QgsVectorLayer("Point?crs=EPSG:4326", "Point_{0:.3f},{1:.3f}".format(loc_dict['Lon'], loc_dict['Lat']), "memory")
        
        layer_out_prov = layer_out.dataProvider()
        layer_out_prov.addAttributes([QgsField("AA_MINS", QVariant.Int)])
        layer_out_prov.addAttributes([QgsField("AA_MODE", QVariant.String)])
        layer_out.updateFields()
        
        layer_out_point_prov = layer_out_point.dataProvider()
        layer_out_point_prov.addAttributes([QgsField("LAT", QVariant.String)])
        layer_out_point_prov.addAttributes([QgsField("LONG", QVariant.String)])
        layer_out_point_prov.addAttributes([QgsField("DIST_INPUT", QVariant.String)])
        layer_out_point_prov.addAttributes([QgsField("BULIDINGNA", QVariant.String)])
        layer_out_point_prov.addAttributes([QgsField("OFFICIALNA", QVariant.String)])
        layer_out_point_prov.addAttributes([QgsField("NUMBER", QVariant.String)])
        layer_out_point_prov.addAttributes([QgsField("POSTALCODE", QVariant.String)])
        layer_out_point_prov.addAttributes([QgsField("MUNICIPALI", QVariant.String)])
        layer_out_point_prov.addAttributes([QgsField("COUNTRYSUB", QVariant.String)])
        layer_out_point_prov.addAttributes([QgsField("COUNTRY", QVariant.String)])
        layer_out_point.updateFields()
        
        # Add clicked point feature to point feature class
        point_out = QgsFeature()
        point_out.setGeometry(point_geometry)
        point_out.setAttributes([loc_dict.get("Lat", None),
                                loc_dict.get("Lon", None),
                                loc_dict.get("DIST_INPUT", None),
                                loc_dict.get("BULIDINGNA", None),
                                loc_dict.get("OFFICIALNA", None),
                                loc_dict.get("NUMBER", None),
                                loc_dict.get("POSTALCODE", None),
                                loc_dict.get("MUNICIPALI", None),
                                loc_dict.get("COUNTRYSUB", None),
                                loc_dict.get('COUNTRY', None)
                                ])
        layer_out_point_prov.addFeatures([point_out])
        
        for ind, feat in enumerate(feat_list):
            feat.setAttributes([isochrone_list[ind], self.iso_mode])
            layer_out_prov.addFeatures([feat])

        layer_out.updateExtents()
        layer_out_point.updateExtents()
        
        QgsMapLayerRegistry.instance().addMapLayer(layer_out_point)
        QgsMapLayerRegistry.instance().addMapLayer(layer_out)

        fields_diss = ["AA_MINS"]
        self.dissolveFields(layer_out, fields_diss)
        
        # Unset Map Tool
        self.iface.mapCanvas().unsetMapTool(self.mapTool)
        self.mapTool = None

    def iterAnalysis(self):
        allLayers = self.iface.legendInterface().layers()
                
        # Determine selected layer
        for layer in allLayers:
            if layer.name() == self.dlg.layer.currentText():
                acc_input_lyr = layer
                break
        #TODO: Maybe reproject when other than WGS84?! Now it`s just closing the window
        if ors_tools.CheckCRS(self, acc_input_lyr.crs().authid()) == False:
            return
        
        # Define polygon .shp
        layer_out = QgsVectorLayer("Polygon?crs=EPSG:4326", "{}_AA_{}".format(acc_input_lyr.name(),self.iso_mode), "memory")
        layer_out_prov = layer_out.dataProvider()
        for field in acc_input_lyr.fields():
            layer_out_prov.addAttributes([field])
        layer_out_prov.addAttributes([QgsField("AA_MINS", QVariant.Int)])
        layer_out_prov.addAttributes([QgsField("AA_MODE", QVariant.String)])
        layer_out.updateFields()
        
        features = acc_input_lyr.getFeatures()
        
        # Progress Bar
        feature_count = acc_input_lyr.featureCount()
        progressMessageBar = self.iface.messageBar().createMessage("Requesting analysis from ORS...")
        progress = QProgressBar()
        progress.setMaximum(feature_count)
        progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        progressMessageBar.layout().addWidget(progress)
        self.iface.messageBar().pushWidget(progressMessageBar, self.iface.messageBar().INFO)
                
        for i, feat_in in enumerate(features):
            progress.setValue(i)
            
            feat_list, isochrone_list = self.accRequest(feat_in.geometry())
            
            for ind, feat in enumerate(feat_list):                
                feat.setAttributes(feat_in.attributes() + [isochrone_list[ind], self.iso_mode])
                layer_out_prov.addFeatures([feat])

            layer_out.updateExtents()
        
        id_field = self.dlg.id_field.currentText()
        fields_diss = ["AA_MINS", id_field]
        
        QgsMapLayerRegistry.instance().addMapLayer(layer_out)
        self.dissolveFields(layer_out, fields_diss)
    
        
    def dissolveFields(self, layer_out, fields_diss):        
        # Dissolve output for interval 'AA_MINS' and id_layer, remove non-dissolved layer
        
        processing.runandload("qgis:dissolve", layer_out , False,
                          fields_diss, "memory:dissolved")
        layer_dissolved = QgsMapLayerRegistry.instance().mapLayersByName("Dissolved")[-1]
        layer_dissolved.setLayerName(layer_out.name())
        QgsMapLayerRegistry.instance().removeMapLayers([layer_out.id()])