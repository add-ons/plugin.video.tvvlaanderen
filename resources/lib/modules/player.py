# -*- coding: utf-8 -*-
""" Player module """

from __future__ import absolute_import, division, unicode_literals

import logging

from resources.lib import kodiutils
from resources.lib.solocoo.auth import AuthApi
from resources.lib.solocoo.channel import ChannelApi
from resources.lib.solocoo.exceptions import NotAvailableInOfferException

_LOGGER = logging.getLogger(__name__)


class Player:
    """ Code responsible for playing media """

    def __init__(self):
        """ Initialise object """
        # TODO: hardcoded tvv
        auth = AuthApi(username=kodiutils.get_setting('username'),
                       password=kodiutils.get_setting('password'),
                       tenant='tvv',
                       token_path=kodiutils.get_tokens_path())
        self._channel_api = ChannelApi(auth)

    def channel(self, channel_id):
        """ Play the live channel.

        :param string channel_id:       The ID of the channel to play.
        """
        # channel_info = self._api.get_channel(channel_id)
        # TODO: use channel_info to add extra information to the listitem to play

        try:
            stream_info = self._channel_api.get_stream(channel_id)
        except NotAvailableInOfferException as exc:
            # TODO: show nice error dialog
            _LOGGER.error(exc)
            return

        license_key = self._create_license_key(stream_info.drm_license_url)

        _LOGGER.debug('Starting playing %s with license key %s', stream_info.url, license_key)
        kodiutils.play(stream_info.url, license_key)

    @staticmethod
    def _create_license_key(key_url, key_type='R', key_headers=None, key_value=None):
        """ Create a license key string that we need for inputstream.adaptive.

        :param str key_url:
        :param str key_type:
        :param dict[str, str] key_headers:
        :param str key_value:

        :returns:   A license key string that can be passed to inputstream.adaptive.
        :rtype: str
        """
        try:  # Python 3
            from urllib.parse import urlencode, quote
        except ImportError:  # Python 2
            from urllib import urlencode, quote

        header = ''
        if key_headers:
            header = urlencode(key_headers)

        if key_type in ('A', 'R', 'B'):
            key_value = key_type + '{SSM}'
        elif key_type == 'D':
            if 'D{SSM}' not in key_value:
                raise ValueError('Missing D{SSM} placeholder')
            key_value = quote(key_value)

        return '%s|%s|%s|' % (key_url, header, key_value)
