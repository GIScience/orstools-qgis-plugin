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

class IsochronesGui:
    """GUI control for isochrones tab"""

    def __init__(self, dlg):
        self._dlg = dlg
        self._iface = self._dlg.iface
        self._project = self._dlg.project
        self.feature_count = 1

        self._iso_mode = self._dlg.iso_travel_combo.currentText()

        self._dimension = self._dlg.iso_unit_combo.currentText()
        self._factor = 60 if self._dimension == 'time' else 1
        self._iso_range_input = [x * self._factor for x in map(int, self.dlg.iso_range_text.text().split(','))]

    def getParameters(self):

        params = {
            'range_type': self._dimension,
            'profile': self._iso_mode,
            'range': convert.comma_list(self._iso_range_input),
        }

        return params

    def getFeatureParameters(self, isLayerChecked):
        if isLayerChecked:
            layer = self._project.mapLayer(self._dlg.iso_layer_combo.currentData())

            # Reproject layer if necessary
            layer_crs = layer.crs().authid()
            if not layer_crs.endswith('4326'):
                layer = transform.transformToWGS(layer, layer_crs)

            locations_ids = []
            # Only selected features if applicable
            features_selected = layer.selectedFeatureCount() != 0
            feats = layer.getFeatures() if not features_selected else layer.selectedFeatures()
            self.feature_count = layer.featureCount() if not features_selected else layer.selectedFeatureCount()
            for feat in feats:
                geom = feat.geometry().asPoint()
                coords = [geom.x(), geom.y()]

                yield convert.build_coords(coords), str(feat.id())

        else:
            coords = [float(x) for x in self._dlg.iso_location_label.text().split('\n')[:2]]

            yield convert.build_coords(coords), '-1'

