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
__source__ = "https://github.com/felt/qgis-plugin/blob/main/felt/gui/gui_utils.py"

import os

from qgis.PyQt.QtGui import (
    QIcon,
)


class GuiUtils:
    """
    Utilities for GUI plugin components
    """

    @staticmethod
    def get_icon(icon: str) -> QIcon:
        """
        Returns a plugin icon
        :param icon: icon name (svg file name)
        :return: QIcon
        """
        path = os.path.join(os.path.dirname(__file__), "..", "gui/img", icon)
        if not os.path.exists(path):
            return QIcon()

        return QIcon(path)

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
