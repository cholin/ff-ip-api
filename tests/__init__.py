# -*- coding: utf-8 -*-

import base64
import re

from flask.ext.testing import TestCase
from flask.testing import FlaskClient
from app.models import User, Network
from app.exts import db
from app import create_app

EXISTING_USER_EMAIL = u'test@test.de'
EXISTING_USER_PASS = u'test123'
EXISTING_NETWORK_ADDRESS='192.168.0.0'
EXISTING_NETWORK_PREFIXLEN=26
AUTH = (EXISTING_USER_EMAIL, EXISTING_USER_PASS)


class TestClient(FlaskClient):
    def _gen_auth_headers(self, email, password):
        return ('Authorization', 'Basic ' + base64.b64encode('{}:{}'.format(
                    email, password)))

    def _add_auth_header(self, args, kwds):
        if 'auth' in kwds:
            email, password = kwds['auth']
            auth = self._gen_auth_headers(email, password)
            if 'headers' not in kwds:
                kwds['headers'] = []
            kwds['headers'].append(auth)
            del kwds['auth']

    def get(self, *args, **kwds):
        self._add_auth_header(args, kwds)
        return super(TestClient, self).get(*args, **kwds)

    def post(self, *args, **kwds):
        self._add_auth_header(args, kwds)
        return super(TestClient, self).post(*args, **kwds)

    def put(self, *args, **kwds):
        self._add_auth_header(args, kwds)
        return super(TestClient, self).put(*args, **kwds)

    def delete(self, *args, **kwds):
        self._add_auth_header(args, kwds)
        return super(TestClient, self).delete(*args, **kwds)


class BaseCase(TestCase):

    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"

    def create_app(self):
        app =  create_app(self)
        app.test_client_class = TestClient
        return app

    def setUp(self):
        db.create_all()

        user = User(EXISTING_USER_EMAIL, EXISTING_USER_PASS)
        user.verified = True
        network = Network(EXISTING_NETWORK_ADDRESS, EXISTING_NETWORK_PREFIXLEN,
            user)
        db.session.add(user)
        db.session.add(network)
        db.session.commit()

    def tearDown(self):
        db.drop_all()

    def _extract_url(self, msg):
        return re.search("(?P<url>https?://[^\s]+)", msg).group("url")

    def _gen_auth_headers(self, email, password):
        return ('Authorization', 'Basic ' + base64.b64encode('{}:{}'.format(
                    email, password)))
