# -*- coding: utf-8 -*-
""" Solocoo Search API """

from __future__ import absolute_import, division, unicode_literals

import json
import logging

from resources.lib.solocoo import SOLOCOO_API, util

_LOGGER = logging.getLogger(__name__)


class SearchApi:
    """ Solocoo Search API """

    def __init__(self, auth):
        """ Initialisation of the class.

        :param resources.lib.solocoo.auth.AuthApi auth: The Authentication object
        """
        self._auth = auth
        self._tokens = self._auth.login()

    def search(self, query):
        """ Search through the catalog.

        :returns: A list of results.

        :rtype: List[]
        """
        _LOGGER.debug('Requesting channel listing')
        reply = util.http_get(SOLOCOO_API + '/search', params=dict(query=query), token_bearer=self._tokens.jwt_token)
        data = json.loads(reply.text)

        # TODO: parse result
        _LOGGER.debug(data)

        return []
