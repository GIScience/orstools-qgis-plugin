#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 19 10:39:11 2018

@author: nilsnolde
"""

from itertools import product

from PyQt4.QtGui import (QComboBox,
                             QLabel,
                             QCheckBox
                             )

from PyQt4.QtCore import QVariant

from qgis.core import (QgsVectorLayer,
                       QgsField, 
                       QgsPointXY,
                       QgsGeometry,
                       QgsFeature,
                       QgsProject
                       )

from . import convert, geocode, auxiliary

class directions:
    """
    Performs requests to the ORS directions API.
    """
    def __init__(self, dlg, client, iface):
        """
        :param dlg: Main OSMtools dialog window.
        :type dlg: QDialog
        
        :param client: Client to ORS API.
        :type client: OSMtools.client.Client()
        
        :param iface: A QGIS interface instance.
        :type iface: QgisInterface
        """
        self.dlg = dlg
        self.client = client
        self.iface = iface
        
        self.url = '/directions'        
        
        self.radio_buttons = (self.dlg.start_layer_radio,
                              self.dlg.end_layer_radio)
        
        # API parameters
        self.route_mode = self.dlg.route_mode_combo.currentText()
        self.route_pref = self.dlg.route_pref_combo.currentText()
        avoid_boxes = self.dlg.avoid_frame.findChildren(QCheckBox)
        
        self.params = {'profile': self.route_mode,
                    'preference': self.route_pref,
                    'geometry': 'true',
                    'geometry_format': 'geojson',
                    'instructions': 'false'
                    }
        
        
        # Check if avoid features is checked
        self.avoid_dict = dict()
        if any(box.isChecked() for box in avoid_boxes):
            avoid_features = []
            for box in avoid_boxes:
                if box.isChecked():
                    avoid_features.append((box.text()))
            avoid_features = convert._pipe_list(avoid_features)
            self.avoid_dict = dict()
            
            self.avoid_dict['avoid_features'] = avoid_features
        
        if self.avoid_dict:
            self.params['options'] = str(self.avoid_dict)
    
                    
    def directions_calc(self):
        """
        Main method to perform the actual request
        """
        
        # create route_dict, {'radio_button_name': {'geometries': list of coords,
        #                                           'values': list of values}}
        route_dict = self._selectInput()
        
        # generate lists with locations and values         
        (start_layer_name,
         end_layer_name) = [x.objectName() for x in self.radio_buttons]
        
        locations_list = list(product(route_dict[start_layer_name]['geometries'],
                                      route_dict[end_layer_name]['geometries']))
        values_list = list(product(route_dict[start_layer_name]['values'],
                                   route_dict[end_layer_name]['values']))
        
        # If row-by-row in two-layer mode, then only zip the locations
        if all([button.isChecked() for button in self.radio_buttons]) and self.dlg.row_by_row.isChecked():
            locations_list = list(zip(route_dict[start_layer_name]['geometries'],
                                          route_dict[end_layer_name]['geometries']))
            values_list = list(zip(route_dict[start_layer_name]['values'],
                                       route_dict[end_layer_name]['values']))
    
        route_via = None
        if self.dlg.via_label.text() != 'Long,Lat':
            route_via = [float(x) for x in self.dlg.via_label.text().split(",")]
                
        message_bar, progress_widget = auxiliary.pushProgressBar(self.iface)
        
        responses = []
        delete_values = []
        for i, coords_tuple in enumerate(locations_list):
            if coords_tuple[0] == coords_tuple[-1]:
                # Skip when same location
                delete_values.append(i)
                continue
            if route_via:
                # add via coords
                coords_tuple = list(coords_tuple)
                coords_tuple.insert(1, route_via)
            
            # Update progress bar
            percent = (i/len(locations_list)) * 100
            message_bar.setValue(percent)
            
            # Make the request
            self.params['coordinates'] = convert._build_coords(coords_tuple)
            responses.append(self.client.request(self.url, self.params))
        
        # Delete entries in values_list where coords where the same
        values_list = [value for idx, value in enumerate(values_list) if idx not in delete_values]
            
        # Only proceed when there actual responses
        if responses:        
            layer_out = self._addLine(responses, values_list)
            layer_out.updateExtents()
            
            QgsProject.instance().addMapLayer(layer_out)
            
        self.iface.messageBar().popWidget(progress_widget)
        
        
    def _addLine(self, responses, values_list):
        """
        :param responses: Collection of HTTP responses.
        :type responses: list
        
        :param values_list: List of feature ID's.
        :type values_list: list
        
        :rtype: QgsMapLayer
        """
        
        # Create memory routing layer with fields
        layer_out = QgsVectorLayer("LineString?crs=EPSG:4326", "Route_ORS", "memory")
        layer_out_prov = layer_out.dataProvider()
        layer_out_prov.addAttributes([QgsField("DISTANCE", QVariant.Double)])
        layer_out_prov.addAttributes([QgsField("TIME_H", QVariant.Double)])
        layer_out_prov.addAttributes([QgsField("MODE", QVariant.String)])
        layer_out_prov.addAttributes([QgsField("PREF", QVariant.String)])
        layer_out_prov.addAttributes([QgsField("AVOID_TYPE", QVariant.String)])
        layer_out_prov.addAttributes([QgsField("FROM_ID", QVariant.String)])
        layer_out_prov.addAttributes([QgsField("TO_ID", QVariant.String)])
        
        layer_out.updateFields()
        
        
        for i, response in enumerate(responses):
            resp_minified = response['routes'][0]
            feat = QgsFeature()
            coordinates = resp_minified['geometry']['coordinates']
            distance = resp_minified['summary']['distance']
            duration = resp_minified['summary']['duration']
            qgis_coords = [QgsPointXY(x, y) for x, y in coordinates]
            feat.setGeometry(QgsGeometry.fromPolylineXY(qgis_coords))
            feat.setAttributes(["{0:.3f}".format(distance/1000),
                               "{0:.3f}".format(duration/3600),
                               self.route_mode,
                               self.route_pref,
                               self.avoid_dict.get('avoid_features', ''),
                               values_list[i][0],
                               values_list[i][1]
                               ])
            layer_out.dataProvider().addFeature(feat)
                
        return layer_out
                
    def _selectInput(self):
        """
        Selects start and end features and returns them as a dict.
        
        :rtype: dict, {'radio_button_name': {'geometries': list of coords,
            'values': list of values}, 'other_radio_button':...}
        """
        route_dict = dict()
        for radio_button in self.radio_buttons:
            if radio_button.isChecked():
                # Find layer combo box
                all_combos = radio_button.parent().findChildren(QComboBox)
                layer_combo = [combo for combo in all_combos if combo.objectName().endswith('layer_combo')][0]  
                # Get selected layer                              
                layer_name = layer_combo.currentText()
                layer = [layer for layer in self.iface.mapCanvas().layers() if layer.name() == layer_name][0]
                
                # Check CRS and transform if necessary
                auxiliary.checkCRS(layer,
                             self.iface.messageBar())
                
                # If features are selected, calculate with those
                if layer.selectedFeatureCount() == 0:
                    feats = layer.getFeatures()
                else:
                    feats = layer.selectedFeatures()
                    
                # Get features
                point_geom = [feat.geometry().asPoint() for feat in feats]
                
                # Find field combo box
                field_combo = [combo for combo in all_combos if combo.objectName().endswith('layer_id')][0] 
                field_id = layer.fields().lookupField(field_combo.currentText())
                field_values = [feat[field_id] for feat in feats]
                
            else:
                parent_widget = radio_button.parentWidget()
                parent_widget_name = parent_widget.objectName()
                grandparent_widget = parent_widget.parentWidget()
                parent_widget_label = [child for child in grandparent_widget.children() if child.objectName() != parent_widget_name][1]
                
                point_label = parent_widget_label.findChild(QLabel)
                point_coords = [float(x) for x in point_label.text().split(",")]
                
                point_geom = [QgsPointXY(*point_coords)]
                response_dict = geocode.reverse_geocode(self.client, *point_geom)
                
                field_values = [response_dict.get('CITY', point_label.text())]
            
            # Get all id attributes from field
            route_dict[radio_button.objectName()] = {'geometries': point_geom,
                                                     'values': field_values}
            
        return route_dict