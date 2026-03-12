"""
session.py
----------
Manages the Redfish HTTP session for iLO API communication.
Builds a single shared session used by all other modules.
"""

import urllib3
import requests

from config import DEFAULT_HEADERS, DATETIME_PATH, RESET_PATH, NIC_PATH

# Suppress SSL warnings — iLO uses self-signed certificates by default.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class IloSession:
    """
    Holds the active Redfish session and all computed URLs for one iLO target.
    One instance is created per script run and passed to all other modules.
    """

    def __init__(self, ip, username, password):
        self.base_url     = "https://{}".format(ip)
        self.datetime_url = "{}{}".format(self.base_url, DATETIME_PATH)
        self.reset_url    = "{}{}".format(self.base_url, RESET_PATH)
        self.nic_url      = "{}{}".format(self.base_url, NIC_PATH)

        self.session         = requests.Session()
        self.session.auth    = (username, password)
        self.session.headers.update(DEFAULT_HEADERS)
        self.session.verify  = False   # iLO uses self-signed certs

    def get(self, url, **kwargs):
        """Delegate GET to the underlying requests Session."""
        return self.session.get(url, **kwargs)

    def patch(self, url, **kwargs):
        """Delegate PATCH to the underlying requests Session."""
        return self.session.patch(url, **kwargs)

    def post(self, url, **kwargs):
        """Delegate POST to the underlying requests Session."""
        return self.session.post(url, **kwargs)
