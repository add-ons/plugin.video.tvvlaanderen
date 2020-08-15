# -*- coding: utf-8 -*-
""" Search module """

from __future__ import absolute_import, division, unicode_literals

import logging

from resources.lib import kodiutils
from resources.lib.modules.menu import Menu
from resources.lib.solocoo.auth import AuthApi
from resources.lib.solocoo.search import SearchApi

_LOGGER = logging.getLogger(__name__)


class Search:
    """ Menu code related to search """

    def __init__(self):
        """ Initialise object """
        # TODO: hardcoded tvv
        auth = AuthApi(username=kodiutils.get_setting('username'),
                       password=kodiutils.get_setting('password'),
                       tenant='tvv',
                       token_path=kodiutils.get_tokens_path())
        self._search_api = SearchApi(auth)

    def show_search(self, query=None):
        """ Shows the search dialog
        :type query: str
        """
        if not query:
            # Ask for query
            query = kodiutils.get_search_string(heading=kodiutils.localize(30009))  # Search
            if not query:
                kodiutils.end_of_directory()
                return

        # Do search
        try:
            items = self._search_api.search(query)
        except Exception as ex:  # pylint: disable=broad-except
            kodiutils.notification(message=str(ex))
            kodiutils.end_of_directory()
            return

        # Display results
        listing = [Menu.generate_titleitem(item) for item in items]

        # Sort like we get our results back.
        kodiutils.show_listing(listing, 30009, content='tvshows')
