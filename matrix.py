#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 23 15:49:29 2018

@author: nilsnolde
"""

import os.path
from itertools import product

from PyQt4.QtGui import QComboBox

from PyQt4.QtCore import QVariant

from qgis.core import (QgsVectorLayer,
                       QgsField,
                       QgsFeature,
                       QgsMapLayerRegistry
                       )

from OSMtools import auxiliary


class matrix:
    """
    Performs requests to the ORS matrix API.
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
        self.plugin_dir = os.path.dirname(__file__)
        
        self.url = '/matrix'        
        
        self.combo_boxes = (self.dlg.matrix_start_combo, self.dlg.matrix_end_combo)
        
        # API parameters
        self.matrix_mode = self.dlg.matrix_mode_combo.currentText()
#        self.matrix_metrics = self.dlg.matrix_metric_combo.currentText()
        
        self.params = {'profile': self.dlg.matrix_mode_combo.currentText(),
                    'metrics': 'distance|duration'
                    }
        
    
    def matrix_calc(self):
        """
        Main method to perform the actual request
        """
        
        # create route_dict, {'combobox_name': {'geometries': list of coords,
        #                                       'values': list of values}}
        route_dict = self._selectInput()
        
        start_box_name  = self.combo_boxes[0].objectName()
        end_box_name  = self.combo_boxes[1].objectName()
        # generate lists with locations and values      
        locations_list = route_dict[start_box_name]['geometries'] + \
                         route_dict[end_box_name]['geometries']
        values_list = route_dict[start_box_name]['values'] + \
                         route_dict[end_box_name]['values']
        
        ids = list(range(len(locations_list)))
        destinations_amount = len(route_dict[end_box_name]['geometries'])
        sources = ids[:destinations_amount]
        destinations = ids[destinations_amount:]        
        
        values_list = list(product(values_list[:destinations_amount],
                                   values_list[destinations_amount:]))

        # Make the request
        self.params['locations'] = locations_list
        self.params['sources'] = sources
        self.params['destinations'] = destinations
        response = self.client.request(self.url, {}, post_json=self.params)
        
        
        durations = [item for sublist in response['durations'] for item in sublist]
        distances = [item for sublist in response['distances'] for item in sublist]
        
        layer_out = QgsVectorLayer('None', "Matrix_ORS", "memory")
        layer_out_prov = layer_out.dataProvider()
        layer_out_prov.addAttributes([QgsField("FROM_ID", QVariant.String)])
        layer_out_prov.addAttributes([QgsField("TO_ID", QVariant.String)])
        layer_out_prov.addAttributes([QgsField("DURATION_HOURS", QVariant.String)])
        layer_out_prov.addAttributes([QgsField("DISTANCE_KM", QVariant.String)])
        
        for row in range(len(values_list)):    
            feat = QgsFeature()
            feat.setAttributes([values_list[row][0],
                             values_list[row][1],
                             durations[row]/3600,
                             distances[row]/1000])
            layer_out_prov.addFeatures([feat])
        
        layer_out.updateFields()
    
        QgsMapLayerRegistry.instance().addMapLayer(layer_out)
        
        
    def _selectInput(self):
        """
        Selects start and end features and returns them as a dict.
        ues_list)):    
#            feat = QgsFeature()
#            feat.setAttributes([values_list[row][0],
#                             values_list[row][1],
#                             durations[row]/3600,
#                             distances[row]/1000])
#            layer_out_prov.addFeature(feat)
        :rtype: dict, {'radio_button_name': {'geometries': list of coords,
            'values': list of values}, 'other_radio_button':...}
        """
        route_dict = dict()
        for combo in self.combo_boxes: 
            # Get selected layer                              
            layer_name = combo.currentText()
            layer = [layer for layer in QgsMapLayerRegistry.instance().mapLayers().values() if layer.name() == layer_name][0]
            
            # Check CRS and transform if necessary
            auxiliary.checkCRS(layer,
                         self.iface.messageBar())
            
            # If features are selected, calculate with those
            if layer.selectedFeatureCount() == 0:
                feats = layer.getFeatures()
            else:
                feats = layer.selectedFeatures()
                
            # Get features
            point_geom = [list(feat.geometry().asPoint()) for feat in feats]
            
            # Find field combo box
            all_combos = combo.parent().findChildren(QComboBox)
            field_combo = [box for box in all_combos if box.objectName().endswith('_id')][0] 
            field_id = layer.fields().indexFromName(field_combo.currentText())
            field_values = [feat[field_id] for feat in feats]
            
            # Get all id attributes from field
            route_dict[combo.objectName()] = {'geometries': point_geom,
                                              'values': field_values}
            
        return route_dict
        
        