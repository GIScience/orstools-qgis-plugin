from qgis.testing import unittest

from qgis.core import QgsCoordinateReferenceSystem, QgsPointXY

from ORStools.utils.transform import transformToWGS
from ORStools.utils.convert import decode_polyline
from ORStools.utils.processing import get_params_optimize


class TestUtils(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.WGS = QgsCoordinateReferenceSystem.fromEpsgId(4326)
        cls.PSEUDO = QgsCoordinateReferenceSystem.fromEpsgId(3857)

    def test_to_wgs_pseudo(self):
        point = QgsPointXY(1493761.05913532, 6890799.81730105)
        transformer = transformToWGS(self.PSEUDO)
        self.assertEqual(
            transformer.transform(point), QgsPointXY(13.41868390243822162, 52.49867709045137332)
        )

    def test_polyline_convert(self):
        polyline = "psvcBxg}~KAGUoBMo@Ln@TnB@F"
        decoded = decode_polyline(polyline)
        self.assertEqual(
            decoded,
            [
                [-68.14861, -16.50505],
                [-68.14857, -16.50504],
                [-68.14801, -16.50493],
                [-68.14777, -16.50486],
                [-68.14801, -16.50493],
                [-68.14857, -16.50504],
                [-68.14861, -16.50505],
            ],
        )

    def test_get_params_optimize(self):
        points = [
            QgsPointXY(-68.14860459410432725, -16.5050554680791457),
            QgsPointXY(-68.14776841920792094, -16.50487191749212812),
        ]
        profile = "driving-car"
        mode = 0

        params = {
            "jobs": [{"location": [-68.147768, -16.504872], "id": 0}],
            "vehicles": [
                {
                    "id": 0,
                    "profile": "driving-car",
                    "start": [-68.148605, -16.505055],
                    "end": [-68.148605, -16.505055],
                }
            ],
            "options": {"g": True},
        }
        self.assertEqual(get_params_optimize(points, profile, mode), params)
