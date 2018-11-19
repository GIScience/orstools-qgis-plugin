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

__version__ = "3.0.6b"

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load OSMtools class from file OS;tools.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .osm_tools import OSMtools
    return OSMtools(iface)
