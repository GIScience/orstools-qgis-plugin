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
from qgis.core import QgsPointXY

from typing import List

from ORStools import BASE_DIR
from ORStools.common import OPTIMIZATION_MODES


def get_params_optimize(point_list: List[QgsPointXY], ors_profile: str, mode: int) -> dict:
    """
    Build parameters for optimization endpoint

    :param point_list: individual polyline points
    :param ors_profile: ors transport profile to be used
    :param mode: optimization mode
    """
    start = end = None

    if mode == OPTIMIZATION_MODES.index("Fix End Point"):
        end = point_list.pop(-1)
    elif mode == OPTIMIZATION_MODES.index("Fix Start Point"):
        start = point_list.pop(0)
    elif mode == OPTIMIZATION_MODES.index("Fix Start and End Point"):
        start = point_list.pop(0)
        end = point_list.pop(-1)
    elif mode == OPTIMIZATION_MODES.index("Do Round Trip"):
        start = end = point_list.pop(0)

    vehicle = {
        "id": 0,
        "profile": ors_profile
    }

    if start:
        vehicle.update({"start": [round(start.x(), 7), round(start.y(), 7)]})
    if end:
        vehicle.update({"end": [round(end.x(), 7), round(end.y(), 7)]})

    params = {
        'jobs': [{
            "location": [round(point.x(), 7), round(point.y(), 7)],
            "id": point_list.index(point)
        } for point in point_list],
        'vehicles': [vehicle],
        'options': {'g': True}
    }

    return params


def read_help_file(file_name: str):
    """
    Returns the contents of a file from the help folder
    :rtype: str
    """
    file = os.path.join(
        BASE_DIR,
        'help',
        file_name
    )
    with open(file, encoding='utf-8') as help_file:
        msg = help_file.read()
    return msg
