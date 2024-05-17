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

from typing import Union


def decode_polyline(polyline: str, is3d: bool = False) -> list:
    """Decodes a Polyline string into a GeoJSON geometry.

    :param polyline: An encoded polyline, only the geometry.
    :type polyline: string

    :param is3d: Specifies if geometry contains Z component.
    :type is3d: boolean

    :returns: GeoJSON Linestring geometry
    :rtype: dict
    """
    points = []
    index = lat = lng = z = 0

    while index < len(polyline):
        result = 1
        shift = 0
        while True:
            b = ord(polyline[index]) - 63 - 1
            index += 1
            result += b << shift
            shift += 5
            if b < 0x1F:
                break
        lat += (~result >> 1) if (result & 1) != 0 else (result >> 1)

        result = 1
        shift = 0
        while True:
            b = ord(polyline[index]) - 63 - 1
            index += 1
            result += b << shift
            shift += 5
            if b < 0x1F:
                break
        lng += ~(result >> 1) if (result & 1) != 0 else (result >> 1)

        if is3d:
            result = 1
            shift = 0
            while True:
                b = ord(polyline[index]) - 63 - 1
                index += 1
                result += b << shift
                shift += 5
                if b < 0x1F:
                    break
            if (result & 1) != 0:
                z += ~(result >> 1)
            else:
                z += result >> 1

            points.append([round(lng * 1e-5, 6), round(lat * 1e-5, 6), round(z * 1e-2, 1)])

        else:
            points.append([round(lng * 1e-5, 6), round(lat * 1e-5, 6)])

    return points


def decode_extrainfo(extra_info: str, key: int) -> Union[int, str]:
    waytypes = [
        "Unknown",
        "state Road",
        "Road",
        "Street",
        "Path",
        "Track",
        "Cycleway",
        "Footway",
        "Ferry",
        "Construction",
    ]
    surfaces = [
        "Unknown",
        "Paved",
        "Unpaved",
        "Asphalt",
        "Concrete",
        "Cobblestone",
        "Metal",
        "Wood",
        "Compacted Gravel",
        "Fine Grave",
        "Gravel",
        "Dirt",
        "Ground",
        "Ice",
        "Paving Stones",
        "Sand",
        "Woodchips",
        "Grass",
        "Grass Paver",
    ]
    waycategory = ["Ford", "Ferry", "Steps", "Tollways", "Highway"]
    restrictions = ["Permissive", "Private", "Delivery", "Destination", "Customers", "No"]
    steepness = [
        ">=16% decline",
        "10% - <16% decline",
        "7% - <10% decline",
        "4% - <7% decline",
        "1% - <4% decline",
        "0% - <1% decline",
        "1% - <4% incline",
        "4% - <7% incline",
        "7% - <10% incline",
        "10% - <16% incline",
        ">=16% incline",
    ]

    if extra_info == "waytypes":
        try:
            return waytypes[key]
        except IndexError:
            return "Unknown"
    elif extra_info == "surface":
        try:
            return surfaces[key]
        except IndexError:
            return "Unknown"
    elif extra_info == "waycategory":
        binary = list(bin(key))[2:]
        padding = ["0"] * (len(waycategory) - len(binary))
        padded_binary = padding + binary
        category = ""

        for set_bit, value in zip(padded_binary, waycategory):
            if set_bit == "1":
                category += value

        if category == "":
            return "No category"

        return category
    elif extra_info == "roadaccessrestrictions":
        binary = list(bin(key))[2:]
        padding = ["0"] * (len(restrictions) - len(binary))
        padded_binary = padding + binary
        restriction = ""

        for set_bit, value in zip(padded_binary, restrictions):
            if set_bit == "1":
                restriction += value
                restriction += " "

        if restriction == "":
            return "None"

        return restriction
    elif extra_info == "steepness":
        # We get values from -5 to 5 here, but our decoded array is 11 values long.
        key += 5
        try:
            return steepness[key]
        except IndexError:
            return "No steepness available"
    elif extra_info == "traildifficulty":
        # TODO: we need to differentiate the profile here…
        return key
    else:
        return key
