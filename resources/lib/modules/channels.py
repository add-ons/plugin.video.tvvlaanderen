# -*- coding: utf-8 -*-
""" Channels module """

from __future__ import absolute_import, division, unicode_literals

import logging
from datetime import datetime, timedelta

from resources.lib import kodiutils
from resources.lib.kodiutils import TitleItem
from resources.lib.modules.menu import Menu
from resources.lib.solocoo.auth import AuthApi
from resources.lib.solocoo.channel import ChannelApi
from resources.lib.solocoo.epg import EpgApi

_LOGGER = logging.getLogger(__name__)


class Channels:
    """ Menu code related to channels. """

    def __init__(self):
        """ Initialise object. """
        auth = AuthApi(username=kodiutils.get_setting('username'),
                       password=kodiutils.get_setting('password'),
                       tenant=kodiutils.get_setting('tenant'),
                       token_path=kodiutils.get_tokens_path())
        self._entitlements = auth.list_entitlements()
        self._channel_api = ChannelApi(auth)
        self._epg_api = EpgApi(auth)

    def show_channels(self):
        """ Shows TV channels. """
        channels = self._channel_api.get_channels(False)

        listing = []
        for item in channels:
            listing.append(TitleItem(
                title=item.title,
                path=kodiutils.url_for('show_channel', channel_id=item.uid),
                art_dict={
                    'cover': item.icon,
                    'icon': item.icon,
                    'thumb': item.icon,
                },
                info_dict={
                    'title': item.title,
                    'plot': None,
                    'playcount': 0,
                    'mediatype': 'video',
                },
            ))

        kodiutils.show_listing(listing, 30007)

    def show_channel(self, channel_id):
        """ Shows TV channel details.

        :param str channel_id:          The channel we want to display.
        """
        channel = self._channel_api.get_asset(channel_id)

        listing = []

        # Play live
        live_titleitem = Menu.generate_titleitem(channel)
        live_titleitem.info_dict['title'] = kodiutils.localize(30051, channel=channel.title)  # Watch live [B]{channel}[/B]
        listing.append(live_titleitem)

        # Restart currently airing program
        if channel.epg_now and channel.epg_now.restart:
            restart_titleitem = Menu.generate_titleitem(channel.epg_now)
            restart_titleitem.info_dict['title'] = kodiutils.localize(30052, program=channel.epg_now.title)  # Restart [B]{program}[/B]
            restart_titleitem.art_dict['thumb'] = 'DefaultInProgressShows.png'
            listing.append(restart_titleitem)

        # TV Guide
        listing.append(
            TitleItem(
                title=kodiutils.localize(30053, channel=channel.title),  # TV Guide for {channel}
                path=kodiutils.url_for('show_channel_guide', channel_id=channel_id),
                art_dict=dict(
                    icon='DefaultAddonTvInfo.png',
                ),
                info_dict=dict(
                    plot=kodiutils.localize(30054, channel=channel.title),  # Browse the TV Guide for {channel}
                ),
            )
        )

        kodiutils.show_listing(listing, 30007)

    def show_channel_guide(self, channel_id):
        """ Shows the dates in the tv guide.

        :param str channel_id:          The channel for which we want to show an EPG.
        """
        listing = []
        for day in self._get_dates('%A %d %B %Y'):
            if day.get('highlight'):
                title = '[B]{title}[/B]'.format(title=day.get('title'))
            else:
                title = day.get('title')

            listing.append(TitleItem(
                title=title,
                path=kodiutils.url_for('show_channel_guide_detail', channel_id=channel_id, date=day.get('key')),
                art_dict=dict(
                    icon='DefaultYear.png',
                    thumb='DefaultYear.png',
                ),
                info_dict=dict(
                    plot=None,
                    date=day.get('date'),
                ),
            ))

        kodiutils.show_listing(listing, 30013, content='files')

    def show_channel_guide_detail(self, channel_id, date):
        """ Shows the dates in the tv guide.

        :param str channel_id:          The channel for which we want to show an EPG.
        :param str date:                The date to show.
        """
        programs = self._epg_api.get_guide([channel_id], date)

        listing = [Menu.generate_titleitem(item) for item in programs.get(channel_id)]

        kodiutils.show_listing(listing, 30013, content='files')

    @staticmethod
    def _get_dates(date_format):
        """ Return a dict of dates.

        :param str date_format:         The date format to use for the labels.

        :rtype: list[dict]
        """
        dates = []
        today = datetime.today()

        # The API provides 7 days in the past and 0 days in the future
        for i in range(0, -7, -1):
            day = today + timedelta(days=i)

            if i == -1:
                dates.append({
                    'title': '%s, %s' % (kodiutils.localize(30301), day.strftime(date_format)),  # Yesterday
                    'key': 'yesterday',
                    'date': day.strftime('%d.%m.%Y'),
                    'highlight': False,
                })
            elif i == 0:
                dates.append({
                    'title': '%s, %s' % (kodiutils.localize(30302), day.strftime(date_format)),  # Today
                    'key': 'today',
                    'date': day.strftime('%d.%m.%Y'),
                    'highlight': True,
                })
            elif i == 1:
                dates.append({
                    'title': '%s, %s' % (kodiutils.localize(30303), day.strftime(date_format)),  # Tomorrow
                    'key': 'tomorrow',
                    'date': day.strftime('%d.%m.%Y'),
                    'highlight': False,
                })
            else:
                dates.append({
                    'title': day.strftime(date_format),
                    'key': day.strftime('%Y-%m-%d'),
                    'date': day.strftime('%d.%m.%Y'),
                    'highlight': False,
                })

        return dates
