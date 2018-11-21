# -*- coding: utf-8 -*-
"""
/***************************************************************************
 OSMtools
                                 A QGIS plugin
 falk
                             -------------------
        begin                : 2017-02-01
        copyright            : (C) 2017 by nils
        email                : nils
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""

import os.path

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load OSMtools class from file OS;tools.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """

    from .OSMtoolsPlugin import OSMtools
    return OSMtools(iface)

__version__ = '3.2'
__author__ = 'Nils Nolde'
__date__ = '2018-11-19'
__copyright__ = '(C) 2018 by Nils Nolde'

# Define plugin wide constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_DIR = os.path.join(BASE_DIR, 'static', 'img')
CONFIG = os.path.join(BASE_DIR, 'config.yml')
