import re
from app.exts import mail
from app.models import User
from tests import BaseCase

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

            url = re.search("(?P<url>https?://[^\s]+)", outbox[0].body).group("url")
            response = self.client.get(url)
            self.assertEqual(response.json, dict(message='success'))

            user = User.query.filter_by(email=USER_MAIL).one()
            self.assertTrue(user.verified)

    def test_existing_email_registration(self):
            response = self.client.post('/user', data=dict(
                email='test@test.de',
                password='test123'
                )
            )
            self.assert400(response)
            self.assertEqual(response.json, dict(message='email already exists'))

