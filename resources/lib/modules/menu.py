# -*- coding: utf-8 -*-
""" Menu module """

from __future__ import absolute_import, division, unicode_literals

import logging

from resources.lib import kodiutils
from resources.lib.kodiutils import TitleItem
from resources.lib.solocoo.channel import Channel

_LOGGER = logging.getLogger(__name__)


class Menu:
    """ Menu code """

    def __init__(self):
        """ Initialise object """

    @staticmethod
    def show_mainmenu():
        """ Show the main menu """
        listing = [
            TitleItem(
                title=kodiutils.localize(30007),  # TV Channels
                path=kodiutils.url_for('show_channels'),
                art_dict=dict(
                    icon='DefaultAddonPVRClient.png',
                    fanart=kodiutils.get_addon_info('fanart'),
                ),
                info_dict=dict(
                    plot=kodiutils.localize(30008),
                )
            ),
            TitleItem(
                title=kodiutils.localize(30009),  # Search
                path=kodiutils.url_for('show_search'),
                art_dict=dict(
                    icon='DefaultAddonsSearch.png',
                    fanart=kodiutils.get_addon_info('fanart'),
                ),
                info_dict=dict(
                    plot=kodiutils.localize(30010),
                )
            )
        ]

        kodiutils.show_listing(listing, sort=['unsorted'])

    @staticmethod
    def generate_titleitem(item):
        """ Generate a TitleItem.
        :param Union[Channel] item:         The item to convert to a TitleItem.

        :rtype: TitleItem
        """
        #
        # Channel
        #
        if isinstance(item, Channel):
            return TitleItem(
                title=item.title,
                path=kodiutils.url_for('play_channel', channel=item.uid) + '?.pvr',
                art_dict={
                    'icon': item.icon,
                    'thumb': item.icon,
                    'fanart': item.preview,
                },
                info_dict={
                    'plot': None,
                    'playcount': 0,
                    'mediatype': 'video',
                },
                is_playable=True,
            )

        raise Exception('Unknown type')
