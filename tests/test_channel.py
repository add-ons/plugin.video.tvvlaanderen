# -*- coding: utf-8 -*-
""" Tests for Channel API """

# pylint: disable=missing-docstring,no-self-use

from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import unittest

from resources.lib import kodiutils
from resources.lib.solocoo.auth import AuthApi
from resources.lib.solocoo.channel import ChannelApi, Channel, StreamInfo
from resources.lib.solocoo.exceptions import NotAvailableInOfferException

_LOGGER = logging.getLogger(__name__)


class TestChannel(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestChannel, self).__init__(*args, **kwargs)

        self._auth = AuthApi(kodiutils.get_setting('username'), kodiutils.get_setting('password'), 'tvv',
                             kodiutils.get_tokens_path())

    def test_get_channels(self):
        api = ChannelApi(self._auth)

        channels = api.get_channels()
        self.assertIsInstance(channels, list)
        self.assertIsInstance(channels[0], Channel)

        print(channels)

    def test_get_channel(self):
        api = ChannelApi(self._auth)

        channel_id = 'V6sXTJf1I6krfS3MRe0Dd5UGqFczlxHlZ86MLQ_R'  # VTM

        channel = api.get_channel(channel_id)
        self.assertIsInstance(channel, Channel)
        print(channel)

        stream_info = api.get_stream(channel_id)
        self.assertIsInstance(stream_info, StreamInfo)
        print(stream_info)

    def test_get_channel_without_package(self):
        api = ChannelApi(self._auth)

        channel_id = 'c2Zizb4y-j0jSz1je7joROr5YbwFwCVZpjVkTHAo'  # Love Nature HD

        channel = api.get_channel(channel_id)
        self.assertIsInstance(channel, Channel)

        with self.assertRaises(NotAvailableInOfferException):
            api.get_stream(channel_id)


if __name__ == '__main__':
    unittest.main()
