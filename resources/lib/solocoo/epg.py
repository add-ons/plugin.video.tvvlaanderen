# -*- coding: utf-8 -*-
""" Solocoo EPG API """

from __future__ import absolute_import, division, unicode_literals

import json
import logging
from datetime import datetime, timedelta

import dateutil.tz
import dateutil.parser

from resources.lib.solocoo import SOLOCOO_API, util
from resources.lib.solocoo.util import parse_program

_LOGGER = logging.getLogger(__name__)


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

        entitlements = self._auth.list_entitlements()
        offers = entitlements.get('offers', [])

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
        programs = {channel: [parse_program(program, offers) for program in programs]
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
        return parse_program(data)

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
            date_obj = dateutil.parser.parse(date)

        # Mark as midnight
        date_obj = date_obj.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=dateutil.tz.gettz('CET'))
        date_obj = date_obj.astimezone(dateutil.tz.gettz('UTC'))

        return date_obj
