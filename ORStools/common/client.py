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

import json
import random
import time
from datetime import datetime, timedelta
from typing import Union, Dict, List, Optional
from urllib.parse import urlencode

from qgis.PyQt.QtCore import QObject, pyqtSignal
from requests.utils import unquote_unreserved

from ORStools import __version__
from ORStools.common import networkaccessmanager
from ORStools.utils import exceptions, configmanager, logger

from qgis.core import QgsSettings

_USER_AGENT = f"ORSQGISClient@v{__version__}"


class Client(QObject):
    """Performs requests to the ORS API services."""

    def __init__(self, provider: Optional[dict] = None, agent: Optional[str] = None) -> None:
        """
        :param provider: A openrouteservice provider from config.yml
        :type provider: dict

        :param retry_timeout: Timeout across multiple retryable requests, in
            seconds.
        :type retry_timeout: int
        """
        QObject.__init__(self)

        self.key = provider["key"]
        self.base_url = provider["base_url"]
        self.ENV_VARS = provider.get("ENV_VARS")

        # self.session = requests.Session()
        retry_timeout = provider.get("timeout")

        self.nam = networkaccessmanager.NetworkAccessManager(debug=False, timeout=retry_timeout)

        self.retry_timeout = timedelta(seconds=retry_timeout)
        self.headers = {
            "User-Agent": _USER_AGENT,
            "Content-type": "application/json",
            "Authorization": provider["key"],
        }

        self.settings = QgsSettings()
        # Read the current value
        self.user_agent = self.settings.value("qgis/networkAndProxy/userAgent")
        # Set a new value
        self.settings.setValue("qgis/networkAndProxy/userAgent", agent)

        # Save some references to retrieve in client instances
        self.url = None
        self.warnings = None

    overQueryLimit = pyqtSignal()

    def request(
        self,
        url: str,
        params: dict,
        first_request_time: Optional[datetime.time] = None,
        retry_counter: int = 0,
        post_json: Optional[dict] = None,
    ):
        """Performs HTTP GET/POST with credentials, returning the body as
        JSON.

        :param url: URL extension for request. Should begin with a slash.
        :type url: string

        :param params: HTTP GET parameters.
        :type params: dict or list of key/value tuples

        :param first_request_time: The time of the first request (None if no
            retries have occurred).
        :type first_request_time: datetime.datetime

        :param retry_counter: Amount of retries with increasing timeframe before raising a timeout exception
        :type retry_counter: int

        :param post_json: Parameters for POST endpoints
        :type post_json: dict

        :param retry_counter: Duration the requests will be retried for before
            raising a timeout exception.
        :type retry_counter: int

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
            delay_seconds = 1.5 ** (retry_counter - 1)

            # Jitter this value by 50% and pause.
            time.sleep(delay_seconds * (random.random() + 0.5))

        authed_url = self._generate_auth_url(
            url,
            params,
        )
        self.url = self.base_url + authed_url

        # Default to the client-level self.requests_kwargs, with method-level
        # requests_kwargs arg overriding.
        # final_requests_kwargs = self.requests_kwargs

        # Determine GET/POST
        # requests_method = self.session.get
        requests_method = "GET"
        body = None
        if post_json is not None:
            # requests_method = self.session.post
            # final_requests_kwargs["json"] = post_json
            body = post_json
            requests_method = "POST"

        logger.log(f"url: {self.url}\nParameters: {json.dumps(body, indent=2)}", 0)

        try:
            response, content = self.nam.request(
                self.url, method=requests_method, body=body, headers=self.headers, blocking=True
            )
        except networkaccessmanager.RequestsExceptionTimeout:
            raise exceptions.Timeout

        except networkaccessmanager.RequestsException:
            try:
                self._check_status()

            except exceptions.OverQueryLimit as e:
                # Let the instances know something happened
                # noinspection PyUnresolvedReferences
                self.overQueryLimit.emit()
                logger.log(f"{e.__class__.__name__}: {str(e)}", 1)

                return self.request(url, params, first_request_time, retry_counter + 1, post_json)

            except exceptions.ApiError as e:
                logger.log(
                    f"Feature ID {post_json['id']} caused a {e.__class__.__name__}: {str(e)}", 2
                )
                raise

            raise

        # Write env variables if successful
        if self.ENV_VARS:
            for env_var in self.ENV_VARS:
                configmanager.write_env_var(
                    env_var, response.headers.get(self.ENV_VARS[env_var], "None")
                )

        # Reset to old value
        self.settings.setValue("qgis/networkAndProxy/userAgent", self.user_agent)

        return json.loads(content.decode("utf-8"))

    def _check_status(self) -> None:
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
        message = (
            self.nam.http_call_result.text
            if self.nam.http_call_result.text != ""
            else self.nam.http_call_result.reason
        )

        if not status_code:
            raise Exception(
                f"{message}. Are your provider settings correct and the provider ready?"
            )

        elif status_code == 403:
            raise exceptions.InvalidKey(str(status_code), message)

        elif status_code == 429:
            raise exceptions.OverQueryLimit(str(status_code), message)
        # Internal error message for Bad Request
        elif 400 <= status_code < 500:
            raise exceptions.ApiError(str(status_code), message)
        # Other HTTP errors have different formatting
        elif status_code != 200:
            raise exceptions.GenericServerError(str(status_code), message)

    def _generate_auth_url(self, path: str, params: Union[Dict, List]) -> str:
        """Returns the path and query string portion of the request URL, first
        adding any necessary parameters.

        :param path: The path portion of the URL.
        :type path: string

        :param params: URL parameters.
        :type params: dict or list of key/value tuples

        :returns: encoded URL
        :rtype: string
        """

        if isinstance(params, dict):
            params = sorted(dict(**params).items())

        # Only auto-add API key when using ORS. If own instance, API key must
        # be explicitly added to params
        # if self.key:
        #     params.append(("api_key", self.key))

        return path + "?" + unquote_unreserved(urlencode(params))
