# -*- coding: utf-8 -*-
""" Solocoo Channel API """

from __future__ import absolute_import, division, unicode_literals

import json
import logging

from requests import HTTPError

from resources.lib.solocoo import SOLOCOO_API, util
from resources.lib.solocoo.exceptions import NotAvailableInOfferException
from resources.lib.solocoo.util import parse_channel, StreamInfo

_LOGGER = logging.getLogger(__name__)


class ChannelApi:
    """ Solocoo Channel API """

    def __init__(self, auth):
        """ Initialisation of the class.

        :param resources.lib.solocoo.auth.AuthApi auth: The Authentication object
        """
        self._auth = auth
        self._tokens = self._auth.login()

    def get_channels(self, include_epg=False):
        """ Get all channels.

        :returns: A list of all channels.
        :rtype: List[Channel]
        """
        _LOGGER.debug('Requesting entitlements')
        entitlements = self._auth.list_entitlements()

        _LOGGER.debug('Requesting channel listing')
        reply = util.http_get(SOLOCOO_API + '/bouquet', token_bearer=self._tokens.jwt_token)
        data = json.loads(reply.text)

        # Parse list to Channel objects
        channels = [
            parse_channel(channel.get('assetInfo', {}), entitlements.get('offers', []))
            for channel in data.get('channels', [])
        ]

        # Filter only available channels
        channels = [channel for channel in channels if channel is not None]

        # Load the channel directly in case we also want to have the EPG
        if include_epg:
            channels = [self.get_channel(channel.uid) for channel in channels]

        return channels

    def get_channel(self, channel_id):
        """ Get channel information for the requested Channel.

        :param str channel_id:          The ID of the channel

        :returns: The requested channel.
        :rtype: resources.lib.solocoo.util.Channel
        """
        _LOGGER.debug('Requesting channel %s', channel_id)
        reply = util.http_get(SOLOCOO_API + '/assets/{channel_id}'.format(channel_id=channel_id),
                              token_bearer=self._tokens.jwt_token)
        data = json.loads(reply.text)

        return parse_channel(data)

    def get_stream(self, channel_id):
        """ Get stream information for the requested Channel.

        :param str channel_id:          The ID of the channel

        :returns: Information on how to play this channel.
        :rtype: StreamInfo
        """
        _LOGGER.debug('Requesting stream info for channel %s', channel_id)
        try:
            reply = util.http_post(
                SOLOCOO_API + '/assets/{channel_id}/play'.format(channel_id=channel_id),
                token_bearer=self._tokens.jwt_token,
                data={
                    "player": {
                        "name": "Bitmovin",
                        "version": "8.22.0",
                        "capabilities": {
                            "mediaTypes": ["DASH"],  # ["DASH", "HLS", "MSSS", "Unspecified"]
                            "drmSystems": ["Widevine"]
                        },
                        "drmSystems": ["Widevine"]
                    }
                }
            )
        except HTTPError as ex:
            if ex.response.status_code == 402:
                raise NotAvailableInOfferException
            raise

        data = json.loads(reply.text)

        stream = StreamInfo(
            url=data.get('url'),
            protocol=data.get('mediaType'),
            drm_protocol=data.get('drm', {}).get('system'),
            drm_license_url=data.get('drm', {}).get('licenseUrl'),
            drm_certificate=data.get('drm', {}).get('cert'),
        )

        return stream
