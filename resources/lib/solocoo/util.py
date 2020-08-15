# -*- coding: utf-8 -*-
""" Solocoo utility functions """

from __future__ import absolute_import, division, unicode_literals

import logging
from datetime import datetime

import requests

from resources.lib.solocoo.exceptions import NotAvailableInOfferException

_LOGGER = logging.getLogger(__name__)

# Setup a static session that can be reused for all calls
_SESSION = requests.Session()
_SESSION.headers['User-Agent'] = \
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'


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

    :returns: The requested image in the highest quality.
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

    our_offers = set(offers)
    now = datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'

    # TODO: cleanup debug

    for deal in deals:
        # Check if deal is active
        start = deal.get('start', None)
        end = deal.get('end', None)
        if start and end and not start <= now <= end:
            _LOGGER.debug('This deal is not valid at this time')
            continue

        # Check if we have a matching offer
        deal_offers = set(deal.get('offers', []))
        if not our_offers & deal_offers:
            _LOGGER.debug('Our offers (%s) don\'t match with this deal (%s)', our_offers, deal_offers)
            continue

        return True

    return False


def http_get(url, params=None, token_bearer=None, token_cookie=None):
    """ Make a HTTP GET request for the specified URL.

    :param str url:                 The URL to call.
    :param dict params:             The query parameters to include to the URL.
    :param str token_bearer:        The token to use in Bearer authentication.
    :param str token_cookie:        The token to use in Cookie authentication.

    :returns:                       The HTTP Response object.
    :rtype: Response
    """
    return _request('GET', url=url, params=params, token_bearer=token_bearer, token_cookie=token_cookie)


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
    # TODO: catch InvalidLoginException, re-authenticate and retry
    return _request('POST', url=url, params=params, form=form, data=data, token_bearer=token_bearer,
                    token_cookie=token_cookie)


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

    _LOGGER.debug('Got response (status=%s): %s...', response.status_code, response.text[:80])

    if response.status_code == 402:
        raise NotAvailableInOfferException

    # Raise a generic HTTPError exception when we got an non-okay status code.
    response.raise_for_status()

    return response
