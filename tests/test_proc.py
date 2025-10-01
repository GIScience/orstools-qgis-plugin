from qgis.core import (
    QgsPointXY,
    QgsProcessingFeedback,
    QgsProcessingContext,
    QgsProcessingUtils,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsRectangle,
)
from qgis.testing import unittest
from qgis.PyQt.QtCore import QMetaType

from ORStools.utils.wrapper import create_qgs_field
from ORStools.proc.directions_lines_proc import ORSDirectionsLinesAlgo
from ORStools.proc.directions_points_layer_proc import ORSDirectionsPointsLayerAlgo
from ORStools.proc.directions_points_layers_proc import ORSDirectionsPointsLayersAlgo
from ORStools.proc.isochrones_layer_proc import ORSIsochronesLayerAlgo
from ORStools.proc.isochrones_point_proc import ORSIsochronesPointAlgo
from ORStools.proc.matrix_proc import ORSMatrixAlgo
from ORStools.proc.snap_layer_proc import ORSSnapLayerAlgo
from ORStools.proc.snap_point_proc import ORSSnapPointAlgo


class TestProc(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        uri = "point?crs=epsg:4326"
        cls.point_layer_1 = QgsVectorLayer(uri, "Scratch point layer", "memory")
        points_of_interest = [QgsPointXY(8.6724, 49.3988), QgsPointXY(8.6908, 49.4094)]
        for point in points_of_interest:
            feature = QgsFeature()
            feature.setGeometry(QgsGeometry.fromPointXY(point))
            cls.point_layer_1.dataProvider().addFeature(feature)

        cls.point_layer_2 = QgsVectorLayer(uri, "Scratch point layer", "memory")
        points_of_interest = [QgsPointXY(8.4660, 49.4875), QgsPointXY(8.4796, 49.4978)]
        for point in points_of_interest:
            feature = QgsFeature()
            feature.setGeometry(QgsGeometry.fromPointXY(point))
            cls.point_layer_2.dataProvider().addFeature(feature)

        uri = "linestring?crs=epsg:4326"
        cls.line_layer = QgsVectorLayer(uri, "Scratch point layer", "memory")
        vertices = [(8.6724, 49.3988), (8.7165, 49.4106), (8.6947, 49.4178)]
        line_geometry = QgsGeometry.fromPolylineXY([QgsPointXY(x, y) for x, y in vertices])
        feature = QgsFeature()
        feature.setGeometry(line_geometry)
        cls.line_layer.dataProvider().addFeature(feature)

        lower_left = QgsPointXY(8.45, 48.85)
        upper_right = QgsPointXY(8.46, 48.86)
        cls.bbox = QgsRectangle(lower_left, upper_right)

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

        feat_length = next(processed_layer.getFeatures()).geometry().length()
        self.assertTrue(feat_length > 0)

    def test_directions_lines_opti(self):
        parameters = {
            "INPUT_AVOID_BORDERS": None,
            "INPUT_AVOID_COUNTRIES": "",
            "INPUT_AVOID_FEATURES": [],
            "INPUT_AVOID_POLYGONS": None,
            "INPUT_LAYER_FIELD": None,
            "INPUT_LINE_LAYER": self.line_layer,
            "INPUT_OPTIMIZE": 0,
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

        feat_length = next(processed_layer.getFeatures()).geometry().length()
        self.assertTrue(feat_length > 0)

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

        feat_length = next(processed_layer.getFeatures()).geometry().length()
        self.assertTrue(feat_length > 0)

        return processed_layer

    def test_directions_points_layer_optimization(self):
        parameters = {
            "INPUT_AVOID_BORDERS": None,
            "INPUT_AVOID_COUNTRIES": "",
            "INPUT_AVOID_FEATURES": [],
            "INPUT_AVOID_POLYGONS": None,
            "INPUT_LAYER_FIELD": None,
            "INPUT_OPTIMIZE": 1,
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

        feat_length = next(processed_layer.getFeatures()).geometry().length()
        self.assertTrue(feat_length > 0)

        return processed_layer

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

        feat_length = next(processed_layer.getFeatures()).geometry().length()
        self.assertTrue(feat_length > 0)

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

        feat_area = next(processed_layer.getFeatures()).geometry().area()
        self.assertTrue(feat_area > 0)

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

        feats = processed_layer.getFeatures()
        feat_areas = [feat.geometry().area() for feat in feats]
        self.assertTrue(feat_areas[0] > 0)
        # TODO: This is the wrong way around, because polygon order in isochrones is inverted.
        self.assertTrue(feat_areas[0] > feat_areas[1])

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

        feat = next(processed_layer.getFeatures())
        self.assertTrue(feat.attributes()[2] > 0)

    # def test_export(self):
    #     parameters = {
    #         "INPUT_PROVIDER": 0,
    #         "INPUT_PROFILE": 0,
    #         "INPUT_EXPORT": self.bbox,
    #         "OUTPUT_POINT": "TEMPORARY_OUTPUT",
    #         "OUTPUT": "TEMPORARY_OUTPUT",
    #     }
    #
    #     export = ORSExportAlgo().create()
    #     dest_id = export.processAlgorithm(parameters, self.context, self.feedback)
    #     processed_layer = QgsProcessingUtils.mapLayerFromString(dest_id["OUTPUT"], self.context)
    #     processed_nodes = QgsProcessingUtils.mapLayerFromString(
    #         dest_id["OUTPUT_POINT"], self.context)
    #     )
    #
    #     self.assertEqual(type(processed_layer), QgsVectorLayer)
    #     self.assertEqual(type(processed_nodes), QgsVectorLayer)
    #
    #     feat_point = next(processed_layer.getFeatures())
    #     self.assertTrue(feat_point.hasGeometry())
    #     feat_line = next(processed_nodes.getFeatures())
    #     self.assertTrue(feat_line.hasGeometry())

    def test_snapping(self):
        parameters = {
            "INPUT_PROFILE": 0,
            "INPUT_PROVIDER": 0,
            "IN_POINT": "-11867882.765490,4161830.530990 [EPSG:3857]",
            "OUTPUT": "TEMPORARY_OUTPUT",
            "RADIUS": 300,
        }

        snap_point = ORSSnapPointAlgo().create()
        dest_id = snap_point.processAlgorithm(parameters, self.context, self.feedback)
        processed_layer = QgsProcessingUtils.mapLayerFromString(dest_id["OUTPUT"], self.context)
        new_feat = next(processed_layer.getFeatures())
        self.assertEqual(
            new_feat.geometry().asWkt(), "Point (-106.61225600000000213 34.98548300000000211)"
        )

        parameters = {
            "INPUT_PROFILE": 0,
            "INPUT_PROVIDER": 0,
            "IN_POINTS": self.point_layer_2,
            "OUTPUT": "TEMPORARY_OUTPUT",
            "RADIUS": 300,
        }

        snap_points = ORSSnapLayerAlgo().create()
        dest_id = snap_points.processAlgorithm(parameters, self.context, self.feedback)
        processed_layer = QgsProcessingUtils.mapLayerFromString(dest_id["OUTPUT"], self.context)
        new_feat = next(processed_layer.getFeatures())

        self.assertEqual(
            new_feat.geometry().asWkt(), "Point (8.46554599999999979 49.48699799999999982)"
        )
        self.assertEqual(len([i for i in processed_layer.getFeatures()]), 2)

        # test with "SNAPPED_NAME" being present in layer fields
        new_field = create_qgs_field("SNAPPED_NAME", QMetaType.Type.QString)
        self.point_layer_2.dataProvider().addAttributes([new_field])
        self.point_layer_2.updateFields()

        self.assertRaises(
            Exception, lambda: snap_points.processAlgorithm(parameters, self.context, self.feedback)
        )
