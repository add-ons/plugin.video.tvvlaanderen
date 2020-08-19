# -*- coding: utf-8 -*-
""" Channels module """

from __future__ import absolute_import, division, unicode_literals

import logging

from resources.lib import kodiutils
from resources.lib.modules.menu import Menu
from resources.lib.solocoo.auth import AuthApi
from resources.lib.solocoo.channel import ChannelApi

_LOGGER = logging.getLogger(__name__)


class Channels:
    """ Menu code related to channels """

    def __init__(self):
        """ Initialise object """
        auth = AuthApi(username=kodiutils.get_setting('username'),
                       password=kodiutils.get_setting('password'),
                       tenant=kodiutils.get_setting('tenant'),
                       token_path=kodiutils.get_tokens_path())
        self._channel_api = ChannelApi(auth)

    def show_channels(self):
        """ Shows TV channels """
        channels = self._channel_api.get_channels()

        listing = [Menu.generate_titleitem(channel) for channel in channels]
        kodiutils.show_listing(listing, 30007)
