# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ORStools
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
"""
Contains isochrones class to perform requests to ORS isochrone API.
"""

from PyQt5.QtWidgets import (QComboBox,
                             QLabel,
                             QCheckBox)
from PyQt5.QtCore import QVariant

from qgis.core import QgsProject, QgsPointXY, QgsGeometry, QgsCoordinateReferenceSystem, QgsVectorLayer

from ORStools.core import directions_core
from ORStools.utils import convert, transform


class Directions():

    def __init__(self, dlg, advanced):
        self.dlg = dlg
        self.advanced = advanced

        self.radio_buttons = {
            'start': dlg.routing_start_fromlayer_radio,
            'end': dlg.routing_end_fromlayer_radio
        }
        self.crs = QgsCoordinateReferenceSystem(4326)
        self.fieldtype_to = None
        self.fieldtype_from = None

        self.avoid = None

    def get_id_field_types(self):
        field_types = dict()
        for name in self.radio_buttons:
            # Check if routing_*_fromlayer_button is checked
            radio_button = self.radio_buttons[name]
            if radio_button.isChecked():
                # Find layer combo box
                combo_layer_all = radio_button.parent().findChildren(QComboBox)
                combo_layer_layer = [combo for combo in combo_layer_all if combo.objectName().endswith('layer_combo')][0]
                combo_layer_field = [combo for combo in combo_layer_all if combo.objectName().endswith('id_combo')][0]
                # Get selected layer
                layer = QgsProject().instance().mapLayer(combo_layer_layer.currentData())

                field_name = combo_layer_field.currentText()

                # Retrieve field type to define the output field type
                field_id = layer.fields().lookupField(field_name)
                field_type = layer.fields().field(field_id).type()
                field_types[name] = field_type
            else:
                field_type = QVariant.Int

                field_types[name] = field_type

        return field_types

    def get_route_count(self):
        route_dict = self._selectInput()

        # If row-by-row in two-layer mode, then only zip the locations
        if all([button.isChecked() for button in self.radio_buttons.values()]) and self.dlg.routing_twolayer_rowbyrow.isChecked():
            return min([len(route_dict['start']['geometries']), len(route_dict['end']['geometries'])])
        else:
            return len(route_dict['start']['geometries']) * len(route_dict['end']['geometries'])


    def get_basic_paramters(self):

        avoid_boxes = self.advanced.routing_avoid_group.findChildren(QCheckBox)

        # API parameters
        route_mode = self.dlg.routing_travel_combo.currentText()
        route_pref = self.dlg.routing_preference_combo.currentText()

        params = {
            'profile': route_mode,
            'preference': route_pref,
            'geometry': 'true',
            'format': 'geojson',
            'geometry_format': 'geojson',
            'instructions': 'false',
            'id': None,
        }

        self.avoid = self._get_advanced_parameters(avoid_boxes)
        if self.avoid is not None:
            params['options'] = self.avoid

        return params

    def get_request_features(self):

        route_dict = self._selectInput()
        row_by_row = False

        # If row-by-row in two-layer mode, then only zip the locations
        if all([button.isChecked() for button in self.radio_buttons.values()]) and self.dlg.routing_twolayer_rowbyrow.isChecked():
            row_by_row = True

        return directions_core.get_request_features(route_dict, row_by_row)

    def get_linestring_layer(self):
        field_types = self.get_id_field_types()
        # Create memory routing layer with fields
        layer_out = QgsVectorLayer("LineString?crs=EPSG:4326", "Route_ORS", "memory")
        layer_out.dataProvider().addAttributes(directions_core.get_fields(
            field_types['start'],
            field_types['end'],
        ))
        layer_out.updateFields()

        return layer_out

    def _get_advanced_parameters(self, avoid_boxes):

        # from Advanced dialog
        avoid_dict = dict()
        if any(box.isChecked() for box in avoid_boxes):
            avoid_features = []
            for box in avoid_boxes:
                if box.isChecked():
                    avoid_features.append((box.text()))
            avoid_features = convert.pipe_list(avoid_features)

            avoid_dict['avoid_features'] = avoid_features

            return str(avoid_dict)

    def _selectInput(self):
        """
        Selects start and end features and returns them as a dict.

        :rtype: dict, {'radio_button_name': {'geometries': list of coords,
            'values': list of values}, 'other_radio_button':...}
        """
        route_dict = dict()
        # select input for both, start and end features
        for name in self.radio_buttons:
            # Check if routing_*_fromlayer_button is checked
            radio_button = self.radio_buttons[name]
            if radio_button.isChecked():
                # Find layer combo box
                combo_layer_all = radio_button.parent().findChildren(QComboBox)
                combo_layer_layer = [combo for combo in combo_layer_all if combo.objectName().endswith('layer_combo')][0]
                combo_layer_field = [combo for combo in combo_layer_all if combo.objectName().endswith('id_combo')][0]

                # Get selected layer
                layer = QgsProject().instance().mapLayer(combo_layer_layer.currentData())

                # If features are selected, calculate with those, else the whole layer
                # Convert to list, bcs it's a QgsFeatureIterator
                if layer.selectedFeatureCount() == 0:
                    feats = list(layer.getFeatures())
                else:
                    feats = list(layer.selectedFeatures())

                # Transform and get feature geometries
                xformer = transform.transformToWGS(layer.crs())
                point_geom = [xformer.transform(feat.geometry().asPoint()) for feat in feats]

                field_name = combo_layer_field.currentText()
                field_values = [feat.attribute(field_name) for feat in feats]

                # Retrieve field type to define the output field type
                field_id = layer.fields().lookupField(field_name)
                field_type = layer.fields().field(field_id).type()

            else:
                # Take the coords displayed in the routing_*_frommap_label field
                parent_group_widget = radio_button.parentWidget()
                parent_widget_name = parent_group_widget.objectName()
                grandparent_widget = parent_group_widget.parentWidget()
                parent_widget_label = \
                [child for child in grandparent_widget.children() if child.objectName() != parent_widget_name][1]

                point_label = parent_widget_label.findChild(QLabel)
                # TODO: warning message when no coordiates have been specified: QMessage.warning() or so
                point_coords = [float(x) for x in point_label.text().split(",")]

                point_geom = [QgsPointXY(*point_coords)]

                field_values = point_label.text()
                field_type = QVariant.String

            # Get all id attributes from field
            route_dict[name] = {'geometries': point_geom,
                                 'values': field_values,
                                'type': field_type}

        return route_dict
