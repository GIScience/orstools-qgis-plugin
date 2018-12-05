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

admin_levels = {'country': 'COUNTRY',
                'region': 'STATE',
                'locality': 'CITY',
                'postalcode': 'POSTALCODE',
                'street': 'STREET',
                'housenumber': 'NUMBER',
                'name': 'NAME',
                }


def reverse_geocode(client, point_in):
    params = dict()
    params['point.lat'] = point_in.y()
    params['point.lon'] = point_in.x()
    
    response = client.request('/geocode/reverse', params)['features'][0]
    
    response_dict = dict()
    
    x, y = response['geometry'].get('coordinates', None)
    response_dict['Lon'] = x
    response_dict['Lat'] = y

    # Get all properties
    for admin in admin_levels:
        if admin in response['properties']:
            response_dict[admin_levels[admin]] = response['properties'][admin]
                       
    return response_dict
