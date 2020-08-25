# -*- coding: utf-8 -*-
""" Solocoo utility functions """

from __future__ import absolute_import, division, unicode_literals

import logging
from datetime import datetime

import dateutil.parser
import dateutil.tz
import requests
from requests import HTTPError

from resources.lib.solocoo.exceptions import InvalidTokenException

_LOGGER = logging.getLogger(__name__)

# Setup a static session that can be reused for all calls
_SESSION = requests.Session()
_SESSION.headers['User-Agent'] = \
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'


class Channel:
    """ Channel Object """

    def __init__(self, uid, title, icon, preview, number, epg_now, epg_next, radio=False, available=None):
        """
        :param Program epg_now:     The currently playing program on this channel.
        :param Program epg_next:    The next playing program on this channel.
        """
        self.uid = uid
        self.title = title
        self.icon = icon
        self.preview = preview
        self.number = number
        self.epg_now = epg_now
        self.epg_next = epg_next
        self.radio = radio

        self.available = available

    def __repr__(self):
        return "%r" % self.__dict__


class StreamInfo:
    """ Stream information """

    def __init__(self, url, protocol, drm_protocol, drm_license_url, drm_certificate):
        self.url = url
        self.protocol = protocol
        self.drm_protocol = drm_protocol
        self.drm_license_url = drm_license_url
        self.drm_certificate = drm_certificate

    def __repr__(self):
        return "%r" % self.__dict__


class Program:
    """ Program object """

    def __init__(self, uid, title, description, cover, preview, start, end, channel_id, formats, genres, replay,
                 restart, age, series_id=None, season=None, episode=None, credit=None, available=None):
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

        self.available = available

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


def find_image(images, image_type):
    """ Find the largest image of the specified type.

    :param List[dict] images:       A list of all images.
    :param str image_type:          Type of image (la=landscape, po=portrait, lv=live).

    :returns:                       The requested image in the highest quality.
    :rtype: str
    """
    for size in ['lg', 'md', 'sm']:
        for image in images:
            if image.get('type') == image_type and image.get('size') == size:
                return image.get('url')

    return None


def check_deals_entitlement(deals, offers):
    """ Check if we have are entitled to play an item.

    :param List[object] deals:          A list of deals.
    :param List[str] offers:            A list of the offers that we have.

    :returns: True if we have a matching deal.
    :rtype: bool
    """

    # The API supports multiple deals for an item. A deal contains a list of offers it applies on, it can
    # also have a start and end time to indicate when the deal is active.
    #
    # This allows to define if something is playable for a specific offer, and to indicate the timeslot when this is
    # available.
    #
    # Example:
    # deals = [{'offers': ['0', '1', '2', '11'], 'start': '2020-07-30T09:15:00Z', 'end': '2020-07-30T10:25:00Z'},
    #          {'offers': ['0', '1', '2', '11'], 'start': '2020-07-30T10:30:00Z', 'end': '2020-08-06T09:15:00Z'}]

    # If we have no offers, allow everything
    if not offers:
        return False

    our_offers = set(offers)
    now = datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'

    for deal in deals:
        # Check if deal is active
        start = deal.get('start', None)
        end = deal.get('end', None)
        if start and end and not start <= now <= end:
            # _LOGGER.debug('This deal is not valid at this time')
            continue

        # Check if we have a matching offer
        deal_offers = set(deal.get('offers', []))
        if not our_offers & deal_offers:
            # _LOGGER.debug('Our offers (%s) don\'t match with this deal (%s)', our_offers, deal_offers)
            continue

        return True

    return False


def parse_channel(channel, offers=None):
    """ Parse the API result of a channel into a Channel object.

    :param dict channel:            The channel info from the API.
    :param List[str] offers:        A list of offers that we have.

    :returns: A channel that is parsed.
    :rtype: Channel
    """
    return Channel(
        uid=channel.get('id'),
        title=channel.get('title'),
        icon=find_image(channel.get('images'), 'la'),
        preview=find_image(channel.get('images'), 'lv'),
        number=channel.get('params', {}).get('lcn'),
        epg_now=parse_program(channel.get('params', {}).get('now')),
        epg_next=parse_program(channel.get('params', {}).get('next')),
        radio=channel.get('params', {}).get('radio', False),
        available=check_deals_entitlement(channel.get('deals'), offers) if offers else True,
    )


def parse_program(program, offers=None):
    """ Parse a program dict.

    :param dict program:            The program object to parse.
    :param List[str] offers:        A list of offers that we have.

    :returns: A program that is parsed.
    :rtype: Program
    """
    if not program:
        return None

    # Parse dates
    start = dateutil.parser.parse(program.get('params', {}).get('start')).astimezone(dateutil.tz.gettz('CET'))
    end = dateutil.parser.parse(program.get('params', {}).get('end')).astimezone(dateutil.tz.gettz('CET'))

    return Program(
        uid=program.get('id'),
        title=program.get('title'),
        description=program.get('desc'),
        cover=find_image(program.get('images'), 'po'),  # portrait
        preview=find_image(program.get('images'), 'la'),  # landscape
        start=start,
        end=end,
        channel_id=program.get('params', {}).get('channelId'),
        formats=[epg_format.get('title') for epg_format in program.get('params', {}).get('formats')],
        genres=[epg_genre.get('title') for epg_genre in program.get('params', {}).get('genres')],
        replay=program.get('params', {}).get('replay', False),
        restart=program.get('params', {}).get('restart', False),
        age=program.get('params', {}).get('age'),
        series_id=program.get('params', {}).get('seriesId'),
        season=program.get('params', {}).get('seriesSeason'),
        episode=program.get('params', {}).get('seriesEpisode'),
        credit=[
            Credit(credit.get('role'), credit.get('person'), credit.get('character'))
            for credit in program.get('params', {}).get('credits', [])
        ],
        available=check_deals_entitlement(program.get('deals'), offers) if offers else True,
    )


def http_get(url, params=None, token_bearer=None, token_cookie=None):
    """ Make a HTTP GET request for the specified URL.

    :param str url:                 The URL to call.
    :param dict params:             The query parameters to include to the URL.
    :param str token_bearer:        The token to use in Bearer authentication.
    :param str token_cookie:        The token to use in Cookie authentication.

    :returns:                       The HTTP Response object.
    :rtype: Response
    """
    try:
        return _request('GET', url=url, params=params, token_bearer=token_bearer, token_cookie=token_cookie)
    except HTTPError as ex:
        if ex.response.status_code == 401:
            raise InvalidTokenException
        raise


def http_post(url, params=None, form=None, data=None, token_bearer=None, token_cookie=None):
    """ Make a HTTP POST request for the specified URL.

    :param str url:                 The URL to call.
    :param dict params:             The query parameters to include to the URL.
    :param dict form:               A dictionary with form parameters to POST.
    :param dict data:               A dictionary with json parameters to POST.
    :param str token_bearer:        The token to use in Bearer authentication.
    :param str token_cookie:        The token to use in Cookie authentication.

    :returns:                       The HTTP Response object.
    :rtype: requests.Response
    """
    try:
        return _request('POST', url=url, params=params, form=form, data=data, token_bearer=token_bearer,
                        token_cookie=token_cookie)
    except HTTPError as ex:
        if ex.response.status_code == 401:
            raise InvalidTokenException
        raise


def _request(method, url, params=None, form=None, data=None, token_bearer=None, token_cookie=None):
    """ Makes a request for the specified URL.

    :param str method:              The HTTP Method to use.
    :param str url:                 The URL to call.
    :param dict params:             The query parameters to include to the URL.
    :param dict form:               A dictionary with form parameters to POST.
    :param dict data:               A dictionary with json parameters to POST.
    :param str token_bearer:        The token to use in Bearer authentication.
    :param str token_cookie:        The token to use in Cookie authentication.

    :returns:                       The HTTP Response object.
    :rtype: Response
    """
    _LOGGER.debug('Sending %s %s... (%s)', method, url, form or data)

    if token_bearer:
        headers = {
            'authorization': 'Bearer ' + token_bearer,
        }
    else:
        headers = {}

    if token_cookie:
        cookies = {
            '.ASPXAUTH': token_cookie
        }
    else:
        cookies = {}

    response = _SESSION.request(method, url, params=params, data=form, json=data, headers=headers, cookies=cookies)

    # Set encoding to UTF-8 if no charset is indicated in http headers (https://github.com/psf/requests/issues/1604)
    if not response.encoding:
        response.encoding = 'utf-8'

    _LOGGER.debug('Got response (status=%s): %s', response.status_code, response.text)

    # Raise a generic HTTPError exception when we got an non-okay status code.
    response.raise_for_status()

    return response
