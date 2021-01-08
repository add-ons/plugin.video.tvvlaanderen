# -*- coding: utf-8 -*-
""" Tests for Routing """

# pylint: disable=missing-docstring,no-self-use

from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import unittest

from resources.lib import addon, kodiutils

routing = addon.routing  # pylint: disable=invalid-name

_LOGGER = logging.getLogger(__name__)

EXAMPLE_CHANNEL = 'JIY-fyHDkM1Rk260f-WNXlVD8iYnlDtWOQ4ah0hb:1790975744'  # één


@unittest.skipUnless(kodiutils.get_setting('username') and kodiutils.get_setting('password'), 'Skipping since we have no credentials.')
class TestRouting(unittest.TestCase):
    """ Tests for Routing """

    def __init__(self, *args, **kwargs):
        super(TestRouting, self).__init__(*args, **kwargs)

    def setUp(self):
        # Don't warn that we don't close our HTTPS connections, this is on purpose.
        # warnings.simplefilter("ignore", ResourceWarning)
        pass

    def test_index(self):
        routing.run([routing.url_for(addon.index), '0', ''])

    def test_main_menu(self):
        routing.run([routing.url_for(addon.show_main_menu), '0', ''])

    def test_channels_menu(self):
        routing.run([routing.url_for(addon.show_channels), '0', ''])
        routing.run([routing.url_for(addon.show_channel, channel_id=EXAMPLE_CHANNEL), '0', ''])
        routing.run([routing.url_for(addon.show_channel_guide, channel_id=EXAMPLE_CHANNEL), '0', ''])
        routing.run([routing.url_for(addon.show_channel_guide_detail, channel_id=EXAMPLE_CHANNEL, date='today'), '0', ''])
        routing.run([routing.url_for(addon.show_channel_replay, channel_id=EXAMPLE_CHANNEL), '0', ''])

    def test_search_menu(self):
        routing.run([routing.url_for(addon.show_search), '0', ''])
        routing.run([routing.url_for(addon.show_search, query='vier'), '0', ''])


if __name__ == '__main__':
    unittest.main()
