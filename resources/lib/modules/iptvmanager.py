# -*- coding: utf-8 -*-
""" Implementation of IPTVManager class """

from __future__ import absolute_import, division, unicode_literals

import logging
from collections import defaultdict

from resources.lib import kodiutils
from resources.lib.solocoo.auth import AuthApi
from resources.lib.solocoo.channel import ChannelApi
from resources.lib.solocoo.epg import EpgApi

_LOGGER = logging.getLogger(__name__)


class IPTVManager:
    """ Interface to IPTV Manager """

    def __init__(self, port):
        """ Initialize IPTV Manager object. """
        self.port = port

        self._auth = AuthApi(username=kodiutils.get_setting('username'),
                             password=kodiutils.get_setting('password'),
                             tenant=kodiutils.get_setting('tenant'),
                             token_path=kodiutils.get_tokens_path())

    def via_socket(func):  # pylint: disable=no-self-argument
        """ Send the output of the wrapped function to socket. """

        def send(self):
            """ Decorator to send data over a socket. """
            import json
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', self.port))
            try:
                sock.sendall(json.dumps(func(self)).encode())  # pylint: disable=not-callable
            finally:
                sock.close()

        return send

    @via_socket
    def send_channels(self):
        """ Return JSON-STREAMS formatted information to IPTV Manager. """
        channel_api = ChannelApi(self._auth)

        streams = []

        channels = channel_api.get_channels()
        for channel in channels:
            streams.append(dict(
                name=channel.title,
                stream=kodiutils.url_for('play_asset', asset_id=channel.uid),
                id=channel.uid,
                logo=channel.icon,
                preset=channel.number,
            ))

        return dict(version=1, streams=streams)

    @via_socket
    def send_epg(self):
        """ Return JSON-EPG formatted information to IPTV Manager. """
        channel_api = ChannelApi(self._auth)
        epg_api = EpgApi(self._auth)

        epg = defaultdict(list)

        # Load EPG data
        channels = channel_api.get_channels()
        for date in ['yesterday', 'today', 'tomorrow']:
            for channel, programs in epg_api.get_guide([channel.uid for channel in channels], date).items():
                for program in programs:
                    # Hide these items
                    if program.title == EpgApi.EPG_NO_BROADCAST:
                        continue

                    epg[channel].append(dict(
                        start=program.start.isoformat(),
                        stop=program.end.isoformat(),
                        title=program.title,
                        description=program.description,
                        subtitle=None,
                        episode='S%dE%d' % (program.season, program.episode) if program.season and program.episode else None,
                        genre=None,
                        image=program.cover,
                        date=None,
                        stream=kodiutils.url_for('play_asset', asset_id=program.uid) if program.replay else None))

        return dict(version=1, epg=epg)
