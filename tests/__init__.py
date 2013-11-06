# -*- coding: utf-8 -*-

import base64

from flask.ext.testing import TestCase
from app.models import User, Network
from app.exts import db
from app import create_app

EXISTING_USER_EMAIL = u'test@test.de'
EXISTING_USER_PASS = u'test123'
EXISTING_NETWORK_ADDRESS='192.168.0.0'
EXISTING_NETWORK_PREFIXLEN=26

class BaseCase(TestCase):

    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"

    def create_app(self):
        return create_app(self)

    def setUp(self):
        db.create_all()

        user = User(EXISTING_USER_EMAIL, EXISTING_USER_PASS)
        network = Network(EXISTING_NETWORK_ADDRESS, EXISTING_NETWORK_PREFIXLEN,
            user)
        db.session.add(user)
        db.session.add(network)
        db.session.commit()

    def tearDown(self):
        db.drop_all()

    def _gen_auth_headers(self, email, password):
        return ('Authorization', 'Basic ' + base64.b64encode('{}:{}'.format(
                    email, password)))
