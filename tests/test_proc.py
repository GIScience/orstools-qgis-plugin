from qgis._core import (
    QgsPointXY,
    QgsProcessingFeedback,
    QgsProcessingContext,
    QgsProcessingUtils,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
)
from qgis.testing import unittest

from ORStools.proc.directions_lines_proc import ORSDirectionsLinesAlgo
from ORStools.proc.directions_points_layer_proc import ORSDirectionsPointsLayerAlgo
from ORStools.proc.directions_points_layers_proc import ORSDirectionsPointsLayersAlgo
from ORStools.proc.isochrones_layer_proc import ORSIsochronesLayerAlgo
from ORStools.proc.isochrones_point_proc import ORSIsochronesPointAlgo
from ORStools.proc.matrix_proc import ORSMatrixAlgo


class TestProc(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        uri = "point?crs=epsg:4326"
        cls.point_layer_1 = QgsVectorLayer(uri, "Scratch point layer", "memory")
        points_of_interest = [QgsPointXY(-118.2394, 34.0739), QgsPointXY(-118.3215, 34.1399)]
        for point in points_of_interest:
            feature = QgsFeature()
            feature.setGeometry(QgsGeometry.fromPointXY(point))
            cls.point_layer_1.dataProvider().addFeatures([feature])

        cls.point_layer_2 = QgsVectorLayer(uri, "Scratch point layer", "memory")
        points_of_interest = [QgsPointXY(-118.5, 34.2), QgsPointXY(-118.5, 34.3)]
        for point in points_of_interest:
            feature = QgsFeature()
            feature.setGeometry(QgsGeometry.fromPointXY(point))
            cls.point_layer_2.dataProvider().addFeatures([feature])

        cls.line_layer = QgsVectorLayer(uri, "Scratch point layer", "memory")
        vertices = [(-118.2394, 34.0739), (-118.3215, 34.1341), (-118.4961, 34.5)]
        line_geometry = QgsGeometry.fromPolylineXY([QgsPointXY(x, y) for x, y in vertices])
        feature = QgsFeature()
        feature.setGeometry(line_geometry)
        cls.line_layer.dataProvider().addFeatures([feature])

        cls.feedback = QgsProcessingFeedback()
        cls.context = QgsProcessingContext()

    def test_directions_lines(self):
        parameters = {
            "INPUT_AVOID_BORDERS": None,
            "INPUT_AVOID_COUNTRIES": "",
            "INPUT_AVOID_FEATURES": [],
            "INPUT_AVOID_POLYGONS": None,
            "INPUT_LAYER_FIELD": None,
            "INPUT_LINE_LAYER": self.line_layer,
            "INPUT_OPTIMIZE": None,
            "INPUT_PREFERENCE": 0,
            "INPUT_PROFILE": 0,
            "INPUT_PROVIDER": 0,
            "INPUT_METRIC": 0,
            "LOCATION_TYPE": 0,
            "OUTPUT": "TEMPORARY_OUTPUT",
        }

        directions = ORSDirectionsLinesAlgo().create()
        dest_id = directions.processAlgorithm(parameters, self.context, self.feedback)
        processed_layer = QgsProcessingUtils.mapLayerFromString(dest_id["OUTPUT"], self.context)

        self.assertEqual(type(processed_layer), QgsVectorLayer)

    def test_directions_points_layer(self):
        parameters = {
            "INPUT_AVOID_BORDERS": None,
            "INPUT_AVOID_COUNTRIES": "",
            "INPUT_AVOID_FEATURES": [],
            "INPUT_AVOID_POLYGONS": None,
            "INPUT_LAYER_FIELD": None,
            "INPUT_OPTIMIZE": None,
            "INPUT_POINT_LAYER": self.point_layer_1,
            "INPUT_PREFERENCE": 0,
            "INPUT_PROFILE": 0,
            "INPUT_PROVIDER": 0,
            "INPUT_SORTBY": None,
            "OUTPUT": "TEMPORARY_OUTPUT",
        }

        directions = ORSDirectionsPointsLayerAlgo().create()
        dest_id = directions.processAlgorithm(parameters, self.context, self.feedback)
        processed_layer = QgsProcessingUtils.mapLayerFromString(dest_id["OUTPUT"], self.context)

        self.assertEqual(type(processed_layer), QgsVectorLayer)

    def test_directions_points_layers(self):
        parameters = {
            "INPUT_AVOID_BORDERS": None,
            "INPUT_AVOID_COUNTRIES": "",
            "INPUT_AVOID_FEATURES": [],
            "INPUT_AVOID_POLYGONS": None,
            "INPUT_END_FIELD": None,
            "INPUT_END_LAYER": self.point_layer_1,
            "INPUT_MODE": 0,
            "INPUT_PREFERENCE": 0,
            "INPUT_PROFILE": 0,
            "INPUT_PROVIDER": 0,
            "INPUT_SORT_END_BY": None,
            "INPUT_SORT_START_BY": None,
            "INPUT_START_FIELD": None,
            "INPUT_START_LAYER": self.point_layer_2,
            "OUTPUT": "TEMPORARY_OUTPUT",
        }

        directions = ORSDirectionsPointsLayersAlgo().create()
        dest_id = directions.processAlgorithm(parameters, self.context, self.feedback)
        processed_layer = QgsProcessingUtils.mapLayerFromString(dest_id["OUTPUT"], self.context)

        self.assertEqual(type(processed_layer), QgsVectorLayer)

    def test_isochrones_layer(self):
        parameters = {
            "INPUT_AVOID_BORDERS": None,
            "INPUT_AVOID_COUNTRIES": "",
            "INPUT_AVOID_FEATURES": [],
            "INPUT_AVOID_POLYGONS": None,
            "INPUT_FIELD": None,
            "INPUT_METRIC": 0,
            "INPUT_POINT_LAYER": self.point_layer_1,
            "INPUT_PROFILE": 0,
            "INPUT_PROVIDER": 0,
            "INPUT_RANGES": "5, 10",
            "INPUT_SMOOTHING": None,
            "LOCATION_TYPE": 0,
            "OUTPUT": "TEMPORARY_OUTPUT",
        }

        iso = ORSIsochronesLayerAlgo().create()
        dest_id = iso.processAlgorithm(parameters, self.context, self.feedback)
        processed_layer = QgsProcessingUtils.mapLayerFromString(dest_id["OUTPUT"], self.context)

        self.assertEqual(type(processed_layer), QgsVectorLayer)

    def test_isochrones_point(self):
        parameters = {
            "INPUT_AVOID_BORDERS": None,
            "INPUT_AVOID_COUNTRIES": "",
            "INPUT_AVOID_FEATURES": [],
            "INPUT_AVOID_POLYGONS": None,
            "INPUT_METRIC": 0,
            "INPUT_POINT": "-12476269.994314,3961968.635469 [EPSG:3857]",
            "INPUT_PROFILE": 0,
            "INPUT_PROVIDER": 0,
            "INPUT_RANGES": "5, 10",
            "INPUT_SMOOTHING": None,
            "LOCATION_TYPE": 0,
            "OUTPUT": "TEMPORARY_OUTPUT",
        }

        iso = ORSIsochronesPointAlgo().create()
        dest_id = iso.processAlgorithm(parameters, self.context, self.feedback)
        processed_layer = QgsProcessingUtils.mapLayerFromString(dest_id["OUTPUT"], self.context)

        self.assertEqual(type(processed_layer), QgsVectorLayer)

    def test_matrix(self):
        parameters = {
            "INPUT_END_FIELD": None,
            "INPUT_END_LAYER": self.point_layer_1,
            "INPUT_PROFILE": 0,
            "INPUT_PROVIDER": 0,
            "INPUT_START_FIELD": None,
            "INPUT_START_LAYER": self.point_layer_2,
            "OUTPUT": "TEMPORARY_OUTPUT",
        }

        matrix = ORSMatrixAlgo().create()
        dest_id = matrix.processAlgorithm(parameters, self.context, self.feedback)
        processed_layer = QgsProcessingUtils.mapLayerFromString(dest_id["OUTPUT"], self.context)

        self.assertEqual(type(processed_layer), QgsVectorLayer)
