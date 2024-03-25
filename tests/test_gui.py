from qgis.testing import unittest

from qgis.PyQt.QtTest import QTest
from qgis.PyQt.QtCore import Qt, QEvent, QPoint
from qgis.PyQt.QtWidgets import QPushButton
from qgis.gui import QgsMapCanvas, QgsMapMouseEvent
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
    def test_ORStoolsDialog(self):
        from ORStools.gui.ORStoolsDialog import ORStoolsDialog
        from ORStools.utils import maptools

        CRS = QgsCoordinateReferenceSystem.fromEpsgId(3857)
        CANVAS.setExtent(QgsRectangle(258889, 7430342, 509995, 7661955))
        CANVAS.setDestinationCrs(CRS)

        dlg = ORStoolsDialog(IFACE)
        dlg.open()
        self.assertTrue(dlg.isVisible())

        map_button: QPushButton = dlg.routing_fromline_map
        # click 'routing_fromline_map'
        QTest.mouseClick(map_button, Qt.LeftButton)
        self.assertFalse(dlg.isVisible())
        self.assertIsInstance(CANVAS.mapTool(), maptools.LineTool)

        map_dclick = QgsMapMouseEvent(
            CANVAS,
            QEvent.MouseButtonDblClick,
            QPoint(5, 5),  # Relative to the canvas' dimensions
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier,
        )

        map_click = QgsMapMouseEvent(
            CANVAS,
            QEvent.MouseButtonRelease,
            QPoint(0, 0),  # Relative to the canvas' dimensions
            Qt.LeftButton,
            Qt.LeftButton,
            Qt.NoModifier,
        )
        # click on canvas at [0, 0]
        dlg.line_tool.canvasReleaseEvent(map_click)
        # doubleclick on canvas at [5, 5]
        dlg.line_tool.canvasDoubleClickEvent(map_dclick)

        self.assertTrue(dlg.isVisible())
        self.assertAlmostEqual(
            dlg.routing_fromline_list.item(0).text(), "Point 0: -0.187575, 56.516620"
        )
