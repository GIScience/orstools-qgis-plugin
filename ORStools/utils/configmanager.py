# -*- coding: utf-8 -*-
"""
/***************************************************************************
 OSMtools
                                 A QGIS plugin
 falk
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
import yaml

from ORStools import BASE_DIR, CONFIG_PATH


def read_config():
    with open(os.path.join(BASE_DIR, CONFIG_PATH)) as f:
        doc = yaml.safe_load(f)

    return doc


def write_config(key, value):

    doc = read_config()
    doc[key] = value
    with open(os.path.join(BASE_DIR, CONFIG_PATH), 'w') as f:
        yaml.safe_dump(doc, f)


def write_config_all(new_config):
    """Dumps new config"""
    with open(os.path.join(BASE_DIR, CONFIG_PATH), 'w') as f:
        yaml.safe_dump(new_config, f)


def write_env_var(key, value):
    """update quota env variables"""
    os.environ[key] = value