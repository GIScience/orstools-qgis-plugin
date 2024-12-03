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

from tests.utils.utilities import get_qgis_app

CANVAS: QgsMapCanvas
QGISAPP, CANVAS, IFACE, PARENT = get_qgis_app()


@pytest.mark.filterwarnings("ignore:.*imp module is deprecated.*")
class TestGui(unittest.TestCase):
    def test_without_live_preview(self):
        from ORStools.gui.ORStoolsDialog import ORStoolsDialog
        from ORStools.utils import maptools

        CRS = QgsCoordinateReferenceSystem.fromEpsgId(3857)
        CANVAS.setExtent(QgsRectangle(258889, 7430342, 509995, 7661955))
        CANVAS.setDestinationCrs(CRS)
        CANVAS.setFrameStyle(0)
        CANVAS.resize(600, 400)
        self.assertEqual(CANVAS.width(), 600)
        self.assertEqual(CANVAS.height(), 400)

        dlg = ORStoolsDialog(IFACE)
        dlg.open()
        self.assertTrue(dlg.isVisible())

        map_button: QPushButton = dlg.routing_fromline_map

        # click green add vertices button
        QTest.mouseClick(map_button, Qt.LeftButton)
        self.assertFalse(dlg.isVisible())
        self.assertIsInstance(CANVAS.mapTool(), maptools.LineTool)

        # click on canvas at [0, 0]
        dlg.line_tool.canvasReleaseEvent(self.map_release(0, 0, Qt.LeftButton))

        dlg.line_tool.canvasReleaseEvent(self.map_release(5, 5, Qt.LeftButton))

        self.assertEqual(dlg.routing_fromline_list.count(), 2)

        len_rubber_band = len(dlg.rubber_band.asGeometry().asPolyline())
        print(dlg.rubber_band.asGeometry().asPolyline())
        self.assertEqual(len_rubber_band, 2)

        # doubleclick on canvas at [5, 5]
        dlg.line_tool.canvasDoubleClickEvent(self.map_dclick(5, 5, Qt.LeftButton))
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
        QTest.mouseClick(dlg.routing_fromline_map, Qt.LeftButton)
        self.assertFalse(dlg.isVisible())
        self.assertIsInstance(CANVAS.mapTool(), maptools.LineTool)

        # click on canvas at [0, 0]
        dlg.line_tool.canvasReleaseEvent(self.map_release(0, 0, Qt.LeftButton))
        # click on canvas at [5, 5]
        dlg.line_tool.canvasReleaseEvent(self.map_release(5, 5, Qt.LeftButton))

        self.assertEqual(
            dlg.routing_fromline_list.item(0).text(), "Point 0: -123.384059, 48.448463"
        )

        # Check that the live preview rubber band has more than two vertices
        self.assertEqual(type(dlg.rubber_band), QgsRubberBand)
        len_rubber_band = len(dlg.rubber_band.asGeometry().asPolyline())
        self.assertTrue(len_rubber_band > 2)

        # Right click and thus show dlg
        dlg.line_tool.canvasReleaseEvent(self.map_release(0, 5, Qt.RightButton))
        self.assertTrue(dlg.isVisible())
        # Test that right click doesn't create a point
        self.assertEqual(dlg.routing_fromline_list.count(), 2)

        # click on canvas at [10, 10]
        # Check that the click with an open dlg doesn't create an entry
        dlg.line_tool.canvasReleaseEvent(self.map_release(10, 10, Qt.LeftButton))
        self.assertEqual(dlg.routing_fromline_list.count(), 2)

        # Disable live preview
        dlg.toggle_preview.toggle()
        self.assertFalse(dlg.toggle_preview.isChecked())

        # Check rubber band has only 2 vertices
        self.assertEqual(dlg.routing_fromline_list.count(), 2)
        self.assertEqual(type(dlg.rubber_band), QgsRubberBand)
        len_rubber_band = len(dlg.rubber_band.asGeometry().asPolyline())
        self.assertEqual(len_rubber_band, 2)

        # Click Add Vertices again
        QTest.mouseClick(dlg.routing_fromline_map, Qt.LeftButton)
        self.assertFalse(dlg.isVisible())

        # continue digitization
        # click on canvas at [10, 5]
        dlg.line_tool.canvasReleaseEvent(self.map_release(10, 5, Qt.LeftButton))
        self.assertEqual(dlg.routing_fromline_list.count(), 3)

        # Double click and thus show dlg
        dlg.line_tool.canvasDoubleClickEvent(self.map_dclick(0, 5, Qt.LeftButton))
        self.assertTrue(dlg.isVisible())

        # clear list widget and check that it's empty
        QTest.mouseClick(dlg.routing_fromline_clear, Qt.LeftButton)
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
        QTest.mouseClick(dlg.routing_fromline_map, Qt.LeftButton)
        self.assertFalse(dlg.isVisible())
        self.assertIsInstance(CANVAS.mapTool(), maptools.LineTool)

        # Add some points to the list
        dlg.line_tool.canvasReleaseEvent(self.map_release(100, 5, Qt.LeftButton))
        dlg.line_tool.canvasReleaseEvent(self.map_release(10, 50, Qt.LeftButton))
        dlg.line_tool.canvasReleaseEvent(self.map_release(100, 50, Qt.LeftButton))

        # Add point to be dragged
        dlg.line_tool.canvasReleaseEvent(self.map_release(10, 5, Qt.LeftButton))
        self.assertEqual(dlg.routing_fromline_list.count(), 4)
        self.assertEqual(
            dlg.routing_fromline_list.item(3).text(), "Point 3: -123.375767, 48.445713"
        )

        # Press at previous position
        dlg.line_tool.canvasPressEvent(self.map_press(11, 5, Qt.LeftButton))

        # Release somewhere else
        dlg.line_tool.canvasReleaseEvent(self.map_release(50, 10, Qt.LeftButton))
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
            QEvent.MouseButtonRelease,
            QPoint(x, y),  # Relative to the canvas' dimensions
            side,
            side,
            Qt.NoModifier,
        )

    def map_press(self, x, y, side):
        return QgsMapMouseEvent(
            CANVAS,
            QEvent.MouseButtonPress,
            QPoint(x, y),  # Relative to the canvas' dimensions
            side,
            side,
            Qt.NoModifier,
        )

    def map_dclick(self, x, y, side):
        return QgsMapMouseEvent(
            CANVAS,
            QEvent.MouseButtonDblClick,
            QPoint(x, y),  # Relative to the canvas' dimensions
            side,
            side,
            Qt.NoModifier,
        )
