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

from datetime import datetime, timedelta
import requests
import time
from urllib.parse import urlencode
import random
import json

from PyQt5.QtCore import QObject, pyqtSignal

from ORStools import __version__
from ORStools.common import networkaccessmanager
from ORStools.utils import exceptions, configmanager, logger

_USER_AGENT = "ORSQGISClient@v{}".format(__version__)


class Client(QObject):
    """Performs requests to the ORS API services."""

    def __init__(self,
                 provider=None,
                 retry_timeout=60):
        """
        :param provider: A openrouteservice provider from config.yml
        :type provider: dict

        :param retry_timeout: Timeout across multiple retriable requests, in
            seconds.
        :type retry_timeout: int
        """
        QObject.__init__(self)

        self.key = provider['key']
        self.base_url = provider['base_url']
        self.ENV_VARS = provider.get('ENV_VARS')
        
        # self.session = requests.Session()
        self.nam = networkaccessmanager.NetworkAccessManager(debug=False)

        self.retry_timeout = timedelta(seconds=retry_timeout)
        self.headers = {
                "User-Agent": _USER_AGENT,
                'Content-type': 'application/json',
                'Authorization': provider['key']
            }

        # Save some references to retrieve in client instances
        self.url = None
        self.warnings = None

    overQueryLimit = pyqtSignal()
    def request(self, 
                url, params,
                first_request_time=None,
                retry_counter=0,
                post_json=None):
        """Performs HTTP GET/POST with credentials, returning the body as
        JSON.

        :param url: URL extension for request. Should begin with a slash.
        :type url: string

        :param params: HTTP GET parameters.
        :type params: dict or list of key/value tuples

        :param first_request_time: The time of the first request (None if no
            retries have occurred).
        :type first_request_time: datetime.datetime

        :param post_json: Parameters for POST endpoints
        :type post_json: dict

        :raises ORStools.utils.exceptions.ApiError: when the API returns an error.

        :returns: openrouteservice response body
        :rtype: dict
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
            delay_seconds = 1.5**(retry_counter - 1)

            # Jitter this value by 50% and pause.
            time.sleep(delay_seconds * (random.random() + 0.5))

        authed_url = self._generate_auth_url(url,
                                             params,
                                             )
        self.url = self.base_url + authed_url

        # Default to the client-level self.requests_kwargs, with method-level
        # requests_kwargs arg overriding.
        # final_requests_kwargs = self.requests_kwargs
        
        # Determine GET/POST
        # requests_method = self.session.get
        requests_method = 'GET'
        body = None
        if post_json is not None:
            # requests_method = self.session.post
            # final_requests_kwargs["json"] = post_json
            body = post_json
            requests_method = 'POST'

        logger.log(
            "url: {}\nParameters: {}".format(
                self.url,
                # final_requests_kwargs
                body
            ),
            0
        )

        try:
            # response = requests_method(
            #     self.base_url + authed_url,
            #     **final_requests_kwargs
            # )
            response, content = self.nam.request(self.url,
                                           method=requests_method,
                                           body=body,
                                           headers=self.headers,
                                           blocking=True)
        # except requests.exceptions.Timeout:
        #     raise exceptions.Timeout()
        except networkaccessmanager.RequestsExceptionTimeout:
            raise exceptions.Timeout

        except networkaccessmanager.RequestsException:
            try:
                # result = self._get_body(response)
                self._check_status()

            except exceptions.OverQueryLimit as e:

                # Let the instances know smth happened
                self.overQueryLimit.emit()
                logger.log("{}: {}".format(e.__class__.__name__, str(e)), 1)

                return self.request(url, params, first_request_time, retry_counter + 1, post_json)

            except exceptions.ApiError as e:
                logger.log("Feature ID {} caused a {}: {}".format(params['id'], e.__class__.__name__, str(e)), 2)
                raise

            raise

        # Write env variables if successful
        if self.ENV_VARS:
            for env_var in self.ENV_VARS:
                configmanager.write_env_var(env_var, response.headers.get(self.ENV_VARS[env_var], 'None'))

        return json.loads(content.decode('utf-8'))

    def _check_status(self):
        """
        Casts JSON response to dict

        :raises ORStools.utils.exceptions.OverQueryLimitError: when rate limit is exhausted, HTTP 429
        :raises ORStools.utils.exceptions.ApiError: when the backend API throws an error, HTTP 400
        :raises ORStools.utils.exceptions.InvalidKey: when API key is invalid (or quota is exceeded), HTTP 403
        :raises ORStools.utils.exceptions.GenericServerError: all other HTTP errors

        :returns: response body
        :rtype: dict
        """

        status_code = self.nam.http_call_result.status_code
        message = self.nam.http_call_result.text if self.nam.http_call_result.text != '' else self.nam.http_call_result.reason

        if status_code == 403:
            raise exceptions.InvalidKey(
                str(status_code),
                # error,
                message
            )

        if status_code == 429:
            raise exceptions.OverQueryLimit(
                str(status_code),
                # error,
                message
            )
        # Internal error message for Bad Request
        if 400 < status_code < 500:
            raise exceptions.ApiError(
                str(status_code),
                # error,
                message
            )
        # Other HTTP errors have different formatting
        if status_code != 200:
            raise exceptions.GenericServerError(
                str(status_code),
                # error,
                message
            )

    def _generate_auth_url(self, path, params):
        """Returns the path and query string portion of the request URL, first
        adding any necessary parameters.

        :param path: The path portion of the URL.
        :type path: string

        :param params: URL parameters.
        :type params: dict or list of key/value tuples

        :returns: encoded URL
        :rtype: string
        """
        
        if type(params) is dict:
            params = sorted(dict(**params).items())
        
        # Only auto-add API key when using ORS. If own instance, API key must
        # be explicitly added to params
        # if self.key:
        #     params.append(("api_key", self.key))

        return path + "?" + requests.utils.unquote_unreserved(urlencode(params))
