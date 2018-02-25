#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI logic for the Isochrones tab, after clicking ok in the dialog
"""

from PyQt4.QtCore import QVariant
from PyQt4.QtGui import QColor

from qgis.core import (QgsPoint,
                       QgsVectorLayer,
                       QgsFeature,
                       QgsField,
                       QgsGeometry,
                       QgsMapLayerRegistry)

from OSMtools.core import geocode, auxiliary

from OSMtools.core import isochrones

class Isochrones:
    """
    Performs requests to ORS isochrone API:
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

        # read + prepare params
        self.profile = self.dlg.access_mode_combo.currentText() # TODO: what is this??
        self.metric = self.dlg.access_unit_combo.currentText()
        self.factor = 60 if self.metric == 'time' else 1000
        self.ranges = list(map(int,self.dlg.access_range.text().split(',')))
        self.ranges = [x * self.factor for x in self.ranges]


    def isochrones_calc(self):
        """
        Performs requests to the ORS isochrone API.
        """
        if self.dlg.access_layer_check.isChecked():
            layer_name = self.dlg.access_layer_combo.currentText()
            layer = [layer for layer in self.iface.mapCanvas().layers() if layer.name() == layer_name][0]

            auxiliary.checkCRS(layer, self.iface.messageBar())

            # If features are selected, calculate with those
            if layer.selectedFeatureCount() == 0:
                feats = layer.getFeatures()
                feat_count = layer.featureCount()
            else:
                feats = layer.selectedFeatures()
                feat_count = layer.selectedFeatureCount()

            message_bar, progress_widget = auxiliary.pushProgressBar(self.iface)

            try:
                responses = []
                for i, feat in enumerate(feats):
                    percent = (i/float(feat_count)) * 100
                    message_bar.setValue(percent)
                    p = feat.geometry().asPoint()
                    res = isochrones.requestFromPoint(self.client, p,
                                                      self.metric, self.ranges,
                                                      self.profile)
                    responses.append(res)
            finally:
                self.iface.messageBar().popWidget(progress_widget)


        else:
            # Define the mapped point
            coords = [float(x) for x in self.dlg.access_map_label.text().split('\n')[:2]]
            in_point_geom = QgsPoint(*coords)
            response_dict = geocode.reverse_geocode(self.client, in_point_geom)

            # Fire request
            responses = [isochrones.requestFromPoint(self.client, in_point_geom,
                                                     self.metric, self.ranges,
                                                     self.profile)]

            out_point_geom = QgsPoint(*responses[0]['features'][0]['properties']['center'])
            layer_name = "{0:.3f},{1:.3f}".format(*responses[0]['features'][0]['properties']['center'])
            point_out = self._addPoint(response_dict, out_point_geom, layer_name)
            point_out.updateExtents()
            QgsMapLayerRegistry.instance().addMapLayer(point_out)


        poly_out = isochrones.layerFromRequests(responses)
        poly_out.setLayerName("Isochrone_{}".format(layer_name))

        QgsMapLayerRegistry.instance().addMapLayer(poly_out)
#        self.iface.mapCanvas().zoomToFeatureExtent(poly_out.extent())



    def _addPoint(self, response_dict, point_geom, name_ext):
        """
        Get point layer from Map button.

        :param response_dict: Response from geocoding request.
        :type response_dict: dict from JSON

        :param point_geom: Point coordinates from geocoding request.
        :type point_geom: QgsPoint

        :param name_ext: Name extension for layer.
        :type name_ext: str

        :rtype: QgsMapLayer
        """
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
        point_feat.setGeometry(QgsGeometry.fromPoint(point_geom))
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
