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

import os.path
import webbrowser

from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QUrl

from qgis.core import (QgsWkbTypes,
                       QgsCoordinateReferenceSystem,
                       QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSink,
                       )
from . import HELP_DIR
from ORStools import ENDPOINTS, ICON_DIR, __help__
from ORStools.core import client, directions_core, PROFILES, PREFERENCES
from ORStools.utils import convert, transform, exceptions


class ORSdirectionsAlgo(QgsProcessingAlgorithm):
    # TODO: create base algorithm class common to all modules

    ALGO_NAME = 'directions'
    MODE_SELECTION = ['Row-by-Row', 'All-by-All']

    IN_START = "INPUT_START_LAYER"
    IN_START_FIELD = "INPUT_START_FIELD"
    IN_END = "INPUT_END_LAYER"
    IN_END_FIELD = "INPUT_END_FIELD"
    IN_PROFILE = "INPUT_PROFILE"
    IN_PREFERENCE = "INPUT_PREFERENCE"
    IN_MODE = "INPUT_MODE"
    OUT = 'OUTPUT'

    def initAlgorithm(self, configuration, p_str=None, Any=None, *args, **kwargs):

        self.addParameter(
            QgsProcessingParameterEnum(
                self.IN_PROFILE,
                "Travel mode",
                PROFILES
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.IN_PREFERENCE,
                "Travel preference",
                PREFERENCES
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.IN_MODE,
                "Layer mode",
                self.MODE_SELECTION
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                name=self.IN_START,
                description="Input Start Point layer",
                types=[QgsProcessing.TypeVectorPoint],
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                name=self.IN_START_FIELD,
                description="Start ID Field (can be used for joining)",
                parentLayerParameterName=self.IN_START,
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                name=self.IN_END,
                description="Input End Point layer",
                types=[QgsProcessing.TypeVectorPoint],
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                name=self.IN_END_FIELD,
                description="End ID Field (can be used for joining)",
                parentLayerParameterName=self.IN_END,
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                name=self.OUT,
                description="Directions",
            )
        )
    def name(self):
        return self.ALGO_NAME

    def shortHelpString(self):
        """Displays the sidebar help in the algorithm window"""

        file = os.path.join(
            HELP_DIR,
            'algorithm_directions.help'
        )
        with open(file) as helpf:
            msg = helpf.read()

        return msg

    def helpUrl(self):
        """will be connected to the Help button in the Algorithm window"""
        return __help__

    def displayName(self):
        return 'Generate ' + self.ALGO_NAME.capitalize()

    def icon(self):
        return QIcon(os.path.join(ICON_DIR, 'icon_directions.png'))

    def createInstance(self):
        return ORSdirectionsAlgo()

    # TODO: preprocess parameters to avoid the range clenaup below:
    # https://www.qgis.org/pyqgis/master/core/Processing/QgsProcessingAlgorithm.html#qgis.core.QgsProcessingAlgorithm.preprocessParameters

    def processAlgorithm(self, parameters, context, feedback):
        # Init ORS client
        clnt = client.Client()

        profile = PROFILES[self.parameterAsEnum(
            parameters,
            self.IN_PROFILE,
            context
        )]

        preference = PREFERENCES[self.parameterAsEnum(
            parameters,
            self.IN_PREFERENCE,
            context
        )]

        mode = self.MODE_SELECTION[self.parameterAsEnum(
            parameters,
            self.IN_MODE,
            context
        )]

        # Get parameter values
        source = self.parameterAsSource(
            parameters,
            self.IN_START,
            context
        )
        source_field_name = self.parameterAsString(
            parameters,
            self.IN_START_FIELD,
            context
        )
        destination = self.parameterAsSource(
            parameters,
            self.IN_END,
            context
        )
        destination_field_name = self.parameterAsString(
            parameters,
            self.IN_END_FIELD,
            context
        )

        # Get fields from field name
        source_field_id = source.fields().lookupField(source_field_name)
        source_field = source.fields().field(source_field_id)
        destination_field_id = source.fields().lookupField(destination_field_name)
        destination_field = source.fields().field(destination_field_id)

        params = {
            'profile': profile,
            'preference': preference,
            'geometry': 'true',
            'format': 'geojson',
            'geometry_format': 'geojson',
            'instructions': 'false',
            'id': None
        }

        route_dict = self._get_route_dict(
            source,
            source_field,
            destination,
            destination_field
        )

        if mode == 'Row-by-Row':
            route_count = min([source.featureCount(), destination.featureCount()])
        else:
            route_count = source.featureCount() * destination.featureCount()

        (sink, dest_id) = self.parameterAsSink(parameters, self.OUT, context,
                                               directions_core.get_fields(source_field.type(), destination_field.type()),
                                               QgsWkbTypes.LineString,
                                               QgsCoordinateReferenceSystem(4326))

        print(route_dict)

        counter = 0
        for coordinates, values in directions_core.get_request_features(route_dict, mode):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break
            feedback.pushInfo(coordinates)

            params['coordinates'] = coordinates

            counter += 1
            feedback.setProgress(int(100.0 / route_count * counter))

            try:
                response = clnt.request(ENDPOINTS[self.ALGO_NAME], params)
            except exceptions.ApiError as e:
                feedback.reportError("Route from {} to {} caused a {}:\n{}".format(
                    values[0],
                    values[1],
                    e.__class__.__name__,
                    str(e))
                )
                continue

            sink.addFeature(directions_core.get_feature(
                response,
                profile,
                preference,
                None,
                values[0],
                values[1]
            ))

        return {self.OUT: dest_id}

    def _get_route_dict(self, source, source_field, destination, destination_field):

        route_dict = dict()

        source_feats = list(source.getFeatures())
        xformer_source = transform.transformToWGS(source.sourceCrs())
        route_dict['start'] = dict(
            geometries=[xformer_source.transform(feat.geometry().asPoint()) for feat in source_feats],
            values= [feat.attribute(source_field.name()) for feat in source_feats],
        )

        destination_feats = list(destination.getFeatures())
        xformer_destination = transform.transformToWGS(destination.sourceCrs())
        route_dict['end'] = dict(
            geometries=[xformer_destination.transform(feat.geometry().asPoint()) for feat in destination_feats],
            values= [feat.attribute(destination_field.name()) for feat in destination_feats],
        )

        return route_dict
