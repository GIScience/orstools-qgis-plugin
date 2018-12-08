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

from qgis.core import (QgsVectorLayer,
                       QgsFeature,
                       QgsWkbTypes,
                       QgsCoordinateReferenceSystem,
                       QgsCoordinateTransform,
                       QgsProject)


# def checkCRS(layer, messageBar):
#     """
#     Check if layer CRS is EPSG:4326.
#
#     :param layer: Layer to be inspected.
#     :type layer: QgsMapLayer
#
#     :param messageBar: QGIS interface message bar.
#     :type messageBar: QgsMessageBar
#     """
#     layer_crs = layer.crs().authid()
#     if layer_crs.split(':')[1] != '4326':
#         layer = transformToWGS(layer, layer_crs)
#         messageBar.pushInfo('CRS conflict',
#                             'The input layer CRS is {}, the output layer '
#                             'CRS will be EPSG:4326'.format(layer_crs))
#
#     return layer


def transformToWGS(old_layer, old_crs):

    geom_string = QgsWkbTypes.geometryDisplayString(old_layer.geometryType())
    new_layer = QgsVectorLayer("{}?crs=EPSG:4326".format(geom_string), old_layer.name(), "memory")
    new_layer.dataProvider().addAttributes(old_layer.fields())
    new_layer.updateFields()

    new_crs = QgsCoordinateReferenceSystem(4326)
    old_crs = QgsCoordinateReferenceSystem(old_crs)
    xform = QgsCoordinateTransform(old_crs, new_crs, QgsProject.instance())

    for o in old_layer.getFeatures():
        n = QgsFeature()
        g = o.geometry()
        g.transform(xform)
        n.setGeometry(g)
        n.setAttributes(o.attributes())

        new_layer.dataProvider().addFeature(n)

    new_layer.updateExtents()

    return new_layer
