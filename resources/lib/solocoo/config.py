# -*- coding: utf-8 -*-
""" Solocoo API Config """
from __future__ import absolute_import, division, unicode_literals

TENANTS = dict([
    ('tvv', dict(
        name='TV Vlaanderen',
        domain='livetv.tv-vlaanderen.be',
        env='m7be2iphone',
        app='tvv',
    )),
    ('as', dict(
        name='HD Austria',
        domain='livetv.hdaustria.at',
        env='m7be2iphone',
        app='as',
    )),
    ('fsro', dict(
        name='Focus Sat',
        domain='livetv.focussat.ro',
        env='m7cziphone',
        app='fsro',
    )),
    # The following providers are untested
    ('cds', dict(
        name='Canal Digitaal',
        domain='livetv.canaldigitaal.nl',
        env='m7be2iphone',
        app='cds',
    )),
    ('ngt', dict(
        name='NextGenTel',
        domain='nextgentel.tv',
        env='m7be2iphone',
        app='ngt',
    )),
    ('slcz', dict(
        name='Skylink CZ',
        domain='livetv.skylink.cz',
        env='m7be2iphone',
        app='slcz',
    )),
    ('slsk', dict(
        name='Skylink SK',
        domain='livetv.skylink.sk',
        env='m7be2iphone',
        app='slsk',
    )),
    ('tsn', dict(
        name='TéléSat',
        domain='livetv.telesat.be',
        env='m7be2iphone',
        app='tsn',
    )),
    ('tnd', dict(
        name='TriNed',
        domain='livetv.trined.nl',
        env='m7be2iphone',
        app='tnd',
    )),
    ('upchu', dict(
        name='Direct One',
        domain='livetv.directone.hu',
        env='m7be2iphone',
        app='upchu',
    )),
])
