# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ORStools
                                 A QGIS plugin
 QGIS client to query openrouteservice
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

import json

from PyQt5.QtWidgets import QCheckBox

from ORStools.utils import convert


class Directions:
    """Extended functionality for directions endpoint for GUI."""
    def __init__(self, dlg):
        """
        :param dlg: Main GUI dialog.
        :type dlg: QDialog
        """
        self.dlg = dlg

        self.options = dict()

    def get_parameters(self):
        """
        Builds parameters across directions functionalities.

        :returns: All parameter mappings except for coordinates.
        :rtype: dict
        """

        if self.dlg.optimization_group.isChecked():
            return self._get_optimize_parameters()

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

        # Get Advanced parameters
        if self.dlg.routing_avoid_tags_group.isChecked():
            avoid_boxes = self.dlg.routing_avoid_tags_group.findChildren(QCheckBox)
            if any(box.isChecked() for box in avoid_boxes):
                self.options['avoid_features'] = self._get_avoid_options(avoid_boxes)

        if self.options:
            params['options'] = json.dumps(self.options)

        return params

    def get_request_line_feature(self):
        """
        Extracts all coordinates for the list in GUI.

        :returns: coordinate list of line
        :rtype: list
        """
        coordinates = []
        layers_list = self.dlg.routing_fromline_list
        for idx in range(layers_list.count()):
            item = layers_list.item(idx).text()
            param, coords = item.split(":")

            coordinates.append([float(coord) for coord in coords.split(', ')])

        return coordinates

    def _get_avoid_options(self, avoid_boxes):
        """
        Extracts checked boxes in Advanced avoid parameters.

        :param avoid_boxes: all checkboxes in advanced paramter dialog.
        :type avoid_boxes: list of QCheckBox

        :returns: avoid_features parameter
        :rtype: JSON dump, i.e. str
        """
        avoid_features = []
        for box in avoid_boxes:
            if box.isChecked():
                avoid_features.append((box.text()))
        avoid_features = convert.pipe_list(avoid_features)

        return avoid_features

    def _get_optimize_parameters(self):
        """Return parameters for optimization waypoint"""
        coordinates = self.get_request_line_feature()

        params = {
            'jobs': list(),
            'vehicles': [{
                "id": 0,
                "profile": self.dlg.routing_travel_combo.currentText()
            }],
            'options': {'g': True}
        }

        if self.dlg.optimize_end.isChecked():
            end = coordinates.pop(-1)
            params['vehicles'][0]['end'] = end
        elif self.dlg.optimize_start.isChecked():
            start = coordinates.pop(0)
            params['vehicles'][0]['start'] = start
        elif self.dlg.optimize_none.isChecked():
            start = coordinates.pop(0)
            end = coordinates.pop(-1)
            params['vehicles'][0]['start'] = start
            params['vehicles'][0]['end'] = end

        for coord in coordinates:
            params['jobs'].append({
                "location": coord,
                "id": coordinates.index(coord)
            })

        return params
