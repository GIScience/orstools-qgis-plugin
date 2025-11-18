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
from datetime import datetime, timedelta
from typing import Union, Dict, List, Optional
from urllib.parse import urlencode


from qgis.PyQt.QtCore import QObject, pyqtSignal, QUrl, QTimer, QEventLoop
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkReply
from qgis.core import QgsSettings, QgsBlockingNetworkRequest
from requests.utils import unquote_unreserved

from ORStools import __version__
from ORStools.utils import exceptions, configmanager, logger

_USER_AGENT = f"ORSQGISClient@v{__version__}"


class Client(QObject):
    """Performs requests to the ORS API services.

    This class handles HTTP communication with the openrouteservice API,
    including authentication, retry logic for rate limiting, and progress
    tracking.

    Signals:
        overQueryLimit: Emitted when rate limit is hit, passes delay in seconds
        downloadProgress: Emitted during download, passes progress ratio (0-1)
    """

    overQueryLimit = pyqtSignal(int)
    downloadProgress = pyqtSignal(int)

    def __init__(self, provider: Optional[dict] = None, agent: Optional[str] = None) -> None:
        """Initialize the ORS API client.

        :param provider: Provider configuration containing base_url, key, timeout, and ENV_VARS
        :type provider: dict
        :param agent: User agent string for the HTTP requests
        :type agent: str
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

    def _request(
        self,
        post_json: Optional[dict],
        blocking_request: QgsBlockingNetworkRequest,
        request: QNetworkRequest,
    ) -> str:
        """Execute a blocking network request.

        :param post_json: JSON payload for POST requests, None for GET requests
        :type post_json: dict or None
        :param blocking_request: QGIS blocking network request handler
        :type blocking_request: QgsBlockingNetworkRequest
        :param request: Network request with URL and headers
        :type request: QNetworkRequest
        :return: Network reply content
        :rtype: QgsNetworkReplyContent
        :raises: Various ApiError exceptions based on HTTP status codes
        """
        if post_json is not None:
            result = blocking_request.post(request, json.dumps(post_json).encode())
        else:
            result = blocking_request.get(request)

        if result != QgsBlockingNetworkRequest.NoError:
            self._check_status(blocking_request.reply())
            return None

        return blocking_request.reply()

    def fetch_with_retry(
        self,
        url: str,
        params: dict,
        first_request_time: Optional[datetime] = None,
        post_json: Optional[dict] = None,
        max_retries: int = 100,
    ):
        """Fetch data from the API with automatic retry on rate limit errors.

        Implements exponential backoff with jitter for retries. The first retry
        occurs after exactly 61 seconds, subsequent retries use exponential
        backoff capped at 5 minutes.

        :param url: API endpoint path (e.g., "/v2/directions/driving-car/geojson")
        :type url: str
        :param params: URL query parameters
        :type params: dict
        :param first_request_time: Timestamp of the first request attempt
        :type first_request_time: datetime or None
        :param post_json: JSON payload for POST requests
        :type post_json: dict or None
        :param max_retries: Maximum number of retry attempts
        :type max_retries: int
        :return: Parsed JSON response from the API
        :rtype: dict
        :raises exceptions.Timeout: When total retry time exceeds configured timeout
        :raises exceptions.ApiError: On non-retryable API errors (4xx except 429)
        """
        first_request_time = datetime.now()

        authed_url = self._generate_auth_url(url, params)
        self.url = self.base_url + authed_url

        request = QNetworkRequest(QUrl(self.url))

        for header, value in self.headers.items():
            request.setRawHeader(header.encode(), value.encode())

        blocking_request = QgsBlockingNetworkRequest()

        blocking_request.downloadProgress.connect(lambda r, t: self.downloadProgress.emit(r / t))

        logger.log(f"url: {self.url}\nParameters: {json.dumps(post_json, indent=2)}", 0)

        content = None

        for i in range(max_retries):
            try:
                reply = self._request(post_json, blocking_request, request)
                content = reply.content().data().decode()
                break

            except exceptions.OverQueryLimit as e:
                if datetime.now() - first_request_time > timedelta(seconds=self.timeout):
                    raise exceptions.Timeout()

                logger.log(f"{e.__class__.__name__}: {str(e)}", 1)

                delay_seconds = self.get_delay_seconds(i)
                self.overQueryLimit.emit(delay_seconds)


                loop = QEventLoop()
                QTimer.singleShot(delay_seconds * 1000, loop.quit)
                loop.exec()

            except exceptions.ApiError as e:
                if post_json:
                    logger.log(
                        f"Feature ID {post_json['id']} caused a {e.__class__.__name__}: {str(e)}", 2
                    )
                raise

        # Write env variables if successful
        if self.ENV_VARS:
            for env_var in self.ENV_VARS:
                header_value = reply.rawHeader(self.ENV_VARS[env_var].encode()).data().decode()
                configmanager.write_env_var(env_var, header_value)

        # Reset to old value
        self.settings.setValue("qgis/networkAndProxy/userAgent", self.user_agent)

        return json.loads(content)

    def get_delay_seconds(self, retry_counter: int) -> int:
        """Calculate delay before next retry attempt.

        First retry waits exactly 61 seconds. Subsequent retries use exponential
        backoff with base delay of 60s * 1.5^(retry_counter-1), capped at 300s,
        with random jitter between 30-60% of the calculated delay.

        :param retry_counter: Zero-based retry attempt number
        :type retry_counter: int
        :return: Delay in seconds before next retry
        :rtype: int
        """
        if retry_counter == 0:
            delay_seconds = 61
        else:
            base_delay = min(60 * (1.5 ** (retry_counter - 1)), 300)
            jitter = random.uniform(0.3, 0.6)
            delay_seconds = base_delay * jitter

        logger.log(f"Retry Counter: {retry_counter}, Delay: {delay_seconds:.2f}s", 1)
        return int(delay_seconds)

    def _check_status(self, reply: QNetworkReply) -> None:
        """Check HTTP response status and raise appropriate exceptions.

        :param reply: Network reply to check
        :type reply: QNetworkReply
        :raises exceptions.InvalidKey: On 403 Forbidden (invalid API key)
        :raises exceptions.OverQueryLimit: On 429 Too Many Requests
        :raises exceptions.ApiError: On 4xx client errors
        :raises exceptions.GenericServerError: On 5xx server errors
        :raises Exception: On network errors or invalid responses
        """
        status_code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        message = reply.content().data().decode()

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
        """Generate authenticated URL with query parameters.

        :param path: API endpoint path
        :type path: str
        :param params: Query parameters as dict or list of tuples
        :type params: dict or list
        :return: URL path with encoded query string
        :rtype: str
        """
        if isinstance(params, dict):
            params = sorted(dict(**params).items())

        # Only auto-add API key when using ORS. If own instance, API key must
        # be explicitly added to params
        # if self.key:
        #     params.append(("api_key", self.key))

        return path + "?" + unquote_unreserved(urlencode(params))
