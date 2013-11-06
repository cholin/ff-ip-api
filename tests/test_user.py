# -*- coding: utf-8 -*-

import urllib2
from app.exts import mail
from app.models import User
from tests import BaseCase, EXISTING_USER_EMAIL, EXISTING_USER_PASS

USER_MAIL = 'foo@bar.de'
USER_PASS = 'foobar'

class TestUser(BaseCase):
    def test_unauthorized_access(self):
        response = self.client.get('/user')
        self.assertEqual(response.json, dict(message='Unauthorized access'))

    def test_create_user(self):
        with mail.record_messages() as outbox:
            response = self.client.post('/user', data=dict(
                email = USER_MAIL,
                password = USER_PASS
                )
            )
            self.assert200(response)
            self.assertEqual(response.json, dict(message='success'))

            user = User.query.filter_by(email=USER_MAIL).one()
            self.assertEqual(USER_MAIL, user.email)
            self.assertNotEqual(USER_PASS, user.password)
            self.assertFalse(user.verified)


            self.assertEqual(len(outbox), 1)
            self.assertEqual(outbox[0].subject, 'Your confirmation is needed!')

            response = self.client.get(self._extract_url(outbox[0].body))
            self.assertEqual(response.json, dict(message='success'))

            user = User.query.filter_by(email=USER_MAIL).one()
            self.assertTrue(user.verified)

    def test_create_user_with_existing_email(self):
        response = self.client.post('/user', data=dict(
            email=EXISTING_USER_EMAIL,
            password=USER_PASS
            )
        )
        self.assert400(response)
        self.assertEqual(response.json, dict(message='email already exists'))

    def test_reset_password(self):
        with mail.record_messages() as outbox:
            email = urllib2.quote(EXISTING_USER_EMAIL)
            response = self.client.get('/users/{}/lost_password'.format(email))
            self.assert200(response)
            self.assertEqual(response.json, dict(
              message='A confirmation mail has been sent to {}'\
              .format(EXISTING_USER_EMAIL)))

            self.assertEqual(len(outbox), 1)
            self.assertEqual(outbox[0].subject, 'Your confirmation is needed!')

            response = self.client.get(self._extract_url(outbox[0].body))
            self.assertEqual(response.json, dict(message='success'))
            self.assertEqual(len(outbox), 2)
            self.assertEqual(outbox[1].subject, 'Your new password!')
            self.assertFalse(User.auth(EXISTING_USER_EMAIL, EXISTING_USER_PASS))

    def test_list_user(self):
        auth = self._gen_auth_headers(EXISTING_USER_EMAIL, EXISTING_USER_PASS)
        response = self.client.get('/user', headers = [auth])
        self.assertDictContainsSubset(dict(email=EXISTING_USER_EMAIL),
            response.json['user'])

    def test_delete_user(self):
        self.assertEqual(1, User.query.count())

        auth = self._gen_auth_headers(EXISTING_USER_EMAIL, EXISTING_USER_PASS)
        response = self.client.delete('/user', headers = [auth])

        self.assert200(response)
        self.assertEqual(0, User.query.count())
