# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ORStools
                                 A QGIS plugin
 QGIS client to query openrouteservice
                              -------------------
        begin                : 2017-02-01
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Nils Nolde
        email                : nils.nolde@gmail.com
 ***************************************************************************/

 This plugin provides access to the various APIs from OpenRouteService
 (https://openrouteservice.org), developed and
 maintained by GIScience team at University of Heidelberg, Germany. By using
 this plugin you agree to the ORS terms of service
 (https://openrouteservice.org/terms-of-service/).

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os.path
import configparser
from datetime import datetime


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load ORStools class

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """

    from .ORStoolsPlugin import ORStools
    return ORStools(iface)


# Define plugin wide constants
PLUGIN_NAME = 'ORS Tools'
DEFAULT_COLOR = '#a8b1f5'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RESOURCE_PREFIX = ":plugins/ORStools/img/"
CONFIG_PATH = os.path.join(BASE_DIR, 'config.yml')
ENV_VARS = {'ORS_REMAINING': 'X-Ratelimit-Remaining',
            'ORS_QUOTA': 'X-Ratelimit-Limit'}

# Read metadata.txt
METADATA = configparser.ConfigParser()
METADATA.read(os.path.join(BASE_DIR, 'metadata.txt'), encoding='utf-8')
today = datetime.today()

__version__ = METADATA['general']['version']
__author__ = METADATA['general']['author']
__email__ = METADATA['general']['email']
__web__ = METADATA['general']['homepage']
__help__ = METADATA['general']['help']
__date__ = today.strftime('%Y-%m-%d')
__copyright__ = '(C) {} by {}'.format(today.year, __author__)
