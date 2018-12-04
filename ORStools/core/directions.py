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

from ORStools.utils import convert, transform
from ORStools.gui import progressbar
from . import geocode


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
        
        self.radio_buttons = (self.dlg.routing_start_fromlayer_radio,
                              self.dlg.routing_end_fromlayer_radio)
        
        # API parameters
        self.route_mode = self.dlg.routing_travel_combo.currentText()
        self.route_pref = self.dlg.routing_preference_combo.currentText()

        self.params = {'profile': self.route_mode,
                        'preference': self.route_pref,
                        'geometry': 'true',
                        'geometry_format': 'geojson',
                        'instructions': 'false'
                        }

        # from Advanced dialog
        self.avoid_dict = None
        if self.dlg.advanced is not None:
            avoid_boxes = self.dlg.advanced.routing_avoid_group.findChildren(QCheckBox)
            if any(box.isChecked() for box in avoid_boxes):
                avoid_features = []
                for box in avoid_boxes:
                    if box.isChecked():
                        avoid_features.append((box.text()))
                avoid_features = convert.pipe_list(avoid_features)

                self.avoid_dict = dict()
                self.avoid_dict['avoid_features'] = avoid_features
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
        if all([button.isChecked() for button in self.radio_buttons]) and self.dlg.routing_twolayer_rowbyrow.isChecked():
            locations_list = list(zip(route_dict[start_layer_name]['geometries'],
                                      route_dict[end_layer_name]['geometries']))

            values_list = list(zip(route_dict[start_layer_name]['values'],
                                   route_dict[end_layer_name]['values']))

        # # Add via point if specified
        # route_via = None
        # if self.dlg.routing_via_label.text() != 'Long,Lat':
        #     route_via = [float(x) for x in self.dlg.routing_via_label.text().split(",")]
                
        message_bar, progress_widget = progressbar.pushProgressBar(self.iface)
        
        responses = []
        delete_values = []
        for i, coords_tuple in enumerate(locations_list):
            if coords_tuple[0] == coords_tuple[-1]:
                # Skip when same location
                delete_values.append(i)
                continue
            # if route_via:
            #     # add via coords
            #     coords_tuple = list(coords_tuple)
            #     coords_tuple.insert(1, route_via)
            
            # Update progress bar
            percent = (i/len(locations_list)) * 100
            message_bar.setValue(percent)
            
            # Make the request
            self.params['coordinates'] = convert.build_coords(coords_tuple)
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
        # select input for both, start and end features
        for radio_button in self.radio_buttons:
            # Check if routing_*_fromlayer_button is checked
            if radio_button.isChecked():
                # Find layer combo box
                all_combos = radio_button.parent().findChildren(QComboBox)
                # Get selected layer
                layer_name = [combo.currentText() for combo in all_combos if combo.objectName().endswith('layer_combo')][0]

                layer = [layer for layer in self.iface.mapCanvas().layers() if layer.name() == layer_name][0]
                
                # Check CRS and transform if necessary
                layer = transform.checkCRS(layer,
                                           self.iface.messageBar())
                
                # If features are selected, calculate with those, else the whole layer
                # Convert to list, bcs it's a QgsFeatureIterator
                if layer.selectedFeatureCount() == 0:
                    feats = list(layer.getFeatures())
                else:
                    feats = list(layer.selectedFeatures())
                    
                # Get features
                point_geom = [feat.geometry().asPoint() for feat in feats]
                
                # Find field combo box and save its name
                field_name = [combo.currentText() for combo in all_combos if combo.objectName().endswith('id_combo')][0]
                field_values = [feat.attribute(field_name) for feat in feats]

                # Retrieve field type to define the output field type
                field_id = layer.fields().lookupField(field_name)
                field_type = layer.fields().field(field_id).type()
                
            else:
                # Take the coords displayed in the routing_*_frommap_label field
                parent_widget = radio_button.parentWidget()
                parent_widget_name = parent_widget.objectName()
                grandparent_widget = parent_widget.parentWidget()
                parent_widget_label = [child for child in grandparent_widget.children() if child.objectName() != parent_widget_name][1]
                
                point_label = parent_widget_label.findChild(QLabel)
                point_coords = [float(x) for x in point_label.text().split(",")]
                
                point_geom = [QgsPointXY(*point_coords)]
                response_dict = geocode.reverse_geocode(self.client, *point_geom)
                
                field_values = [response_dict.get('CITY', point_label.text())]
                field_type = QVariant.String
            
            # Get all id attributes from field
            route_dict[radio_button.objectName()] = {'geometries': point_geom,
                                                     'values': field_values,
                                                     'type': field_type}
            
        return route_dict
