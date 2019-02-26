# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ORStools
                                 A QGIS plugin
 QGIS client to query openrouteservice
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

"""
Defines exceptions that are thrown by the ORS client.
"""


class ApiError(Exception):
    """Represents an exception returned by the remote API."""
    def __init__(self, status, message=None):
        self.status = status
        self.message = message

    def __str__(self):
        if self.message is None:
            return self.status
        else:
            return "{} ({})".format(self.status, self.message)


class InvalidKey(Exception):
    """only called for 403"""
    def __init__(self, status, message):
        self.status = status
        self.message = message

    def __str__(self):
        if self.message is None:
            return self.status
        else:
            return "{} ({})".format(self.status, self.message)


class OverQueryLimit(Exception):
    """Signifies that the request failed because the client exceeded its query rate limit."""

    def __init__(self, status, message=None):
        self.status = status
        self.message = message

    def __str__(self):
        if self.message is None:
            return self.status
        else:
            return "{} ({})".format(self.status, self.message)


class Timeout(Exception):
    """The request timed out."""
    pass


class GenericServerError(Exception):
    """Anything else"""

    def __init__(self, status, message=None):
        self.status = status
        self.message = message

    def __str__(self):
        if self.message is None:
            return self.status
        else:
            return "{} ({})".format(self.status, self.message)
