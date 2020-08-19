# -*- coding: utf-8 -*-
""" Tests for Search API """

# pylint: disable=missing-docstring,no-self-use

from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import unittest

from resources.lib import kodiutils
from resources.lib.solocoo.auth import AuthApi
from resources.lib.solocoo.search import SearchApi

_LOGGER = logging.getLogger(__name__)


class TestSearch(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestSearch, self).__init__(*args, **kwargs)

        self._auth = AuthApi(kodiutils.get_setting('username'),
                             kodiutils.get_setting('password'),
                             kodiutils.get_setting('tenant'),
                             kodiutils.get_tokens_path())

    def test_search(self):
        api = SearchApi(self._auth)

        query = 'vier'

        results = api.search(query)
        self.assertIsInstance(results, list)


if __name__ == '__main__':
    unittest.main()
