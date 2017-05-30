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

import requests
import json
import os.path
from math import ceil
      
import osm_tools_geocode
import osm_tools_pointtool
import osm_tools_aux
        
class accessAnalysis:
    def __init__(self, dlg):
        self.dlg = dlg
        self.url = r"https://api.openrouteservice.org/isochrones?"
                  
        self.mapTool = None
        
        self.loc_limit = 5
        
        self.iso_amount = ceil(self.dlg.iso_max.value()/self.dlg.iso_int.value())

        self.dlg.mode.clear()
        self.dlg.layer.clear()
        self.dlg.unit.clear() 
        self.dlg.unit.addItem('time')
        self.dlg.unit.addItem('distance')
        self.dlg.mode.addItem('driving-car')
        self.dlg.mode.addItem('driving-hgv')
        self.dlg.mode.addItem('cycling-regular')
        self.dlg.mode.addItem('cycling-road')
        self.dlg.mode.addItem('cycling-safe')
        self.dlg.mode.addItem('cycling-mountain')
        self.dlg.mode.addItem('cycling-tour')
        self.dlg.mode.addItem('foot-walking')
        self.dlg.mode.addItem('foot-hiking')
        
        for layer in qgis.utils.iface.legendInterface().layers():
            layerType = layer.type()
            if layerType == QgsMapLayer.VectorLayer and layer.wkbType() == QGis.WKBPoint:
                self.dlg.layer.addItem(layer.name())
        
        # API parameters
        self.api_key = self.dlg.api_key.text()
        self.iso_mode = self.dlg.mode.currentText()
        self.iso_max = self.dlg.iso_max.value()
        self.iso_int = self.dlg.iso_int.value()
        self.iso_range_type = self.dlg.unit.currentText()
        self.iface = qgis.utils.iface
        
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Connect events to signals
        self.dlg.iso_max.valueChanged.connect(self.valueChanged)
        self.dlg.iso_int.valueChanged.connect(self.valueChanged)
        self.dlg.mode.currentIndexChanged.connect(self.valueChanged)
        self.dlg.unit.currentIndexChanged.connect(self.valueChanged)
        self.dlg.use_layer.stateChanged.connect(self.enableLayer)
        self.dlg.api_key.textChanged.connect(self.keyWriter)
        
        # Populate field ID dynamically when combobox selection changes
#        self.dlg.layer.currentIndexChanged.connect(self.popBox)
#        self.dlg.check_dissolve.stateChanged.connect(self.popBox)
        self.dlg.access_map.clicked.connect(self.initMapTool)
    
    
    def enableLayer(self):
        if self.dlg.use_layer.isChecked() == True:
            self.dlg.frame_2.setEnabled(True)
        else:
            self.dlg.frame_2.setEnabled(False)
            
    
    def valueChanged(self):
        self.iso_max = self.dlg.iso_max.value()
        self.iso_int = self.dlg.iso_int.value()
        self.iso_mode = self.dlg.mode.currentText()
        self.iso_range_type = self.dlg.unit.currentText()
        self.iso_amount = ceil(self.dlg.iso_max.value()/self.dlg.iso_int.value())
        
        if self.iso_range_type == 'time':
            self.dlg.iso_max.setDecimals(0)
            self.dlg.iso_int.setDecimals(0)
            self.dlg.label_6.setText('mins')
            self.dlg.label_8.setText('mins')
        else:
            self.dlg.iso_max.setDecimals(3)
            self.dlg.iso_int.setDecimals(3)
            self.dlg.label_6.setText('km')
            self.dlg.label_8.setText('km')
        
    
    def keyWriter(self):
        with open(os.path.join(self.script_dir, "apikey.txt"), 'w') as key:
            self.api_key = self.dlg.api_key.text()
            return key.write(self.dlg.api_key.text())
        
        
    # Populate field ID
#    def popBox(self):              
#        if self.dlg.check_dissolve.isChecked() == True:
#            self.dlg.id_field.setEnabled(True)
#            self.dlg.id_field.clear()
#            layer_list = [lyr for lyr in QgsMapLayerRegistry.instance().mapLayers().values() if lyr.name() == self.dlg.layer.currentText()]
#            if layer_list:
#                layer_selected = layer_list[0]
#                fields_selected = layer_selected.fields()
#                for field in fields_selected:
#                    self.dlg.id_field.addItem(field.name())
#        else:
#            self.dlg.id_field.setEnabled(False)
#        return
    
        
    # Connect to PointTool and set as mapTool
    def initMapTool(self):
        self.dlg.showMinimized()
        sending_button = self.dlg.sender().objectName()
        self.mapTool = osm_tools_pointtool.PointTool(qgis.utils.iface.mapCanvas(), sending_button)        
        self.iface.mapCanvas().setMapTool(self.mapTool)     
        self.mapTool.canvasClicked.connect(self.pointAnalysis)
        
        
    def accRequest(self, points_in):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        #geometry_in = QgsGeometry.fromPoint(point_in)
        
        # Collect all points in a list
        coord_list = []
        for point_in in points_in:
            coord_list.append(point_in.asPoint())
        
        # Set isochrone dimension
        if self.iso_range_type == 'time':
            self.iso_max = self.dlg.iso_max.value() * 60
            self.iso_int = self.dlg.iso_int.value() * 60
        
        req = "{}api_key={}&range_type={}&range={}&interval={}&profile={}&location_type=start&locations={},{}".format(self.url, 
                                                                self.api_key,
                                                                self.iso_range_type,
                                                                self.iso_max,
                                                                self.iso_int,
                                                                self.iso_mode, 
                                                                "{0:.5f}".format(coord_list[0][0]),
                                                                "{0:.5f}".format(coord_list[0][1]))
        
        # Append optional parameters
        if len(points_in) > 1:
            for coord in coord_list[1:]:
                req += "%7C{0:.5f},{1:.5f}".format(coord[0], coord[1])
        
        if self.iso_range_type == 'distance':
            req += '&units=km'
            
        if self.dlg.iso_overlap.isChecked() and self.dlg.iso_overlap.isEnabled():
            req += "&intersections=true"
        
        print req
        
        response = requests.get(req)
        root = json.loads(response.text)
        
        # Check if there was an HTTP error and terminate
        http_status = response.status_code
        
        try:
            if http_status > 200:
                osm_tools_aux.CheckStatus(http_status, req)
                return
        except: 
            qgis.utils.iface.messageBar().clearWidgets()
            return
        
        QApplication.restoreOverrideCursor()
        
        isochrone_list = []
        feat_list = []
        isochrone_parse = self.iso_amount * len(points_in)

#        try:
        for isochrone in root['features']:
            feat_out = QgsFeature()
            
            coord_list = []
            
            # First find the exterior ring
            for coords in isochrone['geometry']['coordinates'][0]:
                qgis_coords = QgsPoint(coords[0], coords[1])
                coord_list.append(qgis_coords)
            
            feat_out.setGeometry(QgsGeometry.fromPolygon([coord_list]))
            feat_list.append(feat_out)
            
            #TODO: Put geometry output in other functions, allowing for separate overlap shapefile
            # Leave loop if feature is an overlap area
            if "contours" in isochrone['properties']:
                isochrone_list.append(isochrone['properties']["contours"])
                continue
            
            iso_value = isochrone['properties']['value']
            if self.iso_range_type == 'time':
                iso_value /= 60.0
            isochrone_list.append(iso_value)
#        except (AttributeError, TypeError):
#            msg = "Request is not valid! Check parameters. TIP: Coordinates must plot within 1 km of a road."
#            qgis.utils.iface.messageBar().pushMessage(msg, level = qgis.gui.QgsMessageBar.CRITICAL)
#            return

        return feat_list, isochrone_list

        
    def pointAnalysis(self, point):
        point_geometry = QgsGeometry.fromPoint(point)
        try:
            feat_list, isochrone_list = self.accRequest([point_geometry])
        except:
            self.dlg.close()
            QApplication.restoreOverrideCursor()
            return
        
        _point_geocode = osm_tools_geocode.Geocode(self.dlg, self.api_key)
        loc_dict = _point_geocode.reverseGeocode(point_geometry)
        
        out_str = u"Long: {0:.3f}, Lat:{1:.3f}\n{2}\n{3}\n{4}".format(loc_dict.get('Lon', ""),
                                                        loc_dict.get('Lat', ""),
                                                        loc_dict.get('CITY', "NA"),
                                                        loc_dict.get('STATE', "NA"),
                                                        loc_dict.get('COUNTRY', "NA")
                                                        )
        self.dlg.access_text.setText(out_str)
        
        layer_out = QgsVectorLayer("Polygon?crs=EPSG:4326", "AA_{0:.3f},{1:.3f}".format(loc_dict['Lon'], loc_dict['Lat']), "memory")
        layer_out_point = QgsVectorLayer("Point?crs=EPSG:4326", "Point_{0:.3f},{1:.3f}".format(loc_dict['Lon'], loc_dict['Lat']), "memory")
        
        layer_out_prov = layer_out.dataProvider()
        if self.iso_range_type == 'time':
            layer_out_prov.addAttributes([QgsField("AA_MINS", QVariant.Int)])
        else:
            layer_out_prov.addAttributes([QgsField("AA_METERS", QVariant.Int)])            
        layer_out_prov.addAttributes([QgsField("AA_MODE", QVariant.String)])
        layer_out.updateFields()
        
        layer_out_point_prov = layer_out_point.dataProvider()
        layer_out_point_prov.addAttributes([QgsField("LAT", QVariant.String)])
        layer_out_point_prov.addAttributes([QgsField("LONG", QVariant.String)])
        layer_out_point_prov.addAttributes([QgsField("NAME", QVariant.String)])
        layer_out_point_prov.addAttributes([QgsField("STREET", QVariant.String)])
        layer_out_point_prov.addAttributes([QgsField("NUMBER", QVariant.String)])
        layer_out_point_prov.addAttributes([QgsField("POSTALCODE", QVariant.String)])
        layer_out_point_prov.addAttributes([QgsField("CITY", QVariant.String)])
        layer_out_point_prov.addAttributes([QgsField("STATE", QVariant.String)])
        layer_out_point_prov.addAttributes([QgsField("COUNTRY", QVariant.String)])
        layer_out_point.updateFields()
        
        # Add clicked point feature to point feature class
        point_out = QgsFeature()
        point_out.setGeometry(point_geometry)
        point_out.setAttributes([loc_dict.get("Lat", None),
                                loc_dict.get("Lon", None),
                                loc_dict.get("NAME", None),
                                loc_dict.get("STREET", None),
                                loc_dict.get("NUMBER", None),
                                loc_dict.get("POSTALCODE", None),
                                loc_dict.get("CITY", None),
                                loc_dict.get("STATE", None),
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

#        fields_diss = ["AA_MINS"]
#        self.dissolveFields(layer_out, fields_diss)
        
        # Unset Map Tool and show dialog again
        self.dlg.showNormal()
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
        if osm_tools_aux.CheckCRS(self, acc_input_lyr.crs().authid()) == False:
            return
        
        # Define polygon .shp
        layer_out = QgsVectorLayer("Polygon?crs=EPSG:4326", "{}_AA_{}".format(acc_input_lyr.name(),self.iso_mode), "memory")
        layer_out_prov = layer_out.dataProvider()
        for field in acc_input_lyr.fields():
            layer_out_prov.addAttributes([field])
        # Add field depending on range type
        if self.iso_range_type == 'time':
            layer_out_prov.addAttributes([QgsField("AA_MINS", QVariant.String)])
        else:
            layer_out_prov.addAttributes([QgsField("AA_METERS", QVariant.String)])
        layer_out_prov.addAttributes([QgsField("AA_MODE", QVariant.String)])
        layer_out.updateFields()
        
        # Progress Bar
        feature_count = acc_input_lyr.featureCount()
        progressMessageBar = self.iface.messageBar().createMessage("Requesting analysis from ORS...")
        progress = QProgressBar()
        progress.setMaximum(100)
        progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        progressMessageBar.layout().addWidget(progress)
        self.iface.messageBar().pushWidget(progressMessageBar, self.iface.messageBar().INFO)
        
        # Chunk features
        n = self.loc_limit
        features_list = []
        for feature in acc_input_lyr.getFeatures():
            features_list.append(feature)
            
        features_chunked = [features_list[i:i+n] for i in xrange(0, feature_count, n)]
        
        for chunk in features_chunked:
            feat_in_list = []
            for i, feat_in in enumerate(chunk):
                percent = (i/feature_count) * 100
                progress.setValue(percent)
                
                feat_in_list.append(feat_in.geometry())
                
            feat_list, isochrone_list = self.accRequest(feat_in_list)
            
            for ind, feat in enumerate(feat_list):
                # Map attributes on features
                if type(isochrone_list[ind]) == list:
                    attr_amount = len(chunk[0].attributes())
                    feat.setAttributes( [None] * attr_amount + ['overlap', self.iso_mode])
                else:
                    att_counter = ind/self.iso_amount
                    feat.setAttributes(chunk[att_counter].attributes() + [isochrone_list[ind], self.iso_mode])
                layer_out_prov.addFeatures([feat])

            layer_out.updateExtents()
        
#        id_field = self.dlg.id_field.currentText()
#        fields_diss = ["AA_MINS", id_field]
        
        qgis.utils.iface.messageBar().clearWidgets() 
        
        QgsMapLayerRegistry.instance().addMapLayer(layer_out)
#        self.dissolveFields(layer_out, fields_diss)
    
        
#    def dissolveFields(self, layer_out, fields_diss):
#        # Dissolve output for interval 'AA_MINS' and id_layer, remove non-dissolved layer
#        
#        processing.runandload("qgis:dissolve", layer_out , False,
#                          fields_diss, "memory:dissolved")
#        layer_dissolved = QgsMapLayerRegistry.instance().mapLayersByName("Dissolved")[-1]
#        layer_dissolved.setLayerName(layer_out.name())
#        QgsMapLayerRegistry.instance().removeMapLayers([layer_out.id()])