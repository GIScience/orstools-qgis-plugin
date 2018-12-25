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
    def __init__(self, dlg, advanced):
        """
        :param dlg: Main GUI dialog.
        :type dlg: QDialog

        :param advanced: Advanced parameters dialog.
        :type advanced: QDialog
        """
        self.dlg = dlg
        self.advanced = advanced

        self.avoid = None

    def get_basic_paramters(self):
        """
        Builds basic common parameters across directions functionalities.

        :returns: All parameter mappings except for coordinates.
        :rtype: dict
        """
        avoid_boxes = self.advanced.routing_avoid_tags_group.findChildren(QCheckBox)

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

    def _get_advanced_parameters(self, avoid_boxes):
        """
        Extracts checked boxes in Advanced parameters.

        :param avoid_boxes: all checkboxes in advanced paramter dialog.
        :type avoid_boxes: list of QCheckBox

        :returns: avoid_features parameter
        :rtype: JSON dump, i.e. str
        """

        # from Advanced dialog
        avoid_dict = dict()
        if any(box.isChecked() for box in avoid_boxes):
            avoid_features = []
            for box in avoid_boxes:
                if box.isChecked():
                    avoid_features.append((box.text()))
            avoid_features = convert.pipe_list(avoid_features)

            avoid_dict['avoid_features'] = avoid_features

            return json.dumps(avoid_dict)
