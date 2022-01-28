# -*- coding: utf-8 -*-
""" Solocoo Channel API """

from __future__ import absolute_import, division, unicode_literals

import json
import logging

from resources.lib.solocoo import SOLOCOO_API, VodCatalog, VodSeason, util
from resources.lib.solocoo.util import parse_vod_episode, parse_vod_genre, parse_vod_movie, parse_vod_series

_LOGGER = logging.getLogger(__name__)

ASSET_TYPE_VOD_MOVIE = 'VOD'
ASSET_TYPE_VOD_SERIES = 'VODSeries'


class CollectionsApi:
    """ Solocoo Channel API """

    def __init__(self, auth):
        """ Initialisation of the class.

        :param resources.lib.solocoo.auth.AuthApi auth: The Authentication object
        """
        self._auth = auth
        self._tokens = self._auth.get_tokens()

    def get_catalogs(self):
        """ Get all catalogs.

        :returns:                       A list of all catalogs.
        :rtype: list[resources.lib.solocoo.VodCatalog]
        """
        # Fetch owner info from TV API
        reply = util.http_get(SOLOCOO_API + '/owners',
                              token_bearer=self._tokens.jwt_token)
        owners = json.loads(reply.text)

        # Create a dict with the owner id and the preferred image (png, dark)
        owner_images = {owner.get('id'): next((icon.get('url') for icon in owner.get('icons') if icon.get('format') == 'png' and icon.get('bg') == 'dark'), None)
                        for owner in owners.get('owners')}

        # Fetch channel listing from TV API
        reply = util.http_get(SOLOCOO_API + '/collections/movies',
                              params={
                                  'group': 'owner,genre',
                                  'sort': 'newest'
                              },
                              token_bearer=self._tokens.jwt_token)
        data = json.loads(reply.text)

        # Parse list to Channel objects
        collections = [
            VodCatalog(
                uid=collection.get('owner'),
                title=collection.get('title'),
                cover=owner_images.get(collection.get('owner'))
            )
            for collection in data.get('collection', [])
        ]

        return collections

    def get_genres(self, catalog=None):
        """ Get all genres.

        :param str catalog:             An optional catalog to fetch the genres from.
        :returns:                       A list of all genres.
        :rtype: list[resources.lib.solocoo.VodGenre]
        """
        if catalog:
            reply = util.http_get(SOLOCOO_API + '/collections/videos,owner,%s' % catalog,
                                  params={
                                      'group': 'genre',
                                      'sort': 'newest'
                                  },
                                  token_bearer=self._tokens.jwt_token)
        else:
            reply = util.http_get(SOLOCOO_API + '/collections/movies',
                                  params={
                                      'group': 'genre',
                                      'sort': 'newest'
                                  },
                                  token_bearer=self._tokens.jwt_token)

        data = json.loads(reply.text)

        # Parse list to Genre objects
        collections = [
            parse_vod_genre(collection)
            for collection in data.get('collection', [])
        ]

        return collections

    def get_seasons(self, asset):
        """ Get all seasons.

        :param str asset:               An asset ID of the Series.
        :returns:                       A list of all seasons.
        :rtype: list[resources.lib.solocoo.VodSeason]
        """
        # Fetch seasons for this series asset
        reply = util.http_get(SOLOCOO_API + '/collections/episodes',
                              params={
                                  'group': 'default',
                                  'sort': 'default',
                                  'asset': asset,
                              },
                              token_bearer=self._tokens.jwt_token)
        data = json.loads(reply.text)

        # Parse list to Season objects
        collections = [
            VodSeason(
                uid=None,
                title=collection.get('title'),
                query=collection.get('query'),
            )
            for collection in data.get('collection', [])
        ]

        return collections

    def query_assets(self, query):
        """ Get a list of assets of the specified query.

        :param str query:               The query to execute.
        :returns:                       A list of Assets.
        :rtype: list[resources.lib.solocoo.VodMovie|resources.lib.solocoo.VodSeries|resources.lib.solocoo.VodEpisode]
        """
        # Execute query
        reply = util.http_get(SOLOCOO_API + '/assets',
                              params={
                                  'query': query,
                                  'limit': 1000,
                              },
                              token_bearer=self._tokens.jwt_token)
        data = json.loads(reply.text)

        # Parse list to VodMovie or VodSeries objects
        assets = []
        for asset in data.get('assets'):
            if asset.get('type') == ASSET_TYPE_VOD_MOVIE:
                if asset.get('params', {}).get('seriesId'):
                    assets.append(parse_vod_episode(asset))
                else:
                    assets.append(parse_vod_movie(asset))
            if asset.get('type') == ASSET_TYPE_VOD_SERIES:
                assets.append(parse_vod_series(asset))

        return assets
