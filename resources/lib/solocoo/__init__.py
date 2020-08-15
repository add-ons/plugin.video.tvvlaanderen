# -*- coding: utf-8 -*-
""" Solocoo API """
from __future__ import absolute_import, division, unicode_literals

SOLOCOO_API = 'https://tvapi.solocoo.tv/v1'

TENANTS = dict([
    ('tvv', dict(
        name='TV Vlaanderen',
        domain='livetv.tv-vlaanderen.be',
        auth='login.tv-vlaanderen.be',
        env='m7be2iphone',
        app='tvv',
    )),
    ('cds', dict(
        name='Canal Digitaal',
        domain='livetv.canaldigitaal.nl',
        auth='login.canaldigitaal.nl',
        env='m7be2iphone',
        app='cds',
    )),
    # and many more, ...
])
