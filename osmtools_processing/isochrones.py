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
from qgis.core import (
    QGis,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFields,
)

from processing import features, runalg
from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import (
    ParameterVector,
    ParameterString,
    ParameterBoolean
)
from processing.core.outputs import OutputVector
from processing.tools.vector import VectorWriter
from processing.tools.dataobjects import getObjectFromUri, getTempFilename

from OSMtools.core.client import Client
from OSMtools.core.isochrones import (
    ISOCHRONES_METRICS,
    ISOCHRONES_PROFILES,
    requestFromPoint,
    layerFromRequests,
    _stylePoly
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
    IN_SIMPLIFY = 'INPUT_SIMPLIFY'
    OUT = 'OUTPUT'

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
        self.addParameter(ParameterString(self.IN_RANGES,
                                          self.tr('Range Values (commaseparated, in seconds or meters)'),
                                          '180'))
        self.addParameter(ParameterString(self.IN_KEY,
                                          self.tr('API Key (can be omitted if set in config.yml)'),
                                          optional=True))
        self.addParameter(ParameterBoolean(self.IN_SIMPLIFY,
                                           self.tr('Simplify geometry'),
                                           True))

        self.addOutput(OutputVector(self.OUT, self.tr('Isochrones')))

    def processAlgorithm(self, progress):
        progress.setPercentage(0)
        progress.setInfo('Initializing')

        simplify = self.getParameterValue(self.IN_SIMPLIFY)
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

        progress.setInfo('Processing each selected point')
        responses = []
        for feature in features(pointLayer):

            feature.geometry().transform(transformer)
            point = feature.geometry().asPoint()

            responses.append(requestFromPoint(client, point, metric, ranges, profile))

            processedFeatureCount += 1
            progress.setPercentage(int(processedFeatureCount * totalFeatureCount))

        progress.setInfo('Parsing isochrones layer')
        # get isochrones + store in temp layer
        tmpFile = getTempFilename() + '.shp' # qgis:dissolve only supports shp as input :(
        VectorWriter(tmpFile, 'utf-8', QgsFields(), QGis.WKBPolygon, outCrs)
        isoLayer = getObjectFromUri(tmpFile)
        layerFromRequests(responses, isoLayer)

        if simplify:
            progress.setInfo('Simplifying geometry')
            # merge overlapping polygons of same range
            groupByColumn = 'AA_MINS' if metric == 'time' else 'AA_METERS'
            dissolved = runalg('qgis:dissolve', tmpFile, False, groupByColumn, None, progress=None)
            isoLayer = getObjectFromUri(dissolved['OUTPUT'])

            # make polygons of different ranges distinct
            isochrones = [iso for iso in isoLayer.getFeatures()]
            isochrones = sorted(isochrones, key=lambda f: f[groupByColumn], reverse=True)
            if len(isochrones) > 1:
                for i in range(len(isochrones) - 1):
                    cur = isochrones[i]
                    nxt = isochrones[i+1]
                    cur.setGeometry(cur.geometry().difference(nxt.geometry()))
        else:
            isochrones = [iso for iso in isoLayer.getFeatures()]

        # FIXME: for shapefile outputs no attributes are written!
        # heisenbug³ workaround: use gpkg instead
        output = self.getOutputFromName(self.OUT)
        writer = output.getVectorWriter(isoLayer.fields(), QGis.WKBPolygon, outCrs)
        for f in isochrones:
            writer.addFeature(f)

        if not output.layer:
            output.layer = getObjectFromUri(output.value)

        _stylePoly(output.layer, metric) # reapply style to new layer
