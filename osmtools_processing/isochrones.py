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
from qgis.core import QGis, QgsCoordinateReferenceSystem, QgsCoordinateTransform

from processing import features
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import (
    ParameterVector,
    ParameterString,
    ParameterFixedTable
)
from processing.core.outputs import OutputVector
from processing.tools.dataobjects import getObjectFromUri

from OSMtools.core.client import Client
from OSMtools.core.exceptions import InvalidParameterException
from OSMtools.core.isochrones import (
    ISOCHRONES_METRICS,
    ISOCHRONES_PROFILES,
    requestFromPoint,
    layerFromRequests,
)

class IsochronesGeoAlg(GeoAlgorithm):
    """
    GeoAlgorithm fetching isochrone polygons for a point layer via ORS
    """

    # these names will be visible in console & outputs
    IN_POINTS = 'INPUT_POINTS'
    IN_PROFILE = 'INPUT_PROFILE'
    IN_METRIC = 'INPUT_METRIC'
    IN_RANGES = 'INPUT_RANGES'
    IN_KEY    = 'INPUT_APIKEY'
    OUT = 'OUTPUT'

    def __init__(self):
        GeoAlgorithm.__init__(self)

    def getIcon(self):
        return QIcon(join(dirname(__file__), '../icon.png'))

    def defineCharacteristics(self):
        self.name = 'ORS Isochrones'
        self.group = 'API'

        self.addParameter(ParameterVector(self.IN_POINTS,
                                          self.tr('Central Points Layer'),
                                          ParameterVector.VECTOR_TYPE_POINT))
        self.addParameter(ParameterString(self.IN_PROFILE,
                                          ' '.join([self.tr('Profile'), str(ISOCHRONES_PROFILES)]),
                                          ISOCHRONES_PROFILES[0]))
        self.addParameter(ParameterString(self.IN_METRIC,
                                          ' '.join([self.tr('Metric'), str(ISOCHRONES_METRICS)]),
                                          ISOCHRONES_METRICS[0]))
        self.addParameter(ParameterFixedTable(self.IN_RANGES,
                                              self.tr('Range Values (in seconds or meters'),
                                              1, ['range']))
        self.addParameter(ParameterString(self.IN_KEY,
                                          self.tr('API Key (can be omitted if set in config.yml)'),
                                          optional=True))

        self.addOutput(OutputVector(self.OUT, self.tr('Isochrones')))

    def processAlgorithm(self, progress):
        progress.setPercentage(0)
        progress.setInfo('Initializing')

        apiKey = self.getParameterValue(self.IN_KEY)
        profile = self.getParameterValue(self.IN_PROFILE)
        metric = self.getParameterValue(self.IN_METRIC)
        ranges = self.getParameterValue(self.IN_RANGES)
        ranges = list(map(int, ranges.split(',')))
        client = Client(None, apiKey)
        pointLayer = getObjectFromUri(self.getParameterValue(self.IN_POINTS))

        # ORS understands WGS84 only, so we convert all points before sending
        # don't use auxiliary.checkCRS(), bc we don't want any GUI dependencies in processing
        outCrs = QgsCoordinateReferenceSystem(4326)
        transformer = QgsCoordinateTransform(pointLayer.crs(), outCrs)

        processedFeatureCount = 0
        totalFeatureCount = pointLayer.featureCount()
        totalFeatureCount = 100.0 / max(totalFeatureCount, 1)

        progress.setInfo('Processing each point')
        responses = []
        for feature in features(pointLayer):

            feature.geometry().transform(transformer)
            point = feature.geometry().asPoint()

            responses.append(requestFromPoint(client, point, metric, ranges, profile))

            processedFeatureCount += 1
            progress.setPercentage(int(processedFeatureCount * totalFeatureCount))

        progress.setInfo('Parsing isochrones layer')
        output = self.getOutputFromName(self.OUT)

        # we abuse this function for its sideeffect. to get a layer from the
        # correct provider (-> ouput.layer)
        output.getVectorWriter([], QGis.WKBPolygon, outCrs)

        layerFromRequests(responses, output.layer)
