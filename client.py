#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 17 13:51:13 2018

@author: nilsnolde
"""


from datetime import datetime, timedelta
import requests
import random
import time
import collections
from urllib.parse import urlencode

import json
from PyQt5.QtCore import QUrl, QEventLoop, QSettings
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkProxy
from qgis.core import QgsNetworkAccessManager

import OSMtools
from . import exceptions, auxiliary

_USER_AGENT = "ORSClientQGIS/{}".format(OSMtools.__version__)
_RETRIABLE_STATUSES = [503]
_DEFAULT_BASE_URL = "https://api.openrouteservice.org"

class Client(object):
    """Performs requests to the ORS API services."""

    def __init__(self, iface,
                 retry_timeout=60, 
                 requests_kwargs=None,
                 retry_over_query_limit=False):
        """
        :param key: ORS API key. Required.
        :type key: string
        
        :param iface: A QGIS interface instance.
        :type iface: QgisInterface

        :param retry_timeout: Timeout across multiple retriable requests, in
            seconds.
        :type retry_timeout: int

        :param requests_kwargs: Extra keyword arguments for the requests
            library, which among other things allow for proxy auth to be
            implemented. See the official requests docs for more info:
            http://docs.python-requests.org/en/latest/api/#main-interface
        :type requests_kwargs: dict
        """
        
        base_params = auxiliary.readConfig()
        
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

        Error Values Explanation (for developers, appropriate error message will be printed to console for user):
        :raise 1: the remote server refused the connection (the server is not accepting requests)
        :raise 2: the remote server closed the connection prematurely, before the entire reply was received and
        processed
        :raise 3: the remote host name was not found (invalid hostname)
        :raise 4: the connection to the remote server timed out
        :raise 5: the operation was canceled via calls to abort() or close() before it was finished.
        :raise 6: the SSL/TLS handshake failed and the encrypted channel could not be established. The sslErrors()
        signal should have been emitted.
        :raise 7: the connection was broken due to disconnection from the network, however the system has initiated
        roaming to another access point. The request should be resubmitted and will be processed as soon as the
        connection is re-established.
        :raise 101: the connection to the proxy server was refused (the proxy server is not accepting requests)
        :raise 102: the proxy server closed the connection prematurely, before the entire reply was received and
        processed
        :raise 103: the proxy host name was not found (invalid proxy hostname)
        :raise 104: the connection to the proxy timed out or the proxy did not reply in time to the request sent
        :raise 105: the proxy requires authentication in order to honour the request but did not accept any credentials
        offered (if any)
        :raise 201: the access to the remote content was denied (similar to HTTP error 401)
        :raise 202: the operation requested on the remote content is not permitted
        :raise 203: the remote content was not found at the server (similar to HTTP error 404)
        :raise 204: the remote server requires authentication to serve the content but the credentials provided were not
        accepted (if any)
        :raise 205: the request needed to be sent again, but this failed for example because the upload data could not
        be read a second time.
        :raise 301: the Network Access API cannot honor the request because the protocol is not known
        :raise 302: the requested operation is invalid for this protocol
        :raise 99: an unknown network-related error was detected
        :raise 199: an unknown proxy-related error was detected
        :raise 299: an unknown error related to the remote content was detected
        :raise 399: a breakdown in protocol was detected (parsing error, invalid or unexpected responses, etc.)

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
        
        print(self.base_url + authed_url)

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

        # init qgis network manager
        network_manager = QgsNetworkAccessManager.instance()

        # retrieve proxy setting from qgis and configurate proxy
        qgis_settings = QSettings()

        proxyEnabled = qgis_settings.value("proxy/proxyEnabled", "")
        proxyType = qgis_settings.value("proxy/proxyType", "")
        proxyHost = qgis_settings.value("proxy/proxyHost", "")
        proxyPort = qgis_settings.value("proxy/proxyPort", "")
        proxyUser = qgis_settings.value("proxy/proxyUser", "")
        proxyPassword = qgis_settings.value("proxy/proxyPassword", "")

        if proxyEnabled == "true":
            proxy = QNetworkProxy()

            if proxyType == "DefaultProxy":
                proxy.setType(QNetworkProxy.DefaultProxy)
            elif proxyType == "Socks5Proxy":
                proxy.setType(QNetworkProxy.Socks5Proxy)
            elif proxyType == "HttpProxy":
                proxy.setType(QNetworkProxy.HttpProxy)
            elif proxyType == "HttpCachingProxy":
                proxy.setType(QNetworkProxy.HttpCachingProxy)
            elif proxyType == "FtpCachingProxy":
                proxy.setType(QNetworkProxy.FtpCachingProxy)

            proxy.setHostName(proxyHost)
            proxy.setPort(int(proxyPort))
            proxy.setUser(proxyUser)
            proxy.setPassword(proxyPassword)

            QNetworkProxy.setApplicationProxy(proxy)

            network_manager.setupDefaultProxyAndCache()
            network_manager.setProxy(proxy)

        # request
        request = QNetworkRequest(QUrl(self.base_url + authed_url))
        for key, value in final_requests_kwargs['headers'].items():
            request.setRawHeader(bytes(key, 'utf-8'), bytes(value, 'utf-8'))

        if post_json is not None:
            request.setRawHeader("json", post_json)
            response = network_manager.post(request)
        else:
            response = network_manager.get(request)

        # wait for response
        loop = QEventLoop()
        network_manager.finished.connect(loop.exit)
        loop.exec()

        # check for errors and print error messages
        error = response.error()

        if error == QNetworkReply.NoError:
            result = json.loads(str(response.readAll(), 'utf-8'))  # str(bytes_string, 'utf-8')
            self.sent_times.append(time.time())
            return result
        else:
            print("Error occured: ", error)
            print(response.errorString())
            print("Current Proxy Settings are:")
            print("Use Proxy:", proxyEnabled)
            print("Proxy Type:", proxyType)
            print("Proxy Host:", proxyHost)
            print("Proxy Port:", proxyPort)
            print("Proxy User:", proxyUser)
            print("Proxy Password:", proxyPassword)



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
                         "Visit https://go.openrouteservice.org/dev-dashboard/ "
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