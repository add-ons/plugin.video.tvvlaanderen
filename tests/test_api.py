# -*- coding: utf-8 -*-
""" Tests for Channel API """

# pylint: disable=missing-docstring,no-self-use

from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import unittest

from resources.lib import kodiutils
from resources.lib.solocoo import Channel, StreamInfo, Epg, EpgSeries
from resources.lib.solocoo.asset import AssetApi
from resources.lib.solocoo.auth import AuthApi
from resources.lib.solocoo.exceptions import NotAvailableInOfferException

_LOGGER = logging.getLogger(__name__)


@unittest.skipUnless(kodiutils.get_setting('username') and kodiutils.get_setting('password'), 'Skipping since we have no credentials.')
class TestChannel(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestChannel, self).__init__(*args, **kwargs)

        self._auth = AuthApi(kodiutils.get_setting('username'),
                             kodiutils.get_setting('password'),
                             kodiutils.get_setting('tenant'),
                             kodiutils.get_tokens_path())
        self._api = AssetApi(self._auth)

    def test_get_channels(self):
        channels = self._api.get_channels()
        self.assertIsInstance(channels, list)
        self.assertIsInstance(channels[0], Channel)
        self.assertIsNotNone(channels[0].uid)
        self.assertIsNotNone(channels[0].station_id)

    def test_get_channel(self):
        channel_id = 'V6sXTJf1I6krfS3MRe0Dd5UGqFczlxHlZ86MLQ_R'  # VTM

        channel = self._api.get_asset(channel_id)
        self.assertIsInstance(channel, Channel)

    def test_get_channel_stream(self):
        channel_id = 'V6sXTJf1I6krfS3MRe0Dd5UGqFczlxHlZ86MLQ_R'  # VTM

        stream_info = self._api.get_stream(channel_id)
        self.assertIsInstance(stream_info, StreamInfo)

    def test_get_channel_without_package(self):
        channel_id = 'c2Zizb4y-j0jSz1je7joROr5YbwFwCVZpjVkTHAo'  # Love Nature HD

        channel = self._api.get_asset(channel_id)
        self.assertIsInstance(channel, Channel)

        with self.assertRaises(NotAvailableInOfferException):
            self._api.get_stream(channel_id)

    def test_get_replay(self):
        channel_id = 'JIY-fyHDkM1Rk260f-WNXlVD8iYnlDtWOQ4ah0hb'  # één

        programs = self._api.get_replay(channel_id)
        self.assertIsInstance(programs, list)

        # Find a serie
        series_id = next((program.uid for program in programs if isinstance(program, EpgSeries)))
        programs = self._api.get_replay_series(series_id)
        self.assertIsInstance(programs, list)
        self.assertIsInstance(programs[0], Epg)


if __name__ == '__main__':
    unittest.main()
