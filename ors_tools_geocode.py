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
import xml.etree.ElementTree as ET

class Geocode:
    def __init__(self, dlg, api_key):
        self.dlg = dlg
        self.url = r"http://openls.geog.uni-heidelberg.de/geocode?"
        self.ns = {'gml': 'http://www.opengis.net/gml',
                  'xls': "http://www.opengis.net/xls",
                  'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
                  
        # API parameters
        self.api_key = api_key
        
        self.iface = qgis.utils.iface    
        
    def reverseGeocode(self, point_in):
        x, y = point_in.asPoint()
        req = "{}api_key={}&pos={} {}".format(self.url, 
                                            self.api_key, 
                                            x, 
                                            y)
        response = requests.get(req)
        root = ET.fromstring(response.content)
        access_path = root.find("xls:Response/"
                                "xls:ReverseGeocodeResponse/"
                                "xls:ReverseGeocodedLocation",
                                self.ns)
        
        loc_place_dict = dict()
        
        pos = access_path.find("gml:Point/gml:pos", self.ns).text
        x, y  = pos.split(" ")
        loc_place_dict['Lon'] = float(x)
        loc_place_dict['Lat'] = float(y)
        loc_place_dict['DIST_INPUT'] = access_path.find("xls:SearchCentreDistance", self.ns).get('value')
        loc_list = access_path.findall("xls:StreetAddress/xls:Building", self.ns)
        for element in loc_list:
            loc_place_dict[element.keys()[0][:10].upper()] = element.get(element.keys()[0], "")
        loc_list = access_path.findall("xls:StreetAddress/xls:PostalCode", self.ns)
        for element in loc_list:
            loc_place_dict['POSTALCODE'] = element.text
        loc_list = access_path.findall("xls:Address/xls:StreetAddress/xls:Street", self.ns)
        for element in loc_list:
            loc_place_dict[element.keys()[0][:10].upper()] = element.get(element.keys()[0], "")
        loc_list = access_path.findall("xls:Address/xls:Place", self.ns)
        for element in loc_list:
            loc_place_dict[element.get('type')[:10].upper()] = unicode(element.text)
                           
        return loc_place_dict