# -*- coding: utf-8 -*-
""" Menu module """

from __future__ import absolute_import, division, unicode_literals

import logging

from resources.lib import kodiutils
from resources.lib.kodiutils import TitleItem
from resources.lib.solocoo.util import Channel, Program

_LOGGER = logging.getLogger(__name__)


class Menu:
    """ Menu code """

    def __init__(self):
        """ Initialise object. """

    @staticmethod
    def show_mainmenu():
        """ Show the main menu. """
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

    @classmethod
    def generate_titleitem(cls, item):
        """ Generate a TitleItem.

        :param Union[Channel] item:         The item to convert to a TitleItem.

        :rtype: TitleItem
        """
        #
        # Program
        #
        if isinstance(item, Program):
            title = '{time} - {title}'.format(
                time=item.start.strftime('%H:%M'),
                title=item.title,
            )

            if item.replay and item.available:
                path = kodiutils.url_for('play_asset', asset_id=item.uid)
            else:
                path = None
                title = '[COLOR gray]' + title + '[/COLOR]'

            return TitleItem(
                title=title,
                path=path,
                art_dict={
                    'cover': item.cover,
                    'icon': item.preview,
                    'thumb': item.preview,
                    'fanart': item.preview,
                },
                info_dict={
                    'tvshowtitle': item.title,
                    'plot': item.description,
                    'season': item.season,
                    'episode': item.episode,
                    'mediatype': 'episode',
                },
                prop_dict={
                    'inputstream.adaptive.play_timeshift_buffer': 'true',  # Play from the beginning
                    'inputstream.adaptive.manifest_update_parameter': 'full',
                },
                is_playable=path is not None,
            )

        #
        # Channel
        #
        if isinstance(item, Channel):
            return TitleItem(
                title=item.title,
                path=kodiutils.url_for('play_asset', asset_id=item.uid) + '?.pvr',
                art_dict={
                    'cover': item.icon,
                    'icon': item.icon,
                    'thumb': item.icon,
                    # 'fanart': item.preview,  # Preview doesn't seem to work on most channels
                },
                info_dict={
                    'title': item.title,
                    'plot': cls._format_channel_plot(item),
                    'playcount': 0,
                    'mediatype': 'video',
                },
                prop_dict={
                    'inputstream.adaptive.manifest_update_parameter': 'full',
                },
                is_playable=True,
            )

        raise Exception('Unknown type: %s' % item)

    @classmethod
    def _format_channel_plot(cls, channel):
        """ Format a plot for a channel.

        :param Channel channel:     The channel we want to have a plot for.

        :return A formatted plot for this channel.
        :rtype str
        """
        plot = ''

        if channel.epg_now:
            plot += kodiutils.localize(30213,  # Now
                                       start=channel.epg_now.start.strftime('%H:%M'),
                                       end=channel.epg_now.end.strftime('%H:%M'),
                                       title=channel.epg_now.title) + "\n"

        if channel.epg_next:
            plot += kodiutils.localize(30214,  # Next
                                       start=channel.epg_next.start.strftime('%H:%M'),
                                       end=channel.epg_next.end.strftime('%H:%M'),
                                       title=channel.epg_next.title) + "\n"

        return plot
