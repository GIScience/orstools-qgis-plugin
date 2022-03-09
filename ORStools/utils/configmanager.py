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
import os

import yaml

from ORStools import CONFIG_PATH


def read_config():
    """
    Reads config.yml from file and returns the parsed dict.

    :returns: Parsed settings dictionary.
    :rtype: dict
    """
    with open(CONFIG_PATH) as f:
        doc = yaml.safe_load(f)

    return doc


def write_config(new_config):
    """
    Dumps new config

    :param new_config: new provider settings after altering in dialog.
    :type new_config: dict
    """
    with open(CONFIG_PATH, 'w') as f:
        yaml.safe_dump(new_config, f)


def write_env_var(key, value):
    """
    Update quota env variables

    :param key: environment variable to update.
    :type key: str

    :param value: value for env variable.
    :type value: str
    """
    os.environ[key] = value


def set_active_provider(new_index: int):
    """
    Sets the boolean 'active' flag for the provider to True and for all others to False

    :param new_index: index of the new active provider in the config.yml providers list
    :type new_index: int
    """
    config = read_config()
    for i, provider in enumerate(config["providers"]):
        provider["active"] = i == new_index
    write_config(config)


def get_active_provider_index() -> int:
    """
    Get the active provider index.
    In case the active provider was removed the first provider is set to active.

    :return: active provider index
    :rtype: int
    """
    providers = read_config()["providers"]
    active_list = [p['active'] if 'active' in p.keys() else False for p in providers]
    if True in active_list:
        return active_list.index(True)
    else:
        set_active_provider(0)
        return 0
