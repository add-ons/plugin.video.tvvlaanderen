# -*- coding: utf-8 -*-
""" Tests for Collections API """

# pylint: disable=missing-docstring,no-self-use

from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import unittest

from resources.lib import kodiutils
from resources.lib.solocoo import VodCatalog, VodGenre, VodMovie
from resources.lib.solocoo.auth import AuthApi
from resources.lib.solocoo.collections import CollectionsApi

_LOGGER = logging.getLogger(__name__)


@unittest.skipUnless(kodiutils.get_setting('username') and kodiutils.get_setting('password'), 'Skipping since we have no credentials.')
class TestCollections(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestCollections, self).__init__(*args, **kwargs)

        self._auth = AuthApi(kodiutils.get_setting('username'),
                             kodiutils.get_setting('password'),
                             kodiutils.get_setting('tenant'),
                             kodiutils.get_tokens_path())

    def test_get_catalogs(self):
        api = CollectionsApi(self._auth)

        catalogs = api.get_catalogs()
        self.assertIsInstance(catalogs, list)
        self.assertIsInstance(catalogs[0], VodCatalog)
        self.assertIsNotNone(catalogs[0].uid)
        self.assertIsNotNone(catalogs[0].title)

        _LOGGER.info(catalogs)

    def test_get_genres(self):
        api = CollectionsApi(self._auth)

        genres = api.get_genres()
        self.assertIsInstance(genres, list)
        self.assertIsInstance(genres[0], VodGenre)
        self.assertIsNotNone(genres[0].query)
        self.assertIsNotNone(genres[0].title)

        _LOGGER.info(genres)

    def test_get_assets(self):
        api = CollectionsApi(self._auth)

        assets = api.query_assets('videos,categoryb64,U2NpZW5jZSBGaWN0aW9u,owners,cnlseriesbe,starznl,cnlvodnl,bbcsnl,histint,ngnl,lovnaten')  # Science Fiction
        self.assertIsInstance(assets, list)
        self.assertIsInstance(assets[0], VodMovie)
        self.assertIsNotNone(assets[0].uid)
        self.assertIsNotNone(assets[0].title)

        _LOGGER.info(assets)


if __name__ == '__main__':
    unittest.main()
