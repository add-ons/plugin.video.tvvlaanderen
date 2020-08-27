# -*- coding: utf-8 -*-
""" Solocoo EPG API """

from __future__ import absolute_import, division, unicode_literals

import json
import logging
from datetime import datetime, timedelta

import dateutil.parser
import dateutil.tz

from resources.lib.solocoo import SOLOCOO_API, util
from resources.lib.solocoo.util import parse_program

_LOGGER = logging.getLogger(__name__)


class EpgApi:
    """ Solocoo EPG API """

    # Request this many channels at the same time
    EPG_CHUNK_SIZE = 40

    EPG_NO_BROADCAST = 'Geen uitzending'

    def __init__(self, auth):
        """ Initialisation of the class.

        :param resources.lib.solocoo.auth.AuthApi auth: The Authentication object
        """
        self._auth = auth
        self._tokens = self._auth.login()  # Login and make sure we have a token

    def get_guide(self, channels, date_from=None, date_to=None):
        """ Get the guide for the specified channels and date.

        :param list|str channels:       A single channel or a list of channels to fetch.
        :param str|datetime date_from:  The date of the guide we want to fetch.
        :param str|datetime date_to:    The date of the guide we want to fetch.
        :rtype: dict[str, list[resources.lib.solocoo.util.Program]]
        """
        # Allow to specify one channel, and we map it to a list
        if not isinstance(channels, list):
            channels = [channels]

        entitlements = self._auth.list_entitlements()
        offers = entitlements.get('offers', [])

        # Generate dates in UTC format
        if date_from is not None:
            date_from = self._parse_date(date_from)
        else:
            date_from = self._parse_date('today')

        if date_to is not None:
            date_to = self._parse_date(date_to)
        else:
            date_to = (date_from + timedelta(days=1))

        programs = {}

        for i in range(0, len(channels), self.EPG_CHUNK_SIZE):
            _LOGGER.debug('Fetching EPG at index %d', i)

            reply = util.http_get(SOLOCOO_API + '/schedule',
                                  params={
                                      'channels': ','.join(channels[i:i + self.EPG_CHUNK_SIZE]),
                                      'from': date_from.isoformat().replace('+00:00', ''),
                                      'until': date_to.isoformat().replace('+00:00', ''),
                                      'maxProgramsPerChannel': 2147483647,  # The android app also does this
                                  },
                                  token_bearer=self._tokens.jwt_token)
            data = json.loads(reply.text)

            # Parse to a dict (channel: list[Program])
            programs.update({channel: [parse_program(program, offers) for program in programs]
                             for channel, programs in data.get('epg', []).items()})

        return programs

    def get_program(self, uid):
        """ Get program details by calling the API.

        :param str uid:                 The ID of the program.
        :rtype: resources.lib.solocoo.util.Program
        """
        reply = util.http_get(SOLOCOO_API + '/assets/{uid}'.format(uid=uid),
                              token_bearer=self._tokens.jwt_token)
        data = json.loads(reply.text)

        # Parse to a Program object
        return parse_program(data)

    @staticmethod
    def _parse_date(date):
        """ Parse the passed date to a real date.

        :param str|datetime date:       The date to parse.
        :rtype: datetime
         """
        if isinstance(date, datetime):
            return date

        if date == 'today':
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
