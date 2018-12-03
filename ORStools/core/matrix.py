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
from itertools import product

from PyQt5.QtWidgets import (QComboBox,
                             QLabel,
                             QCheckBox
                             )

from PyQt5.QtCore import QVariant

from qgis.core import (QgsVectorLayer,
                       QgsField, 
                       QgsPointXY,
                       QgsGeometry,
                       QgsFeature,
                       QgsProject
                       )

from OSMtools.utils import convert, transform
from OSMtools.gui import progressbar
from . import geocode


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
        _profile = self.dlg.matrix_travel_combo.currentText()
        self.params = {'profile': _profile,
                       'metrics': 'distance|duration'
                       }
        self.get_params = {'profile': _profile}

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
        origins_amount = len(route_dict[start_box_name]['geometries'])

        sources = ids[:origins_amount]
        destinations = ids[origins_amount:]
        
        values_list = list(product(values_list[:origins_amount],
                                   values_list[origins_amount:]))

        # Make the request
        self.params['locations'] = locations_list
        self.params['sources'] = sources
        self.params['destinations'] = destinations
        response = self.client.request(self.url, self.get_params, post_json=self.params)
        
        durations = [item for sublist in response['durations'] for item in sublist]
        distances = [item for sublist in response['distances'] for item in sublist]
        
        layer_out = QgsVectorLayer('None', 'Matrix_ORS', 'memory')
        layer_out_prov = layer_out.dataProvider()
        layer_out_prov.addAttributes([QgsField("FROM_ID", route_dict[start_box_name]['type'])])
        layer_out_prov.addAttributes([QgsField("TO_ID", route_dict[end_box_name]['type'])])
        layer_out_prov.addAttributes([QgsField("DURATION_HOURS", QVariant.Double)])
        layer_out_prov.addAttributes([QgsField("DISTANCE_KM", QVariant.Double)])

        layer_out.updateFields()
        
        for row in range(len(values_list)):    
            feat = QgsFeature()
            feat.setAttributes([values_list[row][0],
                                values_list[row][1],
                                durations[row]/3600,
                                distances[row]/1000])
            layer_out_prov.addFeature(feat)
    
        QgsProject.instance().addMapLayer(layer_out)

    def _selectInput(self):
        """
        Selects start and end features and returns them as a dict.

        :rtype: dict, {'radio_button_name': {'geometries': list of coords,
            'values': list of values}, 'other_radio_button':...}
        """
        route_dict = dict()
        for combo in self.combo_boxes: 
            # Get selected layer                              
            layer_name = combo.currentText()
            layer = [layer for layer in self.iface.mapCanvas().layers() if layer.name() == layer_name][0]
            
            # Check CRS and transform if necessary
            layer = transform.checkCRS(layer,
                                       self.iface.messageBar())
            
            # If features are selected, calculate with those
            if layer.selectedFeatureCount() == 0:
                feats = list(layer.getFeatures())
            else:
                feats = list(layer.selectedFeatures())
                
            # Get features
            point_geom = [list(feat.geometry().asPoint()) for feat in feats]

            # Get all id attributes from field
            all_combos = combo.parent().findChildren(QComboBox)
            field_name = [box.currentText() for box in all_combos if box.objectName().endswith('_id_combo')][0]
            field_values = [feat.attribute(field_name) for feat in feats]

            # Retrieve field type to define the output field type
            field_id = layer.fields().lookupField(field_name)
            field_type = layer.fields().field(field_id).type()

            route_dict[combo.objectName()] = {'geometries': point_geom,
                                              'values': field_values,
                                              'type': field_type}
            
        return route_dict
        
        