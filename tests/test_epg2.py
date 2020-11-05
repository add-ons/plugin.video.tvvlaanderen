# -*- coding: utf-8 -*-
""" Tests for EPG API """

# pylint: disable=missing-docstring,no-self-use

from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import unittest

from resources.lib import kodiutils
from resources.lib.solocoo.auth import AuthApi
from resources.lib.solocoo.epg2 import Epg2Api
from resources.lib.solocoo.util import Program, Channel

_LOGGER = logging.getLogger(__name__)


class TestEpg(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestEpg, self).__init__(*args, **kwargs)

        self._auth = AuthApi(kodiutils.get_setting('username'),
                             kodiutils.get_setting('password'),
                             kodiutils.get_setting('tenant'),
                             kodiutils.get_tokens_path())

    def test_get_channels(self):
        api = Epg2Api(self._auth)

        channels = api.get_channels()
        self.assertIsInstance(channels, list)
        self.assertIsInstance(channels[0], Channel)

    def test_get_guide(self):
        api = Epg2Api(self._auth)

        channels = [
            '1790975744',  # één
            '1790975808',  # Canvas
        ]
        channels = api.get_guide(channels)
        self.assertIsInstance(channels, dict)

    def test_get_program(self):
        api = Epg2Api(self._auth)

        program = api.get_program('asAfBG-twA9ih-SQAnqQRUvgnPdHyv4P')
        self.assertIsInstance(program, Program)


if __name__ == '__main__':
    unittest.main()
