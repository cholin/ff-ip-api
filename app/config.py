# -*- coding: utf-8 -*-

import os

class DefaultConfig(object):

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.dirname(__file__), '..', 'app.db')
    SALT = '<enter your salt here>'
    SECRET = '<enter your secret here>'
    MAIL_PORT = 1025
