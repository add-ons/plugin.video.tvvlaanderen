# -*- coding: utf-8 -*-
"""Implementation of IPTVManager class"""

from __future__ import absolute_import, division, unicode_literals

import logging

_LOGGER = logging.getLogger(__name__)


class IPTVManager:
    """Interface to IPTV Manager"""

    def __init__(self, port):
        """Initialize IPTV Manager object"""
        self.port = port

    def via_socket(func):  # pylint: disable=no-self-argument
        """Send the output of the wrapped function to socket"""

        def send(self):
            """Decorator to send over a socket"""
            import json
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', self.port))
            try:
                sock.sendall(json.dumps(func()).encode())  # pylint: disable=not-callable
            finally:
                sock.close()

        return send

    @via_socket
    def send_channels():  # pylint: disable=no-method-argument
        """Return JSON-STREAMS formatted information to IPTV Manager"""
        streams = []

        return dict(version=1, streams=streams)

    @via_socket
    def send_epg():  # pylint: disable=no-method-argument
        """Return JSON-EPG formatted information to IPTV Manager"""
        epg = dict()

        return dict(version=1, epg=epg)
