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

from qgis.PyQt.QtCore import QObject, pyqtSignal, QUrl
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.utils import iface
from qgis.core import (
    Qgis,
    QgsSettings,
    QgsBlockingNetworkRequest,
    QgsNetworkAccessManager
)
from requests.utils import unquote_unreserved

from ORStools import __version__
from ORStools.utils import exceptions, configmanager, logger

_USER_AGENT = f"ORSQGISClient@v{__version__}"

class Client(QObject):
    """Performs requests to the ORS API services."""

    overQueryLimit = pyqtSignal(int)

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
        self.timeout = provider.get("timeout")

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

    def request(
        self,
        url: str,
        params: dict,
        first_request_time: Optional[datetime] = None,
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
        if elapsed > timedelta(seconds=self.timeout):
            raise exceptions.Timeout()

        authed_url = self._generate_auth_url(url, params)
        self.url = self.base_url + authed_url

        request = QNetworkRequest(QUrl(self.url))
        for header, value in self.headers.items():
            request.setRawHeader(header.encode(), value.encode())

        blocking_request = QgsBlockingNetworkRequest()

        logger.log(f"url: {self.url}\nParameters: {json.dumps(post_json, indent=2)}", 0)

        try:
            if post_json is not None:
                result = blocking_request.post(request, json.dumps(post_json).encode())
            else:
                result = blocking_request.get(request)

            if result != QgsBlockingNetworkRequest.NoError:
                self._check_status(blocking_request)

            reply = blocking_request.reply()
            if not reply:
                raise exceptions.GenericServerError("0", "No response received")

            content = reply.content().data().decode('utf-8')

        except Exception as e:
            try:
                self._check_status(blocking_request)
            except exceptions.OverQueryLimit as e:

                self.overQueryLimit.emit()
                logger.log(f"{e.__class__.__name__}: {str(e)}", 1)
                return self.request(url, params, first_request_time, retry_counter + 1, post_json)
            except exceptions.ApiError as e:
                if post_json:
                    logger.log(
                        f"Feature ID {post_json['id']} caused a {e.__class__.__name__}: {str(e)}", 2
                    )
                raise
            raise

        if self.ENV_VARS:
            for env_var in self.ENV_VARS:
                header_value = reply.rawHeader(self.ENV_VARS[env_var].encode()).data().decode()
                configmanager.write_env_var(env_var, header_value)

        self.settings.setValue("qgis/networkAndProxy/userAgent", self.user_agent)

        return json.loads(content)

    def _check_status(self, blocking_request: QgsBlockingNetworkRequest) -> None:
        """Check response status and raise appropriate exceptions."""
        reply = blocking_request.reply()
        if not reply:
            raise Exception("No response received. Check provider settings and availability.")

        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        message = reply.content().data().decode()

        if not status_code:
            raise Exception(f"No status code received. Check provider settings.")

        if status_code == 403:
            raise exceptions.InvalidKey(str(status_code), message)
        elif status_code == 429:
            raise exceptions.OverQueryLimit(str(status_code), message)
        elif 400 <= status_code < 500:
            raise exceptions.ApiError(str(status_code), message)
        elif status_code != 200:
            raise exceptions.GenericServerError(str(status_code), message)

    def _generate_auth_url(self, path: str, params: Union[Dict, List]) -> str:
        if isinstance(params, dict):
            params = sorted(dict(**params).items())
        return path + "?" + unquote_unreserved(urlencode(params))