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

from datetime import datetime, timedelta
import requests
import random
import time
import collections
from urllib.parse import urlencode

import OSMtools
from OSMtools.utils import exceptions, configmanager

_USER_AGENT = "ORSClientQGISv{}".format(OSMtools.__version__)
_RETRIABLE_STATUSES = [503]
_DEFAULT_BASE_URL = "https://api.openrouteservice.org"


class Client(object):
    """Performs requests to the ORS API services."""

    def __init__(self, iface,
                 retry_timeout=60,
                 retry_over_query_limit=False):
        """
        :param iface: A QGIS interface instance.
        :type iface: QgisInterface

        :param retry_timeout: Timeout across multiple retriable requests, in
            seconds.
        :type retry_timeout: int
        """
        
        base_params = configmanager.read()
        
        (self.key, 
         self.base_url, 
         self.queries_per_minute) = [v for (k, v) in sorted(base_params.items())]
        self.iface = iface
        
        self.session = requests.Session()
        
        self.retry_over_query_limit = retry_over_query_limit
        self.retry_timeout = timedelta(seconds=retry_timeout)
        self.requests_kwargs = dict()
        self.requests_kwargs.update({
            "headers": {"User-Agent": _USER_AGENT,
                        'Content-type': 'application/json'}
        })

        self.sent_times = collections.deque("", self.queries_per_minute)

    def request(self, 
                url, params,
                first_request_time=None,
                retry_counter=0,
                requests_kwargs=None,
                post_json=None):
        """Performs HTTP GET/POST with credentials, returning the body asdlg
        JSON.

        :param url: URL extension for request. Should begin with a slash.
        :type url: string

        :param params: HTTP GET parameters.
        :type params: dict or list of key/value tuples

        :param first_request_time: The time of the first request (None if no
            retries have occurred).
        :type first_request_time: datetime.datetime

        :param retry_counter: The number of this retry, or zero for first attempt.
        :type retry_counter: int

        :param requests_kwargs: Same extra keywords arg for requests as per
            __init__, but provided here to allow overriding internally on a
            per-request basis.
        :type requests_kwargs: dict

        :param post_json: Parameters for POST endpoints
        :type post_json: dict

        :raises ApiError: when the API returns an error.
        :raises Timeout: if the request timed out.
        :raises TransportError: when something went wrong while trying to
            execute a request.
            
        :rtype: dict from JSON response.
        """

        if not first_request_time:
            first_request_time = datetime.now()

        elapsed = datetime.now() - first_request_time
        if elapsed > self.retry_timeout:
            raise exceptions.Timeout()

        if retry_counter > 0:
            # 0.5 * (1.5 ^ i) is an increased sleep time of 1.5x per iteration,
            # starting at 0.5s when retry_counter=1. The first retry will occur
            # at 1, so subtract that first.
            delay_seconds = 1.5 ** (retry_counter - 1)

            # Jitter this value by 50% and pause.
            time.sleep(delay_seconds * (random.random() + 0.5))

        authed_url = self._generate_auth_url(url,
                                             params,
                                             )

        # Default to the client-level self.requests_kwargs, with method-level
        # requests_kwargs arg overriding.
        requests_kwargs = requests_kwargs or {}
        final_requests_kwargs = dict(self.requests_kwargs, **requests_kwargs)

        # Check if the time of the nth previous query (where n is
        # queries_per_second) is under a second ago - if so, sleep for
        # the difference.
        if self.sent_times and len(self.sent_times) == self.queries_per_minute:
            elapsed_since_earliest = time.time() - self.sent_times[0]
            if elapsed_since_earliest < 60:
                self.iface.messageBar().pushInfo('Limit exceeded',
                                                 'Request limit of {} per minute exceeded. '
                                                 'Wait for {} seconds'.format(self.queries_per_minute, 
                                                                              60 - elapsed_since_earliest))
                time.sleep(60 - elapsed_since_earliest)
        
        # Determine GET/POST.
        # post_json is so far only sent from matrix call
        requests_method = self.session.get
        if post_json is not None:
            requests_method = self.session.post
            final_requests_kwargs["json"] = post_json

        print("url:\n{}\nParameters:\n{}".format(self.base_url+authed_url,
                                                 final_requests_kwargs))

        try:
            response = requests_method(self.base_url + authed_url,
                                       **final_requests_kwargs)
        except requests.exceptions.Timeout:
            raise exceptions.Timeout()
        except Exception:
            raise

        if response.status_code in _RETRIABLE_STATUSES:
            # Retry request.
            print('Server down.\nRetrying for the {}th time.'.format(retry_counter + 1))
            
            return self.request(url, params, first_request_time,
                                 retry_counter + 1, requests_kwargs, post_json)

        try:
            result = self._get_body(response)
            self.sent_times.append(time.time())
            return result
        except exceptions.RetriableRequest as e:
            if isinstance(e, exceptions.OverQueryLimit) and not self.retry_over_query_limit:
                raise
            
            self.iface.messageBar().pushInfo('Rate limit exceeded.\nRetrying for the {}th time.'.format(retry_counter + 1))
            return self.request(url, params, first_request_time,
                                retry_counter + 1, requests_kwargs, post_json)
        except Exception:
            raise

    @staticmethod
    def _get_body(response):
        """
        Casts JSON response to dict
        
        :param response: The HTTP response of the request.
        :type response: JSON object
        
        :rtype: dict from JSON
        """
        body = response.json()
        error = body.get('error')
        status_code = response.status_code
        
        if status_code == 429:
            raise exceptions.OverQueryLimit(
                str(status_code), error)
        if status_code != 200:
            raise exceptions.ApiError(status_code,
                                      error['message'])

        return body

    def _generate_auth_url(self, path, params):
        """Returns the path and query string portion of the request URL, first
        adding any necessary parameters.

        :param path: The path portion of the URL.
        :type path: string

        :param params: URL parameters.
        :type params: dict or list of key/value tuples

        :rtype: string

        """
        
        if type(params) is dict:
            params = sorted(dict(**params).items())
        
        # Only auto-add API key when using ORS. If own instance, API key must
        # be explicitly added to params
        if self.key:
            params.append(("api_key", self.key))
            return path + "?" + _urlencode_params(params)
        elif self.base_url != _DEFAULT_BASE_URL:
            return path + "?" + _urlencode_params(params)

        raise ValueError("No API key specified. "
                         "Visit https://openrouteservice.org/dev/#/home "
                         "to create one.")


def _urlencode_params(params):
    """URL encodes the parameters.

    :param params: The parameters
    :type params: list of key/value tuples.

    :rtype: string
    """
    # urlencode does not handle unicode strings in Python 2.
    # Firstly, normalize the values so they get encoded correctly.
    params = [(key, _normalize_for_urlencode(val)) for key, val in params]
    # Secondly, unquote unreserved chars which are incorrectly quoted
    # by urllib.urlencode, causing invalid auth signatures. See GH #72
    # for more info.
    return requests.utils.unquote_unreserved(urlencode(params))


try:
    unicode
    # NOTE(cbro): `unicode` was removed in Python 3. In Python 3, NameError is
    # raised here, and caught below.

    def _normalize_for_urlencode(value):
        """(Python 2) Converts the value to a `str` (raw bytes)."""
        if isinstance(value, unicode):
            return value.encode('utf8')

        if isinstance(value, str):
            return value

        return _normalize_for_urlencode(str(value))

except NameError:
    def _normalize_for_urlencode(value):
        """(Python 3) No-op."""
        # urlencode in Python 3 handles all the types we are passing it.
        return value
