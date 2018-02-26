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

from os.path import dirname, join

from PyQt4.QtGui import QIcon
from processing.core.AlgorithmProvider import AlgorithmProvider

from OSMtools.osmtools_processing.isochrones import IsochronesGeoAlg

class OSMtoolsAlgoProvider(AlgorithmProvider):
    """
    OSMtools provides some GeoAlgorithms to allow scripting via Processing / Graphical Modeler
    """

    def __init__(self):
        AlgorithmProvider.__init__(self)

        self.activate = True # enable by default

        # Load algorithms
        self.alglist = [
            IsochronesGeoAlg(),
        ]

        for alg in self.alglist:
            alg.provider = self

    def initializeSettings(self):
        AlgorithmProvider.initializeSettings(self)

    def unload(self):
        AlgorithmProvider.unload(self)

    # used in scripts / console
    def getName(self):
        return 'OSMtools'

    # displayed in toolbox
    def getDescription(self):
        return 'OSMtools'

    def getIcon(self):
        return QIcon(join(dirname(__file__), '../icon.png'))

    # output layers from memory provider if no path is given
    def supportsNonFileBasedOutput(self):
        return True

    def getSupportedOutputVectorLayerExtensions(self):
        return ['gpkg']

    def _loadAlgorithms(self):
        self.algs = self.alglist
