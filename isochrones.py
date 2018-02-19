#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 17 17:31:12 2018

@author: nilsnolde
"""


from PyQt5.QtCore import QVariant
from PyQt5.QtGui import QColor

from qgis.core import (QgsPointXY,
                       QgsVectorLayer,
                       QgsFeature,
                       QgsField,
                       QgsGeometry,
                       QgsProject,
                       QgsSymbol,
                       QgsSimpleFillSymbolLayer,
                       QgsRendererCategory,
                       QgsCategorizedSymbolRenderer)
from qgis.gui import QgsMessageBar

from ORStools import (geocode,
                      convert,
                      osm_tools_aux
                      )

class isochrones:
    def __init__(self, dlg, client, iface):
        
        self.dlg = dlg
        self.client = client
        self.iface = iface
        
        self.url = '/isochrones'
    
        self.iso_mode = self.dlg.access_mode_combo.currentText()
        try:
            self.access_range_input = list(map(int,self.dlg.access_range.text().split(',')))
        except ValueError:
            self.iface.messageBar().pushCritical('ValueError', 
                                                 'Only specify comma separated '
                                                 'integer values for isochrone ranges')
            self.dlg.close()
        
        self.dimension = self.dlg.access_unit_combo.currentText()
        self.factor = 60 if self.dimension == 'time' else 1000
        
        self.access_range_input = [x * self.factor for x in self.access_range_input]
             
        self.params = {'range_type': self.dlg.access_unit_combo.currentText(),
                       'profile': self.dlg.access_mode_combo.currentText(),
                       'range': convert._comma_list(self.access_range_input)
                       }
        
    
    def main(self):
        if self.dlg.access_layer_check.isChecked():
            layer_name = self.dlg.access_layer_combo.currentText()
            layer = [layer for layer in self.iface.mapCanvas().layers() if layer.name() == layer_name][0]
            
            osm_tools_aux.checkCRS(layer, self.iface.messageBar())
                
            feats = layer.getFeatures()
            feat_count = layer.featureCount()
            
            message_bar = osm_tools_aux.pushProgressBar(self.iface)
            
            responses = []
            for i, feat in enumerate(feats):
                percent = (i/feat_count) * 100
                message_bar.setValue(percent)
                # Get coordinates
                geom = feat.geometry().asPoint()
                coords = [geom.x(), geom.y()]   
                
                # Get response
                self.params['locations'] = convert._build_coords(coords)
                responses.append(self.client.request(self.url, self.params))
                
            poly_out = self._addPolygon(responses, layer_name)
            
        else:  
            # Define the mapped point
            coords = [float(x) for x in self.dlg.access_map_label.text().split('\n')[:2]]
            point_geom = QgsPointXY(*coords)
            response_dict = geocode.reverse_geocode(self.client, point_geom)
            
            self.params['locations'] = convert._build_coords(coords)
            
            # Fire request
            response = self.client.request(self.url, self.params)
            
            name_ext = "{0:.3f},{1:.3f}".format(*response['features'][0]['properties']['center'])
            
            poly_out = self._addPolygon([response], name_ext)
            
            point_out = self._addPoint(response_dict, point_geom, name_ext)
            point_out.updateExtents()
            QgsProject.instance().addMapLayer(point_out)        
        
        poly_out.updateExtents()
        
        self._stylePoly(poly_out)
#        self.iface.setActiveLayer(poly_out)
        QgsProject.instance().addMapLayer(poly_out)
        self.iface.mapCanvas().zoomToFeatureExtent(poly_out.extent())
        
        self.iface.messageBar().clearWidgets() 
            
        
    def _addPoint(self, response_dict, point_geom, name_ext):
        layer_name = "Point_{}".format(name_ext)
        point_layer = QgsVectorLayer("Point?crs=EPSG:4326", layer_name, "memory")
        
        point_layer.dataProvider().addAttributes([QgsField("LAT", QVariant.String)])
        point_layer.dataProvider().addAttributes([QgsField("LONG", QVariant.String)])
        point_layer.dataProvider().addAttributes([QgsField("NAME", QVariant.String)])
        point_layer.dataProvider().addAttributes([QgsField("STREET", QVariant.String)])
        point_layer.dataProvider().addAttributes([QgsField("NUMBER", QVariant.String)])
        point_layer.dataProvider().addAttributes([QgsField("POSTALCODE", QVariant.String)])
        point_layer.dataProvider().addAttributes([QgsField("CITY", QVariant.String)])
        point_layer.dataProvider().addAttributes([QgsField("STATE", QVariant.String)])
        point_layer.dataProvider().addAttributes([QgsField("COUNTRY", QVariant.String)])
        point_layer.updateFields()
        
        # Add clicked point feature to point feature class
        point_feat = QgsFeature()
        point_feat.setGeometry(QgsGeometry.fromPointXY(point_geom))
        point_feat.setAttributes([response_dict.get("Lat", None),
                                response_dict.get("Lon", None),
                                response_dict.get("NAME", None),
                                response_dict.get("STREET", None),
                                response_dict.get("NUMBER", None),
                                response_dict.get("POSTALCODE", None),
                                response_dict.get("CITY", None),
                                response_dict.get("STATE", None),
                                response_dict.get('COUNTRY', None)
                                ])
        point_layer.dataProvider().addFeatures([point_feat])
        
        return point_layer
        
            
    def _addPolygon(self, responses, name_ext):
        layer_name = "Isochrone_{}".format(name_ext)
        poly_out = QgsVectorLayer("Polygon?crs=EPSG:4326", layer_name, "memory")
        
        if self.dimension == 'time':
            poly_out.dataProvider().addAttributes([QgsField("AA_MINS", QVariant.Int)])
        else:
            poly_out.dataProvider().addAttributes([QgsField("AA_METERS", QVariant.Int)])            
        poly_out.dataProvider().addAttributes([QgsField("AA_MODE", QVariant.String)])
        poly_out.updateFields()
        
        # Sort features based on the isochrone value, so that longest isochrone
        # is added first. This will plot the isochrones on top of each other.
        l = lambda x: x['properties']['value']
        for response in responses:
            for isochrone in sorted(response['features'], key=l, reverse=True):
                feat = QgsFeature()
                coordinates = isochrone['geometry']['coordinates']
                iso_value = isochrone['properties']['value']
                qgis_coords = [QgsPointXY(x, y) for x, y in coordinates[0]]
                feat.setGeometry(QgsGeometry.fromPolygonXY([qgis_coords]))
                feat.setAttributes([iso_value / 60 if self.dimension == 'time' else iso_value,
                                   self.iso_mode])
                poly_out.dataProvider().addFeature(feat)
        
        return poly_out
    

    def _stylePoly(self, layer):
        if self.dimension == 'time':
            field_name = 'AA_MINS'
            legend_suffix = ' mins'
        else:
            field_name = 'AA_METERS'
            legend_suffix = ' m'
        field = layer.fields().lookupField(field_name)
        unique_values = sorted(layer.uniqueValues(field))
            
        colors = {0: QColor('#2b83ba'),
                  1: QColor('#64abb0'),
                  2: QColor('#9dd3a7'),
                  3: QColor('#c7e9ad'),
                  4: QColor('#edf8b9'),
                  5: QColor('#ffedaa'),
                  6: QColor('#fec980'),
                  7: QColor('#f99e59'),
                  8: QColor('#e85b3a'),
                  9: QColor('#d7191c')}
        
        categories = []
        
        for cid, unique_value in enumerate(unique_values):
            # initialize the default symbol for this geometry type
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        
            # configure a symbol layer
            symbol_layer = QgsSimpleFillSymbolLayer(color=colors[cid],
                                                    strokeColor=QColor('#000000'))
        
            # replace default symbol layer with the configured one
            if symbol_layer is not None:
                symbol.changeSymbolLayer(0, symbol_layer)
        
            # create renderer object
            category = QgsRendererCategory(unique_value, symbol, str(unique_value) + legend_suffix)
            # entry for the list of category items
            categories.append(category)
        
        # create renderer object
        renderer = QgsCategorizedSymbolRenderer(field_name, categories)
        
        # assign the created renderer to the layer
        if renderer is not None:
            layer.setRenderer(renderer)
        layer.setOpacity(0.5)
        
        layer.triggerRepaint()