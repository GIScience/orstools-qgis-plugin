# -*- coding: utf-8 -*-
"""
Created on Thu May 04 09:38:00 2017

@author: nnolde
"""

import requests

import qgis.gui
import qgis.utils
from qgis.core import *
from qgis.gui import *

#TODO: Reproject instead of warning
def CheckCRS(self,crs):
    check = True
    if crs != "EPSG:4326":
        msg = "CRS is {}. Must be EPSG:4326 (WGS84)".format(crs)
        qgis.utils.iface.messageBar().pushMessage(msg, level = qgis.gui.QgsMessageBar.CRITICAL, duration=10)
        check = False
    return check

#TODO: More error checking, e.g. print start/end X & Y in message bar
def CheckStatus(code, req):
    code_text = requests.status_codes._codes[code]
    msg = "HTTP status {}: {}\nGet request: {}".format(code, code_text, req)
    qgis.utils.iface.messageBar().pushMessage(msg, level=qgis.gui.QgsMessageBar.CRITICAL, duration=20)
    return