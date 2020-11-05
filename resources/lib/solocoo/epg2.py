# -*- coding: utf-8 -*-
""" Solocoo EPG API """

from __future__ import absolute_import, division, unicode_literals

import json
import logging
from datetime import datetime, timedelta

import dateutil.parser
import dateutil.tz

from resources.lib.solocoo import util
from resources.lib.solocoo.util import Program, Channel

_LOGGER = logging.getLogger(__name__)

# EPG detail bits
BIT_EPG_DETAIL_ID = 1
BIT_EPG_DETAIL_TITLE = 2
BIT_EPG_DETAIL_DESCRIPTION = 8
BIT_EPG_DETAIL_AGE = 16
BIT_EPG_DETAIL_CATEGORY = 32
BIT_EPG_DETAIL_START = 64
BIT_EPG_DETAIL_END = 128
BIT_EPG_DETAIL_FLAGS = 256
BIT_EPG_DETAIL_GENRE = 512
BIT_EPG_DETAIL_COVER = 1024
BIT_EPG_DETAIL_SEASON_NO = 2048
BIT_EPG_DETAIL_EPISODE_NO = 4096
BIT_EPG_DETAIL_SERIES_ID = 8192
BIT_EPG_DETAIL_SG = 16384
BIT_EPG_DETAIL_CHANEL_NAME = 32768
BIT_EPG_DETAIL_GENRES = 65536
BIT_EPG_DETAIL_CREDITS = 131072
BIT_EPG_DETAIL_FORMAT = 262144
BIT_EPG_DETAIL_FORMATS = 524288
BIT_EPG_DETAIL_AIRDATE = 16777216

EPG_DETAIL = (BIT_EPG_DETAIL_ID | BIT_EPG_DETAIL_TITLE | BIT_EPG_DETAIL_DESCRIPTION | BIT_EPG_DETAIL_AGE | BIT_EPG_DETAIL_CATEGORY |
              BIT_EPG_DETAIL_START | BIT_EPG_DETAIL_END | BIT_EPG_DETAIL_COVER | BIT_EPG_DETAIL_SEASON_NO | BIT_EPG_DETAIL_EPISODE_NO |
              BIT_EPG_DETAIL_SERIES_ID | BIT_EPG_DETAIL_GENRES | BIT_EPG_DETAIL_CREDITS | BIT_EPG_DETAIL_FORMATS)

# Channel detail bits
BIT_CHANNEL_DETAIL_ID = 1
BIT_CHANNEL_DETAIL_NUMBER = 2
BIT_CHANNEL_DETAIL_STATIONID = 4
BIT_CHANNEL_DETAIL_TITLE = 8
BIT_CHANNEL_DETAIL_16 = 16  # Unknown
BIT_CHANNEL_DETAIL_GENRES = 32
BIT_CHANNEL_DETAIL_FLAGS = 64
BIT_CHANNEL_DETAIL_128 = 128  # Unknown
BIT_CHANNEL_DETAIL_DVBS = 256  # 3:3225:21025:235
BIT_CHANNEL_DETAIL_SDSD = 2048  # 430B0121870002359602990002

# Channel flags
BIT_CHANNEL_FLAG_RADIO = 16
BIT_CHANNEL_FLAG_PIN = 256
BIT_CHANNEL_FLAG_512 = 512  # Unknown
BIT_CHANNEL_FLAG_1024 = 1024  # Unknown
BIT_CHANNEL_FLAG_REPLAYABLE = 2048
BIT_CHANNEL_FLAG_131072 = 131072  # Unknown
BIT_CHANNEL_FLAG_262144 = 262144  # Unknown
BIT_CHANNEL_FLAG_1048576 = 1048576  # Unknown
BIT_CHANNEL_FLAG_2097152 = 2097152  # Unknown


class Epg2Api:
    """ Solocoo EPG API """

    # Request this many channels at the same time
    EPG_CHUNK_SIZE = 40

    EPG_API = 'https://m7be2.solocoo.tv/m7be2iphone/capi.aspx'  # TODO: use tenant

    def __init__(self, auth):
        """ Initialisation of the class.

        :param resources.lib.solocoo.auth.AuthApi auth: The Authentication object
        """
        self._auth = auth
        self._tokens = self._auth.login()  # Login and make sure we have a token

    def get_channels(self):
        """ Get a list of all channels that have EPG data. """
        # TODO: cache this

        reply = util.http_get(self.EPG_API,
                              params={
                                  'z': 'epg',
                                  'f_format': 'clx',  # channel listing
                                  'd': 3,
                                  'v': 3,
                                  'u': self._tokens.device_serial,
                                  'a': 'tvv',
                                  'cs': (BIT_CHANNEL_DETAIL_ID + BIT_CHANNEL_DETAIL_NUMBER + BIT_CHANNEL_DETAIL_STATIONID +
                                         BIT_CHANNEL_DETAIL_TITLE + BIT_CHANNEL_DETAIL_GENRES + BIT_CHANNEL_DETAIL_FLAGS),  # 111
                                  'lng': 'nl_BE',
                                  'streams': 15,
                              },
                              token_cookie=self._tokens.aspx_token)

        result = json.loads(reply.text)

        channels = []
        idx = 0
        for channel in result[0][1]:
            channels.append(self._parse_epg_channel(channel, result, idx))
            idx = idx + 1

        return channels

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

            reply = util.http_get(self.EPG_API,
                                  params={
                                      'z': 'epg',
                                      'f_format': 'pg',  # program guide
                                      'v': 3,  # version
                                      'u': self._tokens.device_serial,
                                      'a': 'tvv',
                                      # 'n': 2,  # number of results
                                      's': '!'.join(channels[i:i + self.EPG_CHUNK_SIZE]),  # station id's separated with a !
                                      'f': date_from.strftime("%s") + '000',  # from timestamp
                                      't': date_to.strftime("%s") + '000',  # to timestamp
                                      'cs': EPG_DETAIL,
                                      'lng': 'nl_BE',
                                  },
                                  token_cookie=self._tokens.aspx_token)

            data = json.loads(reply.text)

            # Parse to a dict (channel: list[Program])
            programs.update({channel: [self._parse_epg_program(program) for program in programs]
                             for channel, programs in data[1].items()})

        return programs

    def get_program(self, uid):
        """ Get program details by calling the API.

        :param str uid:                 The ID of the program.
        :rtype: resources.lib.solocoo.util.Program
        """
        reply = util.http_get(self.EPG_API,
                              params={
                                  'z': 'epg',
                                  'f_format': 'ei',  # episode info
                                  # 'd': 6,
                                  'v': 3,  # version
                                  'u': self._tokens.device_serial,
                                  'a': 'tvv',
                                  'lids': uid,
                                  'cs': EPG_DETAIL,
                                  'lng': 'nl_BE',
                              },
                              token_cookie=self._tokens.aspx_token)
        data = json.loads(reply.text)

        # Parse to a Program object
        return self._parse_epg_program(data[0])

    def convert_program_to_tvapi(self, locId):
        """ Convert a locId to a assetId. """
        reply = util.http_get(self.EPG_API,
                              params={
                                  'z': 'converttotvapi',
                                  'locId': locId,
                                  'type': 'EPGProgram',
                              },
                              token_cookie=self._tokens.aspx_token)
        data = json.loads(reply.text)

        return data.get('assetId')

    def convert_channel_to_tvapi(self, realSid):
        """ Convert a locId to a assetId. """
        reply = util.http_get(self.EPG_API,
                              params={
                                  'z': 'converttotvapi',
                                  'realSid': realSid,
                                  'type': 'Station',
                              },
                              token_cookie=self._tokens.aspx_token)
        data = json.loads(reply.text)

        return data.get('assetId')

    def convert_from_tvapi(self, assetId):
        """ Convert an assetId to a locId or stationId. """
        reply = util.http_get(self.EPG_API,
                              params={
                                  'z': 'convertfromtvapi',
                                  'u': self._tokens.device_serial,
                                  'a': 'tvv',
                                  'id': assetId,
                                  'lng': 'nl_BE',
                              },
                              token_cookie=self._tokens.aspx_token)
        data = json.loads(reply.text)

        if data.get('type') == 'Station':
            return 'station', data.get('realSid')

        if data.get('type') == 'EPGProgram':
            return 'program', data.get('locId')

        raise Exception('Unknown type: %s' % data.get('type'))

    def _parse_epg_channel(self, channel, data, idx):
        """ Parse the API result of a channel into a Channel object.

        :param dict channel:            The channel info from the API.

        :returns: A channel that is parsed.
        :rtype: Channel
        """

        # I got this from https://github.com/Sorien/plugin.video.sl
        is_available = (len(data[3][0]) > (idx >> 5)) and (data[3][0][idx >> 5] & (1 << (idx & 31)) > 0)

        # TODO: remove this, this is for debugging
        f = lambda n: [n & 2 ** i for i in range(32)]
        _LOGGER.debug(channel)
        _LOGGER.debug('channel = %s, is_available = %s, flags = %s, decoded = %s',
                      channel.get('title'), is_available, channel.get('flags'), f(channel.get('flags')))

        return Channel(
            uid=channel.get('stationid'),
            title=channel.get('title'),
            icon=None,
            preview=None,
            number=channel.get('number'),
            # epg_now=parse_program(channel.get('params', {}).get('now')),
            # epg_next=parse_program(channel.get('params', {}).get('next')),
            radio=(channel.get('flags') & BIT_CHANNEL_FLAG_RADIO) > 0,
            replay=(channel.get('flags') & BIT_CHANNEL_FLAG_REPLAYABLE) > 0,
            available=is_available,
        )

    @staticmethod
    def _parse_epg_program(program):
        """ Parse an EPG program dict.

        :param dict program:            The program object to parse.

        :returns: A program that is parsed.
        :rtype: EpgProgram
        """
        if not program:
            return None

        # Parse dates
        start = datetime.fromtimestamp(program.get('start') / 1000, dateutil.tz.gettz('CET'))
        end = datetime.fromtimestamp(program.get('end') / 1000, dateutil.tz.gettz('CET'))

        # TODO: use url for cover from tenant or a const somewhere

        return Program(
            uid=program.get('locId'),
            title=program.get('title'),
            description=program.get('description'),
            cover='https://m7be2.solocoo.tv/m7be2iphone/' + program.get('cover').replace('mpimages/', 'mpimages/447x251/'),
            preview=None,
            start=start,
            end=end,
            duration=(end - start).total_seconds(),
            channel_id=None,
            formats=None,
            genres=None,
            replay=None,
            restart=None,
            age=program.get('age'),
            series_id=program.get('seriesId'),
            season=program.get('seasonNo'),
            episode=program.get('episodeNo'),
            # credit=[
            #     Credit(credit.get('role'), credit.get('person'), credit.get('character'))
            #     for credit in program.get('params', {}).get('credits', [])
            # ],
            # available=check_deals_entitlement(program.get('deals'), offers),
        )

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
