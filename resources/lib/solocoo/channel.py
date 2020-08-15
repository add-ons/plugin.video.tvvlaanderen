# -*- coding: utf-8 -*-
""" Solocoo Channel API """

from __future__ import absolute_import, division, unicode_literals

import json
import logging

from resources.lib.solocoo import SOLOCOO_API, util
from resources.lib.solocoo.util import find_image, check_deals_entitlement

_LOGGER = logging.getLogger(__name__)


class Channel:
    """ Channel Object """

    def __init__(self, uid, title, icon, preview, number, radio=False):
        self.uid = uid
        self.title = title
        self.icon = icon
        self.preview = preview
        self.number = number
        self.radio = radio

    def __repr__(self):
        return "%r" % self.__dict__


class StreamInfo:
    """ Stream information """

    def __init__(self, url, protocol, drm_protocol, drm_license_url, drm_certificate):
        self.url = url
        self.protocol = protocol
        self.drm_protocol = drm_protocol
        self.drm_license_url = drm_license_url
        self.drm_certificate = drm_certificate

    def __repr__(self):
        return "%r" % self.__dict__


class ChannelApi:
    """ Solocoo Channel API """

    def __init__(self, auth):
        """ Initialisation of the class.

        :param resources.lib.solocoo.auth.AuthApi auth: The Authentication object
        """
        self._auth = auth
        self._tokens = self._auth.login()

    def get_channels(self):
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
            self._parse_channel(channel.get('assetInfo', {}), entitlements.get('offers', []))
            for channel in data.get('channels', [])
        ]

        # Return only available channels
        return [channel for channel in channels if channel is not None]

    def get_channel(self, channel_id):
        """ Get channel information for the requested Channel.

        :param str channel_id:          The ID of the channel

        :returns: The requested channel.
        :rtype: Channel
        """
        _LOGGER.debug('Requesting channel %s', channel_id)
        reply = util.http_get(SOLOCOO_API + '/assets/{channel_id}'.format(channel_id=channel_id),
                              token_bearer=self._tokens.jwt_token)
        data = json.loads(reply.text)

        return self._parse_channel(data)

    def get_stream(self, channel_id):
        """ Get stream information for the requested Channel.

        :param str channel_id:          The ID of the channel

        :returns: Information on how to play this channel.
        :rtype: StreamInfo
        """
        _LOGGER.debug('Requesting stream info for channel %s', channel_id)
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
        data = json.loads(reply.text)

        stream = StreamInfo(
            url=data.get('url'),
            protocol=data.get('mediaType'),
            drm_protocol=data.get('drm', {}).get('system'),
            drm_license_url=data.get('drm', {}).get('licenseUrl'),
            drm_certificate=data.get('drm', {}).get('cert'),
        )

        return stream

    @staticmethod
    def _parse_channel(channel, offers=None):
        """ Parse the API result of a channel into a Channel object.

        :param dict channel:            The channel info from the API.
        :param List[str] offers:        A list of offers that we have.

        :returns: A channel that is parsed.
        :rtype: Channel
        """
        deals = channel.get('deals', [])
        if not deals:
            # No deal
            return None

        if offers and not check_deals_entitlement(deals, offers):
            # We have no entitlement for this channel
            return None

        return Channel(
            uid=channel.get('id'),
            title=channel.get('title'),
            icon=find_image(channel.get('images'), 'la'),
            preview=find_image(channel.get('images'), 'lv'),
            number=channel.get('params', {}).get('lcn'),
            radio=channel.get('params', {}).get('radio', False),
        )
