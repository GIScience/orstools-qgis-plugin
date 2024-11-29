# -*- coding: utf-8 -*-
"""GUI Utilities

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""

__author__ = "(C) 2018 by Nyall Dawson"
__date__ = "20/04/2018"
__copyright__ = "Copyright 2018, North Road"
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = "$Format:%H$"

import math
import os
import re
from typing import Optional, Union

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import (
    QIcon,
    QFont,
    QFontMetrics,
    QImage,
    QPixmap,
    QFontDatabase,
    QColor,
    QPainter,
)
from qgis.PyQt.QtSvg import QSvgRenderer
from qgis.PyQt.QtWidgets import QMenu
from qgis.core import Qgis
from qgis.utils import iface

from ORStools.utils import logger

FONT_FAMILIES = ""

FELT_STYLESHEET = """
QDialog {
    background-color: #ececec;
    color: black;
}
QLabel {
    color: black !important;
    }

QPushButton {
    background: solid #3d521e !important;
    color: white !important;
}

QLineEdit {
    background: solid white;
    color: black;
}

QProgressBar {
    background: solid white;
}

"""


class GuiUtils:
    """
    Utilities for GUI plugin components
    """

    APPLICATION_FONT_MAP = {}

    @staticmethod
    def set_link_color(
        html: str, wrap_color=True, color: Optional[Union[QColor, str]] = None
    ) -> str:
        """
        Adds style tags to links in a HTML string for the standard link color
        """
        if color:
            if isinstance(color, str):
                color_string = color
            else:
                color_string = color.name()
        else:
            color_string = "rgba(0,0,0,.3)"
        res = re.sub(r"(<a href.*?)>", r'\1 style="color: {};">'.format(color_string), html)
        if wrap_color:
            res = '<span style="color: {};">{}</span>'.format(color_string, res)
        return res

    @staticmethod
    def get_icon(icon: str) -> QIcon:
        """
        Returns a plugin icon
        :param icon: icon name (svg file name)
        :return: QIcon
        """
        path = GuiUtils.get_icon_svg(icon)
        if not path:
            return QIcon()

        return QIcon(path)

    @staticmethod
    def get_icon_svg(icon: str) -> str:
        """
        Returns a plugin icon's SVG file path
        :param icon: icon name (svg file name)
        :return: icon svg path
        """
        path = os.path.join(os.path.dirname(__file__), "..", "gui/img", icon)
        logger.log(path)
        if not os.path.exists(path):
            return ""

        return path

    @staticmethod
    def get_icon_pixmap(icon: str) -> QPixmap:
        """
        Returns a plugin icon's PNG file path
        :param icon: icon name (png file name)
        :return: icon png path
        """
        path = os.path.join(os.path.dirname(__file__), "..", "icons", icon)
        if not os.path.exists(path):
            return QPixmap()

        im = QImage(path)
        return QPixmap.fromImage(im)

    @staticmethod
    def get_svg_as_image(
        icon: str,
        width: int,
        height: int,
        background_color: Optional[QColor] = None,
        device_pixel_ratio: float = 1,
    ) -> QImage:
        """
        Returns an SVG returned as an image
        """
        path = GuiUtils.get_icon_svg(icon)
        if not os.path.exists(path):
            return QImage()

        renderer = QSvgRenderer(path)
        image = QImage(
            int(width * device_pixel_ratio), int(height * device_pixel_ratio), QImage.Format_ARGB32
        )
        image.setDevicePixelRatio(device_pixel_ratio)
        if not background_color:
            image.fill(Qt.transparent)
        else:
            image.fill(background_color)

        painter = QPainter(image)
        painter.scale(1 / device_pixel_ratio, 1 / device_pixel_ratio)
        renderer.render(painter)
        painter.end()

        return image

    @staticmethod
    def get_ui_file_path(file: str) -> str:
        """
        Returns a UI file's path
        :param file: file name (uifile name)
        :return: ui file path
        """
        path = os.path.join(os.path.dirname(__file__), "..", "gui", file)
        if not os.path.exists(path):
            return path

        return path

    @staticmethod
    def scale_icon_size(standard_size: int) -> int:
        """
        Scales an icon size accounting for device DPI
        """
        fm = QFontMetrics((QFont()))
        scale = 1.1 * standard_size / 24.0
        return int(
            math.floor(max(Qgis.UI_SCALE_FACTOR * fm.height() * scale, float(standard_size)))
        )

    @staticmethod
    def get_default_font() -> QFont:
        """
        Returns the best font match for the Koordinates default font
        families which is available on the system
        """
        for family in FONT_FAMILIES.split(","):
            family_cleaned = re.match(r"^\s*\'?(.*?)\'?\s*$", family).group(1)
            font = QFont(family_cleaned)
            if font.exactMatch():
                return font

        return QFont()

    @staticmethod
    def get_font_path(font: str) -> str:
        """
        Returns the path to an included font file
        :param font: font name
        :return: font file path
        """
        path = os.path.join(os.path.dirname(__file__), "..", "fonts", font)
        if not os.path.exists(path):
            return ""

        return path

    @staticmethod
    def get_embedded_font(font: str) -> QFont:
        """
        Returns a font created from an embedded font file
        """
        if font in GuiUtils.APPLICATION_FONT_MAP:
            return GuiUtils.APPLICATION_FONT_MAP[font]

        path = GuiUtils.get_font_path(font)
        if not path:
            return QFont()

        res = QFontDatabase.addApplicationFont(path)
        families = QFontDatabase.applicationFontFamilies(res)
        installed_font = QFont(families[0])
        GuiUtils.APPLICATION_FONT_MAP[font] = installed_font
        return installed_font

    @staticmethod
    def get_project_import_export_menu() -> Optional[QMenu]:
        """
        Returns the application Project - Import/Export sub menu
        """
        try:
            # requires QGIS 3.30+
            return iface.projectImportExportMenu()
        except AttributeError:
            pass

        project_menu = iface.projectMenu()
        matches = [m for m in project_menu.children() if m.objectName() == "menuImport_Export"]
        if matches:
            return matches[0]

        return None
