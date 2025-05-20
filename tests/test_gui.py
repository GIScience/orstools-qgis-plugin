
from qgis.PyQt.QtWidgets import QLineEdit
from qgis.core import (
    QgsSettings,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsProject,
    QgsPointXY,
)
from qgis.gui import QgsCollapsibleGroupBox
from qgis.testing import unittest

from qgis.PyQt.QtTest import QTest
from qgis.PyQt.QtCore import Qt, QEvent, QPoint
from qgis.PyQt.QtWidgets import QPushButton
from qgis.gui import QgsMapCanvas, QgsMapMouseEvent, QgsRubberBand
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsRectangle,
)
import pytest

from .test_proc import TestProc
from tests.utils.utilities import get_qgis_app

CANVAS: QgsMapCanvas
QGISAPP, CANVAS, IFACE, PARENT = get_qgis_app()


@pytest.mark.filterwarnings("ignore:.*imp module is deprecated.*")
class TestGui(unittest.TestCase):
    def tearDown(self):
        """Run after each test"""
        # Clean up layers
        QgsProject.instance().removeAllMapLayers()

    def test_without_live_preview(self):
        from ORStools.gui.ORStoolsDialog import ORStoolsDialog
        from ORStools.gui.ORStoolsDialogConfig import ORStoolsDialogConfigMain
        from ORStools.utils import maptools

        CRS = QgsCoordinateReferenceSystem.fromEpsgId(3857)
        CANVAS.setExtent(QgsRectangle(258889, 7430342, 509995, 7661955))
        CANVAS.setDestinationCrs(CRS)
        CANVAS.setFrameStyle(0)
        CANVAS.resize(600, 400)
        self.assertEqual(CANVAS.width(), 600)
        self.assertEqual(CANVAS.height(), 400)

        # Set and reset config to test whether the reset works
        dlg_config = ORStoolsDialogConfigMain()
        provider = dlg_config.providers.findChildren(QgsCollapsibleGroupBox)[0]

        line_edit = provider.findChild(QLineEdit, "openrouteservice_directions_endpoint")
        line_edit.setText("thisisnotanendpoint")

        dlg = ORStoolsDialog(IFACE)
        dlg.open()
        self.assertTrue(dlg.isVisible())

        map_button: QPushButton = dlg.routing_fromline_map

        # click green add vertices button
        QTest.mouseClick(map_button, Qt.MouseButton.LeftButton)
        self.assertFalse(dlg.isVisible())
        self.assertIsInstance(CANVAS.mapTool(), maptools.LineTool)

        # click on canvas at [0, 0]
        dlg.line_tool.canvasReleaseEvent(self.map_release(0, 0, Qt.MouseButton.LeftButton))

        dlg.line_tool.canvasReleaseEvent(self.map_release(5, 5, Qt.MouseButton.LeftButton))

        self.assertEqual(dlg.routing_fromline_list.count(), 2)

        len_rubber_band = len(dlg.rubber_band.asGeometry().asPolyline())
        print(dlg.rubber_band.asGeometry().asPolyline())
        self.assertEqual(len_rubber_band, 2)

        # doubleclick on canvas at [5, 5]
        dlg.line_tool.canvasDoubleClickEvent(self.map_dclick(5, 5, Qt.MouseButton.LeftButton))
        self.assertTrue(dlg.isVisible())

        # Check first item of list widget
        self.assertEqual(dlg.routing_fromline_list.item(0).text(), "Point 0: -0.187575, 56.516620")

        # Check rubber band has only 2 vertices
        self.assertEqual(dlg.routing_fromline_list.count(), 2)
        self.assertEqual(type(dlg.rubber_band), QgsRubberBand)
        len_rubber_band = len(dlg.rubber_band.asGeometry().asPolyline())
        self.assertEqual(len_rubber_band, 2)

    def test_with_live_preview(self):
        """
        Tests basic adding and removing of points to the QListWidget and associated rubber bands.
        """
        from ORStools.gui.ORStoolsDialog import ORStoolsDialog
        from ORStools.utils import maptools

        CRS = QgsCoordinateReferenceSystem.fromEpsgId(3857)
        CANVAS.setExtent(QgsRectangle(-13732628.1, 6181790.0, -13728426.7, 6179205.3))
        CANVAS.setDestinationCrs(CRS)
        CANVAS.setFrameStyle(0)
        CANVAS.resize(600, 400)
        self.assertEqual(CANVAS.width(), 600)
        self.assertEqual(CANVAS.height(), 400)

        dlg = ORStoolsDialog(IFACE)
        dlg.open()
        self.assertTrue(dlg.isVisible())

        # Toggle live preview
        dlg.toggle_preview.toggle()
        self.assertTrue(dlg.toggle_preview.isChecked())

        # click 'routing_fromline_map'
        QTest.mouseClick(dlg.routing_fromline_map, Qt.MouseButton.LeftButton)
        self.assertFalse(dlg.isVisible())
        self.assertIsInstance(CANVAS.mapTool(), maptools.LineTool)

        # click on canvas at [0, 0]
        dlg.line_tool.canvasReleaseEvent(self.map_release(0, 0, Qt.MouseButton.LeftButton))
        # click on canvas at [5, 5]
        dlg.line_tool.canvasReleaseEvent(self.map_release(5, 5, Qt.MouseButton.LeftButton))
        dlg.line_tool.canvasReleaseEvent(self.map_release(5, 0, Qt.MouseButton.LeftButton))
        dlg.line_tool.canvasReleaseEvent(self.map_release(0, 5, Qt.MouseButton.LeftButton))
        dlg.line_tool.canvasReleaseEvent(self.map_release(10, 0, Qt.MouseButton.LeftButton))

        self.assertEqual(
            dlg.routing_fromline_list.item(0).text(), "Point 0: -123.384059, 48.448463"
        )

        # Check that the live preview rubber band has more than two vertices
        self.assertEqual(type(dlg.rubber_band), QgsRubberBand)
        len_rubber_band = len(dlg.rubber_band.asGeometry().asPolyline())
        self.assertTrue(len_rubber_band > 2)

        # Right click and thus show dlg
        dlg.line_tool.canvasReleaseEvent(self.map_release(0, 5, Qt.MouseButton.RightButton))
        self.assertTrue(dlg.isVisible())
        # Test that right click doesn't create a point
        self.assertEqual(dlg.routing_fromline_list.count(), 5)

        # click on canvas at [10, 10]
        # Check that the click with an open dlg doesn't create an entry
        dlg.line_tool.canvasReleaseEvent(self.map_release(10, 10, Qt.MouseButton.LeftButton))
        self.assertEqual(dlg.routing_fromline_list.count(), 5)

        # test whether point order remains valid when selected points are deleted from QListWidget
        dlg.routing_fromline_list.setCurrentRow(1)
        dlg.routing_fromline_clear.clicked.emit()

        # click again after deletion
        QTest.mouseClick(dlg.routing_fromline_map, Qt.MouseButton.LeftButton)
        self.assertFalse(dlg.isVisible())
        dlg.line_tool.canvasReleaseEvent(self.map_release(10, 10, Qt.MouseButton.LeftButton))

        # Right click and thus show dlg
        dlg.line_tool.canvasReleaseEvent(self.map_release(0, 5, Qt.MouseButton.RightButton))
        self.assertTrue(dlg.isVisible())

        self.assertEqual(dlg.routing_fromline_list.count(), 5)
        numbers = [int(i.document().toPlainText()) for i in dlg.annotations]
        self.assertTrue(numbers == list(range(numbers[0], numbers[0] + len(numbers))))

        # Disable live preview
        dlg.toggle_preview.toggle()
        self.assertFalse(dlg.toggle_preview.isChecked())

        # Check rubber band has only 5 vertices
        self.assertEqual(dlg.routing_fromline_list.count(), 5)
        self.assertEqual(type(dlg.rubber_band), QgsRubberBand)
        len_rubber_band = len(dlg.rubber_band.asGeometry().asPolyline())
        self.assertEqual(len_rubber_band, 5)

        # Click Add Vertices again
        QTest.mouseClick(dlg.routing_fromline_map, Qt.MouseButton.LeftButton)
        self.assertFalse(dlg.isVisible())

        # continue digitization
        # click on canvas at [10, 5]
        dlg.line_tool.canvasReleaseEvent(self.map_release(10, 5, Qt.MouseButton.LeftButton))
        self.assertEqual(dlg.routing_fromline_list.count(), 6)

        # Double click and thus show dlg
        dlg.line_tool.canvasDoubleClickEvent(self.map_dclick(0, 5, Qt.MouseButton.LeftButton))
        self.assertTrue(dlg.isVisible())

        # clear list widget and check that it's empty
        QTest.mouseClick(dlg.routing_fromline_clear, Qt.MouseButton.LeftButton)
        self.assertEqual(dlg.routing_fromline_list.count(), 0)
        # Check that the rubber band is empty
        self.assertEqual(type(dlg.rubber_band), QgsRubberBand)
        self.assertTrue(dlg.rubber_band.asGeometry().isNull())

    def test_drag_drop_with_live_preview(self):
        from ORStools.gui.ORStoolsDialog import ORStoolsDialog
        from ORStools.utils import maptools

        CRS = QgsCoordinateReferenceSystem.fromEpsgId(3857)
        CANVAS.setExtent(QgsRectangle(-13732628.1, 6181790.0, -13728426.7, 6179205.3))
        CANVAS.setDestinationCrs(CRS)
        CANVAS.setFrameStyle(0)
        CANVAS.resize(600, 400)
        self.assertEqual(CANVAS.width(), 600)
        self.assertEqual(CANVAS.height(), 400)

        dlg = ORStoolsDialog(IFACE)
        dlg.open()
        self.assertTrue(dlg.isVisible())

        # click 'routing_fromline_map'
        QTest.mouseClick(dlg.routing_fromline_map, Qt.MouseButton.LeftButton)
        self.assertFalse(dlg.isVisible())
        self.assertIsInstance(CANVAS.mapTool(), maptools.LineTool)

        # Add some points to the list
        dlg.line_tool.canvasReleaseEvent(self.map_release(100, 5, Qt.MouseButton.LeftButton))
        dlg.line_tool.canvasReleaseEvent(self.map_release(10, 50, Qt.MouseButton.LeftButton))
        dlg.line_tool.canvasReleaseEvent(self.map_release(100, 50, Qt.MouseButton.LeftButton))

        # Add point to be dragged
        dlg.line_tool.canvasReleaseEvent(self.map_release(10, 5, Qt.MouseButton.LeftButton))
        self.assertEqual(dlg.routing_fromline_list.count(), 4)
        self.assertEqual(
            dlg.routing_fromline_list.item(3).text(), "Point 3: -123.375767, 48.445713"
        )

        # Press at previous position
        dlg.line_tool.canvasPressEvent(self.map_press(11, 5, Qt.MouseButton.LeftButton))

        # Release somewhere else
        dlg.line_tool.canvasReleaseEvent(self.map_release(50, 10, Qt.MouseButton.LeftButton))
        self.assertEqual(dlg.routing_fromline_list.count(), 4)
        # Check that the coordinates of the point at the same position in the list has changed
        self.assertEqual(
            dlg.routing_fromline_list.item(3).text(), "Point 3: -123.342597, 48.442962"
        )

        # Check that the rubber band is not empty
        self.assertEqual(type(dlg.rubber_band), QgsRubberBand)
        self.assertFalse(dlg.rubber_band.asGeometry().isNull())

    def map_release(self, x, y, side):
        return QgsMapMouseEvent(
            CANVAS,
            QEvent.Type.MouseButtonRelease,
            QPoint(x, y),  # Relative to the canvas' dimensions
            side,
            side,
            Qt.KeyboardModifier.NoModifier,
        )

    def map_press(self, x, y, side):
        return QgsMapMouseEvent(
            CANVAS,
            QEvent.Type.MouseButtonPress,
            QPoint(x, y),  # Relative to the canvas' dimensions
            side,
            side,
            Qt.KeyboardModifier.NoModifier,
        )

    def map_dclick(self, x, y, side):
        return QgsMapMouseEvent(
            CANVAS,
            QEvent.Type.MouseButtonDblClick,
            QPoint(x, y),  # Relative to the canvas' dimensions
            side,
            side,
            Qt.KeyboardModifier.NoModifier,
        )

    def test_ORStoolsDialogConfig_endpoints(self):
        from ORStools.gui.ORStoolsDialogConfig import ORStoolsDialogConfigMain

        CRS = QgsCoordinateReferenceSystem.fromEpsgId(3857)
        CANVAS.setExtent(QgsRectangle(258889, 7430342, 509995, 7661955))
        CANVAS.setDestinationCrs(CRS)
        CANVAS.setFrameStyle(0)
        CANVAS.resize(600, 400)
        self.assertEqual(CANVAS.width(), 600)
        self.assertEqual(CANVAS.height(), 400)

        # Set and reset config to test whether the reset works
        dlg_config = ORStoolsDialogConfigMain()
        provider = dlg_config.providers.findChildren(QgsCollapsibleGroupBox)[0]

        # set endpoint of directions to non-existent value
        line_edit = provider.findChild(QLineEdit, "openrouteservice_directions_endpoint")
        line_edit.setText("thisisnotanendpoint")
        dlg_config.accept()

        settings_directions_endpoint = QgsSettings().value("ORStools/config")["providers"][0][
            "endpoints"
        ]["directions"]

        self.assertEqual(settings_directions_endpoint, "thisisnotanendpoint")

        proc = TestProc()
        proc.setUpClass()

        self.assertRaises(StopIteration, proc.test_directions_points_layer)

        # reset endpoints
        dlg_config._reset_endpoints()

        dlg_config._reset_endpoints()
        dlg_config.accept()

        settings_directions_endpoint = QgsSettings().value("ORStools/config")["providers"][0][
            "endpoints"
        ]["directions"]

        self.assertEqual(settings_directions_endpoint, "directions")

        layer = proc.get_directions_points_layer()

        self.assertEqual(
            "POINT(8.67251100000000008 49.39887900000000087)",
            next(layer.getFeatures()).geometry().asPolyline()[0].asWkt(),
        )

    def test_ORStoolsDialogConfig_url(self):
        from ORStools.gui.ORStoolsDialogConfig import ORStoolsDialogConfigMain

        CRS = QgsCoordinateReferenceSystem.fromEpsgId(3857)
        CANVAS.setExtent(QgsRectangle(258889, 7430342, 509995, 7661955))
        CANVAS.setDestinationCrs(CRS)
        CANVAS.setFrameStyle(0)
        CANVAS.resize(600, 400)
        self.assertEqual(CANVAS.width(), 600)
        self.assertEqual(CANVAS.height(), 400)

        # Set and reset config to test whether the reset works
        dlg_config = ORStoolsDialogConfigMain()
        provider = dlg_config.providers.findChildren(QgsCollapsibleGroupBox)[0]

        # set endpoint of directions to non-existent value
        line_edit = provider.findChild(QLineEdit, "openrouteservice_base_url_text")
        line_edit.setText("thisisnotaurl")
        dlg_config.accept()

        settings_directions_endpoint = QgsSettings().value("ORStools/config")["providers"][0][
            "base_url"
        ]

        self.assertEqual(settings_directions_endpoint, "thisisnotaurl")

        proc = TestProc()
        proc.setUpClass()

        self.assertRaises(Exception, proc.get_directions_points_layer)

        # reset url
        url_reset_button = dlg_config.findChild(QPushButton, "openrouteservice_reset_url_button")
        url_reset_button.clicked.emit()

        dlg_config._reset_endpoints()
        dlg_config.accept()

        settings_directions_endpoint = QgsSettings().value("ORStools/config")["providers"][0][
            "endpoints"
        ]["directions"]

        self.assertEqual(settings_directions_endpoint, "directions")

        layer = proc.get_directions_points_layer()

        self.assertEqual(
            "POINT(8.67251100000000008 49.39887900000000087)",
            next(layer.getFeatures()).geometry().asPolyline()[0].asWkt(),
        )

    def test_custom_endpoints(self):
        from ORStools.gui.ORStoolsDialogConfig import ORStoolsDialogConfigMain

        # Set and reset config to test whether the reset works
        dlg_config = ORStoolsDialogConfigMain()
        provider = dlg_config.providers.findChildren(QgsCollapsibleGroupBox)[0]

        # set endpoint of directions to non-existent value
        line_edit = provider.findChild(QLineEdit, "openrouteservice_directions_endpoint")
        line_edit.setText("custom_directions_endpoint")
        dlg_config.accept()

        settings_directions_endpoint = QgsSettings().value("ORStools/config")["providers"][0][
            "endpoints"
        ]["directions"]

        proc = TestProc()
        proc.setUpClass()

        self.assertEqual(settings_directions_endpoint, "custom_directions_endpoint")

        layer = proc.get_directions_points_layer()
        self.assertEqual(layer.featureCount(), 0)

        # reset endpoints
        dlg_config._reset_endpoints()
        dlg_config.accept()

        settings_directions_endpoint = QgsSettings().value("ORStools/config")["providers"][0][
            "endpoints"
        ]["directions"]

        self.assertEqual(settings_directions_endpoint, "directions")

        layer = proc.get_directions_points_layer()
        self.assertEqual(layer.featureCount(), 93)

        self.assertEqual(
            "POINT(8.67251100000000008 49.39887900000000087)",
            next(layer.getFeatures()).geometry().asPolyline()[0].asWkt(),
        )

    def test_load_valid_point_layer(self):
        """Test loading vertices from valid point layer."""
        from ORStools.gui.ORStoolsDialog import ORStoolsDialogMain

        dialog_main = ORStoolsDialogMain(IFACE)
        dialog_main._init_gui_control()

        # Create test layers
        self.point_layer = QgsVectorLayer("Point?crs=EPSG:4326", "test_points", "memory")
        self.line_layer = QgsVectorLayer("LineString?crs=EPSG:4326", "test_lines", "memory")

        # Add 3 features to point layer
        for coords in [(1, 2), (3, 4), (5, 6)]:
            feat = QgsFeature()
            feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(*coords)))
            self.point_layer.dataProvider().addFeature(feat)

        QgsProject.instance().addMapLayers([self.point_layer, self.line_layer])

        # Run test
        dialog_main.dlg.load_vertices_from_layer("ok")

        # Verify
        self.assertTrue(dialog_main.dlg.line_tool is not None)
        self.assertEqual(dialog_main.dlg.routing_fromline_list.count(), 3)
        self.assertIsInstance(dialog_main.dlg.rubber_band, QgsRubberBand)

    def test_user_cancels_operation(self):
        """Test when user cancels the dialog."""
        from ORStools.gui.ORStoolsDialog import ORStoolsDialogMain

        dialog_main = ORStoolsDialogMain(IFACE)
        dialog_main._init_gui_control()
        dialog_main.dlg.load_vertices_from_layer("not_ok")

        self.assertTrue(dialog_main.dlg.line_tool is not None)
        self.assertEqual(dialog_main.dlg.routing_fromline_list.count(), 0)
        self.assertNotIsInstance(dialog_main.dlg.rubber_band, QgsRubberBand)
