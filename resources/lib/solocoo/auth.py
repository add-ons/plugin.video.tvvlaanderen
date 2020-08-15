# -*- coding: utf-8 -*-
""" Solocoo Auth API """

from __future__ import absolute_import, division, unicode_literals

import json
import logging
import os
import time
import uuid

from requests import HTTPError

from resources.lib.solocoo import TENANTS, SOLOCOO_API, util
from resources.lib.solocoo.exceptions import InvalidLoginException

try:  # Python 3
    import jwt
except ImportError:  # Python 2
    # The package is named pyjwt in Kodi 18: https://github.com/lottaboost/script.module.pyjwt/pull/1
    import pyjwt as jwt

try:  # Python 3
    from urllib.parse import urlparse, parse_qs
except ImportError:  # Python 2
    from urlparse import urlparse, parse_qs

_LOGGER = logging.getLogger(__name__)


class AccountStorage:
    """ Data storage for account info """
    # We will generate a random serial when we don't have any
    device_serial = ''
    device_name = 'Kodi'

    # Challenges we can keep to renew our tokens
    challenge_id = ''
    challenge_secret = ''

    # Cookie token used to authenticate requests to the app
    aspx_token = ''

    # Token used to authenticate a request to the tvapi.solocoo.tv endpoint
    jwt_token = ''

    def is_valid_token(self):
        """ Validate the JWT to see if it's still valid.

        :rtype: boolean
        """
        if not self.jwt_token:
            # We have no token
            return False

        try:
            # Verify our token to see if it's still valid.
            jwt.decode(self.jwt_token,
                       algorithms=['HS256'],
                       options={'verify_signature': False, 'verify_aud': False})
        except Exception as exc:  # pylint: disable=broad-except
            _LOGGER.debug('JWT is NOT valid: %s', exc)
            return False

        return True


class AuthApi:
    """ Solocoo Auth API """

    TOKEN_FILE = 'auth-tokens.json'

    def __init__(self, username, password, tenant, token_path):
        """ Initialisation of the class.

        :param str username:            The username of the account.
        :param str password:            The password of the account.
        :param str tenant:              The tenant code of the account (eg. tvv).
        """
        self._username = username
        self._password = password

        self._tenant = TENANTS.get(tenant)
        if self._tenant is None:
            raise Exception('Invalid tenant: %s' % tenant)

        self._token_path = token_path

        # Load existing account data
        self._account = AccountStorage()
        self._load_cache()

        # Generate device serial if we have none
        if not self._account.device_serial:
            self._account.device_serial = str(uuid.uuid4())
            self._save_cache()

        # self.login()

    def login(self, use_cache=True):
        """ Make a new login request.

        :rtype: AccountStorage
        """
        if not use_cache:
            # Remove the cached tokens
            self.logout()

        # Use cached token if it is still valid
        if self._account.is_valid_token():
            return self._account

        # TODO: when changing the username and password, we need to invalidate the challenge_secret

        if not self._account.challenge_id or not self._account.challenge_secret:
            # We don't have an challenge_id or challenge_secret, so we need to request one

            if self._username and self._password:
                # Do authenticated login
                oauth_code = self._do_login()
                data = dict(
                    autotype='nl',
                    app=self._tenant.get('app'),
                    prettyname=self._account.device_name,
                    model='web',
                    serial=self._account.device_serial,
                    oauthcode=oauth_code,
                    apikey='',
                )
            else:
                # Do anonymous login
                data = dict(
                    autotype='nl',
                    app=self._tenant.get('app'),
                    prettyname=self._account.device_name,
                    model='web',
                    serial=self._account.device_serial,
                )

            reply = util.http_post('https://{domain}/{env}/challenge.aspx'.format(domain=self._tenant.get('domain'),
                                                                                  env=self._tenant.get('env')),
                                   data=data)
            challenge = json.loads(reply.text)
            self._account.challenge_id = challenge.get('id')
            self._account.challenge_secret = challenge.get('secret')

        # Request cookie based on challenge response
        # We will be redirected to https://{domain}/{env}/default.aspx
        try:
            reply = util.http_post(
                'https://{domain}/{env}/login.aspx'.format(domain=self._tenant.get('domain'),
                                                           env=self._tenant.get('env')),
                form=dict(
                    secret=self._account.challenge_id + '\t' + self._account.challenge_secret,
                    uid=self._account.device_serial,
                    app=self._tenant.get('app'),
                )
            )

            # We got redirected, and the last response doesn't contain the cookie we need.
            self._account.aspx_token = reply.history[0].cookies.get('.ASPXAUTH')
        except HTTPError as ex:
            if ex.response.status_code == 402:
                # We could not pick up our session. This probably means that our challenge isn't valid anymore.
                if use_cache:
                    # This isn't an outdated token in the cache. Giving up.
                    raise InvalidLoginException

                # We need to retry the challenge.
                return self.login(False)

        # And finally, get our sapi token by using our stored ASPXAUTH token
        # The sapi token token seems to expires in 30 minutes
        reply = util.http_get('https://{domain}/{env}/capi.aspx?z=ssotoken'.format(domain=self._tenant.get('domain'),
                                                                                   env=self._tenant.get('env')),
                              token_cookie=self._account.aspx_token)
        sso_token = json.loads(reply.text).get('ssotoken')

        # Request JWT token
        # The JWT token also seems to expires in 30 minutes
        reply = util.http_post(SOLOCOO_API + '/session',
                               data=dict(
                                   sapiToken=sso_token,
                                   deviceModel=self._account.device_name,
                                   deviceType="PC",
                                   deviceSerial=self._account.device_serial,
                                   osVersion="Linux undefined",
                                   appVersion="84.0",
                                   memberId="0",
                                   brand=self._tenant.get('app'),
                               ))
        self._account.jwt_token = json.loads(reply.text).get('token')
        self._save_cache()

        return self._account

    def _do_login(self):
        """ Do login with the sso.

        :rtype: string
        """
        # This is probably not necessary for all providers, and this also might need some factory pattern to support
        # other providers.

        # Ask to forward us to the login form.
        util.http_get(
            'https://{domain}/{env}/sso.aspx'.format(domain=self._tenant.get('domain'),
                                                     env=self._tenant.get('env')),
            params=dict(
                a=self._tenant.get('app'),
                s=time.time() * 100,  # unixtime in milliseconds
            )
        )

        # TODO: we could extract the correct url from the form in the html, but this is probably provider dependant anyway.

        # Submit credentials
        reply = util.http_post(
            'https://{auth}/'.format(auth=self._tenant.get('auth')),
            form=dict(
                Username=self._username,
                Password=self._password,
            )
        )

        if 'De gebruikersnaam of het wachtwoord dat u heeft ingegeven is niet correct' in reply.text:
            raise InvalidLoginException

        # Extract query parameters from redirected url
        params = parse_qs(urlparse(reply.url).query)

        return params.get('code')[0]

    def logout(self):
        """ Clear the session tokens. """
        self._account.aspx_token = None
        self._account.jwt_token = None
        self._save_cache()

    def list_entitlements(self):
        """ Fetch a list of entitlements on this account.

        :rtype: dict
        """
        reply = util.http_get(SOLOCOO_API + '/entitlements', token_bearer=self._account.jwt_token)

        entitlements = json.loads(reply.text)

        return dict(
            products=[product.get('id') for product in entitlements.get('products')],
            offers=[offer.get('id') for offer in entitlements.get('offers')],
            assets=[asset.get('id') for asset in entitlements.get('assets')],
        )

    def list_devices(self):
        """ Fetch a list of devices that are registered on this account.

        :rtype: list[dict]
        """
        reply = util.http_get(SOLOCOO_API + '/devices', token_bearer=self._account.jwt_token)

        devices = json.loads(reply.text)
        return devices

    def remove_device(self, uid):
        """ Remove the specified device.

        :param str uid:         The ID of the device to remove.
        """
        util.http_post(SOLOCOO_API + '/devices', token_bearer=self._account.jwt_token,
                       data={
                           'delete': [uid]
                       })

    def _load_cache(self):
        """ Load tokens from cache """
        try:
            with open(os.path.join(self._token_path, self.TOKEN_FILE), 'r') as fdesc:
                self._account.__dict__ = json.loads(fdesc.read())
        except (IOError, TypeError, ValueError):
            _LOGGER.warning('We could not use the cache since it is invalid or non-existent.')

    def _save_cache(self):
        """ Store tokens in cache """
        if not os.path.exists(self._token_path):
            os.makedirs(self._token_path)

        with open(os.path.join(self._token_path, self.TOKEN_FILE), 'w') as fdesc:
            json.dump(self._account.__dict__, fdesc)
