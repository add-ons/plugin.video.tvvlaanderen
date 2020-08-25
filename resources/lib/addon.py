# -*- coding: utf-8 -*-
""" Addon code """

from __future__ import absolute_import, division, unicode_literals

import logging

from routing import Plugin

from resources.lib import kodilogging

kodilogging.config()
routing = Plugin()  # pylint: disable=invalid-name
_LOGGER = logging.getLogger('addon')


@routing.route('/')
def show_main_menu():
    """ Show the main menu """
    from resources.lib.modules.menu import Menu
    Menu().show_mainmenu()


@routing.route('/channels')
def show_channels():
    """ Shows Live TV channels """
    from resources.lib.modules.channels import Channels
    Channels().show_channels()


@routing.route('/channel/<channel_id>')
def show_channel(channel_id):
    """ Shows Live TV channel details """
    from resources.lib.modules.channels import Channels
    Channels().show_channel(channel_id)


@routing.route('/channel/<channel_id>/guide')
def show_channel_guide(channel_id):
    """ Shows Live TV channel guide """
    from resources.lib.modules.channels import Channels
    Channels().show_channel_guide(channel_id)


@routing.route('/channel/<channel_id>/guide/<date>')
def show_channel_guide_detail(channel_id, date):
    """ Shows Live TV channel guide details """
    from resources.lib.modules.channels import Channels
    Channels().show_channel_guide_detail(channel_id, date)


@routing.route('/play/asset/<asset_id>')
def play_asset(asset_id):
    """ PLay a Program """
    from resources.lib.modules.player import Player
    Player().play_asset(asset_id)


@routing.route('/search')
@routing.route('/search/<query>')
def show_search(query=None):
    """ Shows the search dialog """
    from resources.lib.modules.search import Search
    Search().show_search(query)


@routing.route('/iptv/channels')
def iptv_channels():
    """ Generate channel data for the Kodi PVR integration """
    from resources.lib.modules.iptvmanager import IPTVManager
    IPTVManager(int(routing.args['port'][0])).send_channels()  # pylint: disable=too-many-function-args


@routing.route('/iptv/epg')
def iptv_epg():
    """ Generate EPG data for the Kodi PVR integration """
    from resources.lib.modules.iptvmanager import IPTVManager
    IPTVManager(int(routing.args['port'][0])).send_epg()  # pylint: disable=too-many-function-args


def run(params):
    """ Run the routing plugin """
    routing.run(params)
