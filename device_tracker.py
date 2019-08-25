"""
Support for TP-Link routers.

For more details about this platform, please refer to the documentation at
[url]https://home-assistant.io/components/device_tracker.tplink/[/url]
"""
import base64
from datetime import datetime
import hashlib
import logging
import re
import json

from aiohttp.hdrs import (
    ACCEPT, COOKIE, PRAGMA, REFERER, CONNECTION, KEEP_ALIVE, USER_AGENT,
    CONTENT_TYPE, CACHE_CONTROL, ACCEPT_ENCODING, ACCEPT_LANGUAGE)
import requests
import voluptuous as vol

from homeassistant.components.device_tracker import (
    DOMAIN, PLATFORM_SCHEMA, DeviceScanner)
from homeassistant.const import (
    CONF_HOST, CONF_PASSWORD, CONF_USERNAME, HTTP_HEADER_X_REQUESTED_WITH)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

HTTP_HEADER_NO_CACHE = 'no-cache'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required(CONF_USERNAME): cv.string
})


def get_scanner(hass, config):
    """Validate the configuration and return a TP-Link scanner."""
    scanner = TplinkDeviceScanner(config[DOMAIN])
    if scanner.success_init:
        return scanner

    return None


class TplinkDeviceScanner(DeviceScanner):
    """This class queries the WDR6500 router."""

    def __init__(self, config):
        """Initialize the scanner."""
        host = config[CONF_HOST]
        username, password = config[CONF_USERNAME], config[CONF_PASSWORD]
        self.host = host
        self.username = username
        self.password = password
        self.stok = ''
        self.success_init = self._update_info()

    def scan_devices(self):
        """Scan for new devices and return a list with found device IDs."""
        self._update_info()
        return self.last_results

    # pylint: disable=no-self-use
    def get_device_name(self, device):
        """Get the firmware doesn't save the name of the wireless device."""
        return None

    def _get_auth_tokens(self):
        """Retrieve auth tokens from the router."""
        _LOGGER.info("Retrieving tp-link auth tokens...")

        url_login = 'http://{}/'.format(self.host)
        Y_passwd = '{}'.format(self.password)
        En_passwd = Encrypt(passwd=Y_passwd).encrypt_passwd()
        post_data = {'login': {'password': En_passwd}, 'method': 'do'}
        get_Text = requests.post(url=url_login, json=post_data).text
        get_data = json.loads(get_Text)

        if 'stok' not in get_data.keys():
            _LOGGER.error("路由器登陆失败，很肯能密码错误")
        else:
            self.stok = get_data['stok']

    def _update_info(self):
        """Ensure the information from the TP-Link router is up to date.
            Return boolean if scanning successful.
        """
        if (self.stok == ''):
            self._get_auth_tokens()

        result = []
        _LOGGER.info("Loading wireless clients...")
        online_host = {"hosts_info": {"table": "online_host"}, "method": "get"}
        url_info = ('http://{}/stok={}/ds').format(self.host, self.stok)
        host_json = requests.post(url=url_info, json=online_host).json()
        try:
            if host_json.get('error_code') == 0:
                info = host_json['hosts_info']['online_host']
                for i in list(range(len(info))):
                    result.append(list(info[i].values())[0]['mac'])
                if result:
                    self.last_results = [mac.replace("-", ":") for mac in result]
                    return True
            else:
                if host_json.get('error_code') == 'timeout':
                    # auth_tokens已过期，需要重新登陆
                    _LOGGER.info("Token timed out. Relogging on next scan")
                    self.stok = ''
                else:
                    _LOGGER.error("An unknown error happened while fetching data with error_code: " +
                                  host_json.get('error_code'))

        except ValueError:
            _LOGGER.error("Router didn't respond with JSON. Check if credentials are correct")

        return False

    def _log_out(self):
        _LOGGER.info("Logging out of router admin interface...")

        log_option = {"system": {"logout": "null"}, "method": "do"}
        url_logout = ('http://{}/stok={}/ds').format(self.host, self.stok)
        logOut_code = requests.post(url=url_logout, json=log_option).json()
        if logOut_code['error_code'] == 0:
            self.stok = ''


class Encrypt:
    def __init__(self, passwd=None, flat=1):
        self.passwd = passwd
        self.Flat = flat

    def encrypt_passwd(self):
        a = "RDpbLfCPsJZ7fiv"
        c = 'yLwVl0zKqws7LgKPRQ84Mdt708T1qQ3Ha7xv3H7NyU84p21BriUWBU43odz3iP4rBL3cD02KZciXTysVXiV8ngg6vL48rPJyAUw0HurW20xqxv9aYb4M9wK1Ae0wlro510qXeU07kV57fQMc8L6aLgMLwygtc0F10a0Dg70TOoouyFhdysuRMO51yY5ZlOZZLEal1h0t9YQW0Ko7oBwmCAHoic4HYbUyVeU3sfQ1xtXcPcf1aT303wAQhv66qzW'
        b = self.passwd
        e = ''
        f, g, h, k, l = 187, 187, 187, 187, 187
        n = 187
        g = len(a)
        h = len(b)
        k = len(c)
        if g > h:
            f = g
        else:
            f = h
        for p in list(range(0, f)):
            n = l = 187
            if p >= g:
                n = ord(b[p])
            else:
                if p >= h:
                    l = ord(a[p])
                else:
                    l = ord(a[p])
                    n = ord(b[p])
            e += c[(l ^ n) % k]

        return e
