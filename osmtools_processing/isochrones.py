# -*- coding: utf-8 -*-

"""
/***************************************************************************
 OSMtools processing
                             -------------------
        begin                : 2017-02-25
        copyright            : (C) 2017 by Norwin Roosen
        email                : github.com/noerw
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Norwin Roosen'
__date__ = '2018-02-25'
__copyright__ = '(C) 2018 by Norwin Roosen'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from os.path import dirname, join
from PyQt4.QtGui import QIcon
from PyQt4.QtCore import QVariant
from qgis.core import QGis, QgsFeature, QgsField, QgsCoordinateReferenceSystem, QgsCoordinateTransform

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterVector, ParameterString, ParameterFixedTable, ParameterSelection
from processing.core.outputs import OutputVector
from processing.tools.dataobjects import getObjectFromUri

from OSMtools.exceptions import InvalidParameterException
from OSMtools.convert import _comma_list

class IsochronesGeoAlg(GeoAlgorithm):
    """
    Prepares the Microm Wohngebaeude data (Hausebene)
    """

    # these names will be visible in console & outputs
    IN_POINTS = 'INPUT_POINTS'
    IN_KEY    = 'INPUT_APIKEY'
    IN_RANGES = 'INPUT_RANGES'
    IN_METRIC = 'INPUT_METRIC'
    OUT = 'OUTPUT'

    METRICS = ['duration', 'distance']

    def __init__(self):
        GeoAlgorithm.__init__(self)

    def getIcon(self):
        return QIcon(join(dirname(__file__), '../icon.png'))

    def defineCharacteristics(self):
        self.name = 'OSM Isochrones'
        self.group = 'API'

        self.addParameter(ParameterString(self.IN_KEY, 'API Key'))
        self.addParameter(ParameterVector(self.IN_POINTS,
                                          self.tr('Central Points Layer'),
                                          ParameterVector.VECTOR_TYPE_POINT))
        self.addParameter(ParameterString(self.IN_METRIC,
                                          ' '.join([self.tr('Metric'), str(self.METRICS)]),
                                          'duration')) # TODO: select between two values?
        self.addParameter(ParameterFixedTable(self.IN_RANGES,
                                              self.tr('Range Values'),
                                              1, ['range']))

        self.addOutput(OutputVector(self.OUT, self.tr('Isochrones')))

    def processAlgorithm(self, progress):
        progress.setPercentage(0)
        progress.setInfo('Initializing')

        apiKey = self.getParameterValue(self.IN_KEY)
        metric = self.getParameterValue(self.IN_METRIC)
        ranges = self.getParameterValue(self.IN_RANGES)
        output = self.getOutputFromName(self.OUT)

        if metric not in self.METRICS:
            raise InvalidParameterException(self.IN_METRIC, metric, self.METRICS)

        if ranges == '0':
            raise InvalidParameterException(self.IN_RANGES, ranges)
        else:
            # ensure correct format for robustness of API changes
            ranges = _comma_list(','.split(ranges))

        pointLayer = getObjectFromUri(self.getParameterValue(self.IN_POINTS))

        # ORS only understands WGS85, so we convert all points before sending
        # don't use auxiliary.checkCRS(), bc we don't want any GUI dependencies in processing
        outCrs = QgsCoordinateReferenceSystem(4326)
        transformer = QgsCoordinateTransform(pointLayer.crs(), outCrs)

        isochronesFields = [] # TODO
        writer = output.getVectorWriter(
            isochronesFields,
            QGis.WKBPolygon, outCrs
        )

        processedFeatureCount = 0
        totalFeatureCount = pointLayer.featureCount()
        totalFeatureCount = 100.0 / max(totalFeatureCount, 1)

        progress.setInfo('Processing each point')
        for feature in pointLayer.getFeatures():

            feature.geometry().transform(transformer)

            # TODO

            self.writeFeature(feature.geometry(), [], writer)
            processedFeatureCount += 1
            progress.setPercentage(int(processedFeatureCount * totalFeatureCount))

    def writeFeature(self, point, attrs, writer):
        outFeat = QgsFeature()
        outFeat.setGeometry(point)
        outFeat.setAttributes([])
        writer.addFeature(outFeat)
