# -*- coding: utf-8 -*-
"""
Created on Tue Feb 07 00:34:21 2017

@author: nnolde
"""

#from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import * 
import qgis.utils

from pprint import pprint

import requests
import json

from ORStools import osm_tools_aux
        
def reverseGeocode(point_in, api_key):
    x, y = point_in.asPoint()
    base_url = 'https://api.openrouteservice.org/geocoding?'
    req = "{}lang=en&api_key={}&location={},{}".format(base_url, 
                                        api_key, 
                                        x, 
                                        y)
    response = requests.get(req)
    root = json.loads(response.text)
    
    # Check if there was an HTTP error and terminate
    http_status = response.status_code
    
    try:
        if http_status > 200:
            osm_tools_aux.CheckStatus(http_status, req)
            return
    except: 
        raise
    
    loc_place_dict = dict()
    
    x, y = root['features'][0]['geometry'].get('coordinates',None)
    loc_place_dict['Lon'] = x
    loc_place_dict['Lat'] = y
    loc_place_dict['COUNTRY'] = root['features'][0]['properties'].get('country', None)
    loc_place_dict['STATE'] = root['features'][0]['properties'].get('state', None)
    loc_place_dict['CITY'] = root['features'][0]['properties'].get('county', None)
    loc_place_dict['POSTALCODE'] = root['features'][0]['properties'].get('postal_code', None)
    loc_place_dict['STREET'] = root['features'][0]['properties'].get('street', None)
    loc_place_dict['NUMBER'] = root['features'][0]['properties'].get('house_number', None)
                       
    return loc_place_dict     