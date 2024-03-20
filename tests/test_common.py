from qgis._core import QgsPointXY
from qgis.testing import unittest

from ORStools.common import client, directions_core, isochrones_core
import os


class TestCommon(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.api_key = os.environ.get("ORS_API_KEY")
        if cls.api_key is None:
            raise ValueError("ORS_API_KEY environment variable is not set")

    def test_client_request_geometry(self):
        test_response = {
            "type": "FeatureCollection",
            "metadata": {
                "id": "1",
                "attribution": "openrouteservice.org | OpenStreetMap contributors",
                "service": "routing",
                "timestamp": 1708505372024,
                "query": {
                    "coordinates": [[8.684101, 50.131613], [8.68534, 50.131651]],
                    "profile": "driving-car",
                    "id": "1",
                    "preference": "fastest",
                    "format": "geojson",
                    "geometry": True,
                    "elevation": True,
                },
                "engine": {
                    "version": "7.1.1",
                    "build_date": "2024-01-29T14:41:12Z",
                    "graph_date": "2024-02-18T14:05:28Z",
                },
                "system_message": "Preference 'fastest' has been deprecated, using 'recommended'.",
            },
            "bbox": [8.684088, 50.131187, 131.0, 8.686212, 50.131663, 133.8],
            "features": [
                {
                    "bbox": [8.684088, 50.131187, 131.0, 8.686212, 50.131663, 133.8],
                    "type": "Feature",
                    "properties": {
                        "ascent": 2.8,
                        "descent": 0.0,
                        "transfers": 0,
                        "fare": 0,
                        "way_points": [0, 13],
                        "summary": {"distance": 247.2, "duration": 45.1},
                    },
                    "geometry": {
                        "coordinates": [
                            [8.684088, 50.131587, 131.0],
                            [8.684173, 50.13157, 131.0],
                            [8.684413, 50.131523, 131.0],
                            [8.684872, 50.131432, 131.0],
                            [8.685652, 50.131272, 132.1],
                            [8.685937, 50.131187, 132.7],
                            [8.686097, 50.131227, 132.9],
                            [8.686204, 50.131325, 133.1],
                            [8.686212, 50.13143, 133.3],
                            [8.686184, 50.13148, 133.4],
                            [8.68599, 50.131544, 133.6],
                            [8.685774, 50.131612, 133.7],
                            [8.685559, 50.131663, 133.7],
                            [8.68534, 50.13166, 133.8],
                        ],
                        "type": "LineString",
                    },
                }
            ],
        }

        provider = {
            "ENV_VARS": {
                "ORS_QUOTA": "X-Ratelimit-Limit",
                "ORS_REMAINING": "X-Ratelimit-Remaining",
            },
            "base_url": "https://api.openrouteservice.org",
            "key": self.api_key,
            "name": "openrouteservice",
            "timeout": 60,
        }

        params = {
            "preference": "fastest",
            "geometry": "true",
            "instructions": "false",
            "elevation": True,
            "id": 1,
            "coordinates": [[8.684101, 50.131613], [8.68534, 50.131651]],
        }
        agent = "QGIS_ORStools_testing"
        profile = "driving-car"
        clnt = client.Client(provider, agent)
        response = clnt.request("/v2/directions/" + profile + "/geojson", {}, post_json=params)
        self.assertAlmostEqual(
            response["features"][0]["geometry"], test_response["features"][0]["geometry"]
        )

    def test_output_feature_directions(self):
        response = {
            "type": "FeatureCollection",
            "metadata": {
                "id": "1",
                "attribution": "openrouteservice.org | OpenStreetMap contributors",
                "service": "routing",
                "timestamp": 1708522371289,
                "query": {
                    "coordinates": [
                        [-68.199488, -16.518187],
                        [-68.199201, -16.517873],
                        [-68.198438, -16.518486],
                        [-68.198067, -16.518183],
                    ],
                    "profile": "driving-car",
                    "id": "1",
                    "preference": "fastest",
                    "format": "geojson",
                    "geometry": True,
                    "elevation": True,
                },
                "engine": {
                    "version": "7.1.1",
                    "build_date": "2024-01-29T14:41:12Z",
                    "graph_date": "2024-02-18T14:05:28Z",
                },
                "system_message": "Preference 'fastest' has been deprecated, using 'recommended'.",
            },
            "bbox": [-68.199495, -16.518504, 4025.0, -68.198061, -16.51782, 4025.07],
            "features": [
                {
                    "bbox": [-68.199495, -16.518504, 4025.0, -68.198061, -16.51782, 4025.07],
                    "type": "Feature",
                    "properties": {
                        "ascent": 0.1,
                        "descent": 0.0,
                        "transfers": 0,
                        "fare": 0,
                        "way_points": [0, 2, 6, 9],
                        "summary": {"distance": 222.4, "duration": 53.0},
                    },
                    "geometry": {
                        "coordinates": [
                            [-68.199495, -16.518181, 4025.0],
                            [-68.199485, -16.51817, 4025.0],
                            [-68.199206, -16.517869, 4025.0],
                            [-68.199161, -16.51782, 4025.0],
                            [-68.198799, -16.518142, 4025.0],
                            [-68.198393, -16.518478, 4025.0],
                            [-68.198417, -16.518504, 4025.0],
                            [-68.198393, -16.518478, 4025.0],
                            [-68.198078, -16.518162, 4025.0],
                            [-68.198061, -16.518177, 4025.1],
                        ],
                        "type": "LineString",
                    },
                }
            ],
        }
        profile = "driving-car"
        preference = "fastest"
        feature = directions_core.get_output_feature_directions(response, profile, preference)
        coordinates = [(vertex.x(), vertex.y()) for vertex in feature.geometry().vertices()]
        test_coords = [
            (-68.199495, -16.518181),
            (-68.199485, -16.51817),
            (-68.199206, -16.517869),
            (-68.199161, -16.51782),
            (-68.198799, -16.518142),
            (-68.198393, -16.518478),
            (-68.198417, -16.518504),
            (-68.198393, -16.518478),
            (-68.198078, -16.518162),
            (-68.198061, -16.518177),
        ]

        self.assertAlmostEqual(coordinates, test_coords)

    def test_output_features_optimization(self):
        response = {
            "code": 0,
            "summary": {
                "cost": 36,
                "routes": 1,
                "unassigned": 0,
                "setup": 0,
                "service": 0,
                "duration": 36,
                "waiting_time": 0,
                "priority": 0,
                "distance": 152,
                "violations": [],
                "computing_times": {"loading": 23, "solving": 0, "routing": 12},
            },
            "unassigned": [],
            "routes": [
                {
                    "vehicle": 0,
                    "cost": 36,
                    "setup": 0,
                    "service": 0,
                    "duration": 36,
                    "waiting_time": 0,
                    "priority": 0,
                    "distance": 152,
                    "steps": [
                        {
                            "type": "start",
                            "location": [-68.193407, -16.472978],
                            "setup": 0,
                            "service": 0,
                            "waiting_time": 0,
                            "arrival": 0,
                            "duration": 0,
                            "violations": [],
                            "distance": 0,
                        },
                        {
                            "type": "job",
                            "location": [-68.192889, -16.472475],
                            "id": 0,
                            "setup": 0,
                            "service": 0,
                            "waiting_time": 0,
                            "job": 0,
                            "arrival": 18,
                            "duration": 18,
                            "violations": [],
                            "distance": 76,
                        },
                        {
                            "type": "end",
                            "location": [-68.193407, -16.472978],
                            "setup": 0,
                            "service": 0,
                            "waiting_time": 0,
                            "arrival": 36,
                            "duration": 36,
                            "violations": [],
                            "distance": 152,
                        },
                    ],
                    "violations": [],
                    "geometry": "lkpcBd_f_LuBiAtBhA",
                }
            ],
        }
        profile = "driving-car"
        preference = "fastest"
        feature = directions_core.get_output_features_optimization(response, profile, preference)
        coordinates = [(vertex.x(), vertex.y()) for vertex in feature.geometry().vertices()]

        test_coords = [(-68.19331, -16.47303), (-68.19294, -16.47244), (-68.19331, -16.47303)]
        self.assertAlmostEqual(coordinates, test_coords)

    def test_build_default_parameters(self):
        preference, point_list, coordinates, options = (
            "fastest",
            [
                QgsPointXY(-68.1934067732971414, -16.47297756153070125),
                QgsPointXY(-68.19288936751472363, -16.47247452813111934),
            ],
            None,
            {},
        )
        params = directions_core.build_default_parameters(
            preference, point_list, coordinates, options
        )
        test_params = {
            "coordinates": [[-68.193407, -16.472978], [-68.192889, -16.472475]],
            "preference": "fastest",
            "geometry": "true",
            "instructions": "false",
            "elevation": True,
            "id": None,
            "options": {},
        }

        self.assertAlmostEqual(params, test_params)

    def test_isochrones(self):
        response = {
            "type": "FeatureCollection",
            "metadata": {
                "attribution": "openrouteservice.org | OpenStreetMap contributors",
                "service": "isochrones",
                "timestamp": 1710421093483,
                "query": {
                    "profile": "driving-car",
                    "locations": [[-112.594673, 43.554193]],
                    "location_type": "start",
                    "range": [60.0],
                    "range_type": "time",
                    "options": {},
                    "attributes": ["total_pop"],
                },
                "engine": {
                    "version": "7.1.1",
                    "build_date": "2024-01-29T14:41:12Z",
                    "graph_date": "2024-03-10T15:19:08Z",
                },
            },
            "bbox": [-112.637014, 43.548994, -112.550441, 43.554343],
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "group_index": 0,
                        "value": 60.0,
                        "center": [-112.5946738217447, 43.55409137088865],
                        "total_pop": 0.0,
                    },
                    "geometry": {
                        "coordinates": [
                            [
                                [-112.637014, 43.549342],
                                [-112.63692, 43.548994],
                                [-112.631205, 43.550527],
                                [-112.625496, 43.552059],
                                [-112.623482, 43.552518],
                                [-112.617781, 43.553548],
                                [-112.615319, 43.553798],
                                [-112.612783, 43.553937],
                                [-112.61154, 43.553971],
                                [-112.609679, 43.553977],
                                [-112.607819, 43.553983],
                                [-112.603711, 43.553958],
                                [-112.599603, 43.553932],
                                [-112.598575, 43.553928],
                                [-112.594187, 43.553909],
                                [-112.593002, 43.553904],
                                [-112.588772, 43.553886],
                                [-112.587429, 43.553881],
                                [-112.578142, 43.553673],
                                [-112.568852, 43.553464],
                                [-112.559651, 43.553232],
                                [-112.55045, 43.553],
                                [-112.550441, 43.55336],
                                [-112.559642, 43.553592],
                                [-112.568844, 43.553824],
                                [-112.578134, 43.554032],
                                [-112.587427, 43.554241],
                                [-112.58877, 43.554246],
                                [-112.593, 43.554264],
                                [-112.594186, 43.554269],
                                [-112.598573, 43.554288],
                                [-112.599601, 43.554292],
                                [-112.603709, 43.554318],
                                [-112.607817, 43.554343],
                                [-112.60968, 43.554337],
                                [-112.611541, 43.554331],
                                [-112.612793, 43.554297],
                                [-112.614041, 43.554262],
                                [-112.615348, 43.554157],
                                [-112.616646, 43.554052],
                                [-112.617826, 43.553905],
                                [-112.618998, 43.553758],
                                [-112.620272, 43.553544],
                                [-112.621537, 43.553331],
                                [-112.623562, 43.552869],
                                [-112.625576, 43.55241],
                                [-112.631298, 43.550875],
                                [-112.637014, 43.549342],
                            ]
                        ],
                        "type": "Polygon",
                    },
                }
            ],
        }
        id_field_value = None
        isochrones = isochrones_core.Isochrones()
        isochrones.set_parameters("driving-car", "time", 60)

        feats = isochrones.get_features(response, id_field_value)
        self.assertAlmostEqual(next(feats).geometry().area(), 3.176372365487623e-05)
