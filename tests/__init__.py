from flask.ext.testing import TestCase
from app.models import User
from app.exts import db
from app import create_app

EXISTING_USER_EMAIL = u'test@test.de'
EXISTING_USER_PASS = u'test123'

class BaseCase(TestCase):

    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"

    def create_app(self):
        return create_app(self)

    def setUp(self):
        db.create_all()
        user = User(email=EXISTING_USER_EMAIL,password=EXISTING_USER_PASS)
        db.session.add(user)
        db.session.commit()

    def tearDown(self):
        db.drop_all()

    def test_auch(self):
        self.assertEqual(True, True)
