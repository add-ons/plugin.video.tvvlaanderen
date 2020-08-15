# -*- coding: utf-8 -*-
""" Solocoo EPG API """

from __future__ import absolute_import, division, unicode_literals

import json
import logging
from datetime import datetime, timedelta

import dateutil.tz

from resources.lib.solocoo import SOLOCOO_API, util
from resources.lib.solocoo.util import find_image

_LOGGER = logging.getLogger(__name__)


class EpgProgram:
    """ Channel object """

    def __init__(self, uid, title, description, cover, preview, start, end, channel_id, formats, genres, replay,
                 restart, age, series_id=None, season=None, episode=None, credit=None):
        self.uid = uid
        self.title = title
        self.description = description
        self.cover = cover
        self.preview = preview
        self.start = start
        self.end = end
        self.age = age
        self.channel_id = channel_id

        self.formats = formats
        self.generes = genres

        self.replay = replay
        self.restart = restart

        self.series_id = series_id
        self.season = season
        self.episode = episode

        self.credit = credit

    def __repr__(self):
        return "%r" % self.__dict__


class Credit:
    """ Credit object """

    ROLE_ACTOR = 'Actor'
    ROLE_COMPOSER = 'Composer'
    ROLE_DIRECTOR = 'Director'
    ROLE_GUEST = 'Guest'
    ROLE_PRESENTER = 'Presenter'
    ROLE_PRODUCER = 'Producer'

    def __init__(self, role, person, character=None):
        self.role = role
        self.person = person
        self.character = character


class EpgApi:
    """ Solocoo EPG API """

    def __init__(self, auth):
        """ Initialisation of the class.

        :param resources.lib.solocoo.auth.AuthApi auth: The Authentication object
        """
        self._auth = auth
        self._tokens = self._auth.login()  # Login and make sure we have a token

    def get_guide(self, channels, date):
        """ Get the guide for the specified channels and date.

        :param list|str channels:       A single channel or a list of channels to fetch.
        :param str date:                The date of the guide we want to fetch.
        :rtype: dict[str, list[Program]]
        """
        # Allow to specify one channel, and we map it to a list
        if not isinstance(channels, list):
            channels = [channels]

        # _LOGGER.debug('Requesting entitlements')
        # entitlements = self._auth.list_entitlements()

        # Generate dates in UTC format
        # TODO: this could be cleaner. We need times in Zulu timezone.
        date = self._parse_date(date)
        date_from = date.isoformat().replace('+00:00', '')
        date_to = (date + timedelta(days=1)).isoformat().replace('+00:00', '')

        reply = util.http_get(SOLOCOO_API + '/schedule',
                              params={
                                  'channels': ','.join(channels),
                                  'from': date_from,
                                  'until': date_to,
                                  'maxProgramsPerChannel': 2147483647,  # The android app also does this
                              },
                              token_bearer=self._tokens.jwt_token)
        data = json.loads(reply.text)

        # Parse to a dict (channel: list[Program])
        programs = {channel: [self._parse_epg_program(program) for program in programs]
                    for channel, programs in data.get('epg', []).items()}

        return programs

    def get_program(self, uid):
        """ Get program details by calling the API.

        :param str uid:                 The ID of the program.
        :rtype: Program
        """
        reply = util.http_get(SOLOCOO_API + '/assets/{uid}'.format(uid=uid),
                              token_bearer=self._tokens.jwt_token)
        data = json.loads(reply.text)

        # Parse to a Program object
        return self._parse_epg_program(data)

    @staticmethod
    def _parse_epg_program(program):
        """ Parse a program dict.

        :param dict program:            The program object to parse.
        :rtype: Program
        """

        # TODO: ratingCategories?
        return EpgProgram(
            uid=program.get('id'),
            title=program.get('title'),
            description=program.get('desc'),
            cover=find_image(program.get('images'), 'po'),  # portrait
            preview=find_image(program.get('images'), 'la'),  # landscape
            start=program.get('params', {}).get('start'),
            end=program.get('params', {}).get('end'),
            channel_id=program.get('params', {}).get('channelId'),
            formats=[format.get('title') for format in program.get('params', {}).get('formats')],
            genres=[genre.get('title') for genre in program.get('params', {}).get('genres')],
            replay=program.get('params', {}).get('replay', False),
            restart=program.get('params', {}).get('restart', False),
            age=program.get('params', {}).get('age'),
            series_id=program.get('params', {}).get('seriesId'),
            season=program.get('params', {}).get('seriesSeason'),
            episode=program.get('params', {}).get('seriesEpisode'),
            credit=[
                Credit(credit.get('role'), credit.get('person'), credit.get('character'))
                for credit in program.get('params', {}).get('credits', [])
            ]
        )

    @staticmethod
    def _parse_date(date):
        """ Parse the passed date to a real date.

        :param str date:                The date to parse.
        :rtype: datetime
         """
        if date is None or date == 'today':
            # Fetch today when no date is specified
            date_obj = datetime.today()
        elif date == 'yesterday':
            date_obj = (datetime.today() + timedelta(days=-1))
        elif date == 'tomorrow':
            date_obj = (datetime.today() + timedelta(days=1))
        else:
            date_obj = date  # TODO: parse date to an datetime object

        # Mark as midnight
        date_obj = date_obj.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=dateutil.tz.gettz('CET'))
        date_obj = date_obj.astimezone(dateutil.tz.gettz('UTC'))

        return date_obj
