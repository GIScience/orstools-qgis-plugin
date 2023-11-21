# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ORStools
                                 A QGIS plugin
 QGIS client to query openrouteservice
                              -------------------
        begin                : 2017-02-01
        git sha              : $Format:%H$
        copyright            : (C) 2021 by HeiGIT gGmbH
        email                : support@openrouteservice.heigit.org
 ***************************************************************************/

 This plugin provides access to openrouteservice API functionalities
 (https://openrouteservice.org), developed and
 maintained by the openrouteservice team of HeiGIT gGmbH, Germany. By using
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
import shutil
from packaging import version
import yaml

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
__copyright__ = f'(C) {today.year} by {__author__}'

CONFIG_PATH = os.path.join(os.path.dirname(BASE_DIR), 'ORStools_config.yml')
BASE_CONFIG_PATH = os.path.join(BASE_DIR, "config.yml")

# Compare plugin version with config file version and copy providers if config file is old
try:
    with open(CONFIG_PATH) as f:
        old_config = yaml.safe_load(f)
        config_version = old_config['version']
    # Check if there's a new version of the plugin
    if version.parse(config_version) < version.parse(__version__):
        # Logic for when there's new things in the config.yml
        with open(BASE_CONFIG_PATH) as f:
            new_config = yaml.safe_load(f)
        new_config['providers'] = old_config['providers']
        new_config['version'] = __version__
        with open(CONFIG_PATH, 'w') as f:
            yaml.safe_dump(new_config, f)
except FileNotFoundError:
    # Create config-yaml outside plugin folder to keep settings upon plugin update
    shutil.copyfile(BASE_CONFIG_PATH, CONFIG_PATH)
    with open(CONFIG_PATH, 'a') as f:
        yaml.safe_dump({'version': __version__}, f)

RESOURCE_PREFIX = ":plugins/ORStools/img/"
ENV_VARS = {'ORS_REMAINING': 'X-Ratelimit-Remaining',
            'ORS_QUOTA': 'X-Ratelimit-Limit'}
