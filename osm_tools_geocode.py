# -*- coding: utf-8 -*-
"""
Created on Tue Feb 07 00:34:21 2017

@author: nnolde
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import * 
import qgis.utils

import requests
import json
import xml.etree.ElementTree as ET

class Geocode:
    def __init__(self, dlg, api_key):
        self.dlg = dlg
        self.url = r"https://api.openrouteservice.org/geocoding?"
                  
        # API parameters
        self.api_key = api_key
        
        self.iface = qgis.utils.iface    
        
    def reverseGeocode(self, point_in):
        x, y = point_in.asPoint()
        req = "{}lang=en&api_key={}&location={},{}".format(self.url, 
                                            self.api_key, 
                                            x, 
                                            y)
        response = requests.get(req)
        root = json.loads(response.text)
        
        loc_place_dict = dict()
        
        x, y = root['features'][0]['geometry']['coordinates']
        loc_place_dict['Lon'] = x
        loc_place_dict['Lat'] = y
        loc_place_dict['COUNTRY'] = root['features'][0]['properties'].get('country', None)
        loc_place_dict['STATE'] = root['features'][0]['properties'].get('state', None)
        loc_place_dict['CITY'] = root['features'][0]['properties'].get('city', None)
        loc_place_dict['POSTALCODE'] = root['features'][0]['properties'].get('postal_code', None)
        loc_place_dict['STREET'] = root['features'][0]['properties'].get('street', None)
        loc_place_dict['NUMBER'] = root['features'][0]['properties'].get('number', None)
        loc_place_dict['NAME'] = root['features'][0]['properties'].get('name', None)
                           
        return loc_place_dict