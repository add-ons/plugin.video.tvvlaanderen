# -*- coding: utf-8 -*-
""" Tests for EPG API """

# pylint: disable=missing-docstring,no-self-use

from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import unittest

from resources.lib import kodiutils
from resources.lib.solocoo.auth import AuthApi
from resources.lib.solocoo.epg import EpgApi
from resources.lib.solocoo.util import Program

_LOGGER = logging.getLogger(__name__)


class TestEpg(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestEpg, self).__init__(*args, **kwargs)

        self._auth = AuthApi(kodiutils.get_setting('username'),
                             kodiutils.get_setting('password'),
                             kodiutils.get_setting('tenant'),
                             kodiutils.get_tokens_path())

    def test_get_guide(self):
        api = EpgApi(self._auth)

        channel_id = 'JIY-fyHDkM1Rk260f-WNXlVD8iYnlDtWOQ4ah0hb'

        guide = api.get_guide(channel_id, 'today')
        self.assertIsInstance(guide, dict)

        programs = guide.get(channel_id)
        self.assertIsInstance(programs, list)
        self.assertIsInstance(programs[0], Program)

    def test_get_guide_capi(self):
        api = EpgApi(self._auth)

        channel_id = [
            '1790975744',  # één
            '1790975808',  # canvas
        ]

        guide = api.get_guide_with_capi(channel_id, 'today')
        self.assertIsInstance(guide, dict)

        programs = guide.get(channel_id[0])
        self.assertIsInstance(programs, list)
        self.assertIsInstance(programs[0], Program)

    def test_get_program(self):
        api = EpgApi(self._auth)

        program_id = 'RsLDvuKQLenxLpd7dd2mi1rxLGNvg8_EHaRGSOmT'

        program = api.get_program(program_id)
        self.assertIsInstance(program, Program)


if __name__ == '__main__':
    unittest.main()
