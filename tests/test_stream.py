# -*- coding: utf-8 -*-
""" Tests for Channel API """

# pylint: disable=missing-docstring,no-self-use

from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import unittest

import xbmc

from resources.lib import kodiutils
from resources.lib.modules.player import Player
from resources.lib.solocoo import Channel
from resources.lib.solocoo.auth import AuthApi
from resources.lib.solocoo.asset import AssetApi

_LOGGER = logging.getLogger(__name__)


@unittest.skipUnless(kodiutils.get_setting('username') and kodiutils.get_setting('password'), 'Skipping since we have no credentials.')
class TestStream(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestStream, self).__init__(*args, **kwargs)

        self._auth = AuthApi(kodiutils.get_setting('username'),
                             kodiutils.get_setting('password'),
                             kodiutils.get_setting('tenant'),
                             kodiutils.get_tokens_path())

    def tearDown(self):
        xbmc.Player().stop()

    def test_play_live(self):
        api = AssetApi(self._auth)

        channels = api.get_channels()
        self.assertIsInstance(channels[0], Channel)

        player = Player()
        player.play_asset(channels[0].uid)


if __name__ == '__main__':
    unittest.main()
