# -*- coding: utf-8 -*-
""" Tests for Auth API """

# pylint: disable=missing-docstring,no-self-use

from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import unittest

from resources.lib import kodiutils
from resources.lib.solocoo.auth import AuthApi, AccountStorage

_LOGGER = logging.getLogger(__name__)


class TestAuth(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestAuth, self).__init__(*args, **kwargs)

        self._auth = AuthApi(kodiutils.get_setting('username'), kodiutils.get_setting('password'), 'tvv', kodiutils.get_tokens_path())

    def test_login(self):
        account = self._auth.login()
        self.assertIsInstance(account, AccountStorage)

    def test_list_devices(self):
        devices = self._auth.list_devices()
        self.assertIsInstance(devices, dict)

    def test_list_entitlements(self):
        entitlements = self._auth.list_entitlements()
        self.assertIsInstance(entitlements, dict)


if __name__ == '__main__':
    unittest.main()
