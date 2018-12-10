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

from ORStools.utils import convert, transform


def get_request_parameters(dlg):

    iso_mode = dlg.iso_travel_combo.currentText()

    dimension = dlg.iso_unit_combo.currentText()
    factor = 60 if dimension == 'time' else 1
    iso_range_input = [x * factor for x in map(int, dlg.iso_range_text.text().split(','))]

    params = {
        'range_type': dimension,
        'profile': iso_mode,
        'range': convert.comma_list(iso_range_input),
        'attributes': 'total_pop'
    }

    params['locations'], params['id'] = _get_feature_parameters(dlg.iso_location_label.text())

    return params


def _get_feature_parameters(location_label):
        coords = [float(x) for x in location_label.split('\n')[:2]]

        return convert.build_coords(coords), '-1'

