# -*- coding: utf-8 -*-

from app.models import Network
from tests import BaseCase, EXISTING_USER_EMAIL, EXISTING_USER_PASS,\
    EXISTING_NETWORK_ADDRESS, EXISTING_NETWORK_PREFIXLEN

NETWORK_ADDRESS='10.0.0.0'
NETWORK_PREFIXLEN=28

class TestNetworks(BaseCase):
    def test_create_new_network(self):
        self.assertEqual(1, Network.query.count())
        auth = self._gen_auth_headers(EXISTING_USER_EMAIL, EXISTING_USER_PASS)
        response = self.client.post('/networks', headers = [auth], data=dict(
            address=NETWORK_ADDRESS,
            prefixlen=NETWORK_PREFIXLEN
            ))
        self.assert200(response)
        self.assertEqual(response.json, dict(message='success'))

        network = Network.find(NETWORK_ADDRESS, NETWORK_PREFIXLEN).one()
        self.assertEqual(network.network_address, NETWORK_ADDRESS)
        self.assertEqual(network.prefixlen, NETWORK_PREFIXLEN)
        self.assertEqual(2, Network.query.count())

    def test_list_networks(self):
        auth = self._gen_auth_headers(EXISTING_USER_EMAIL, EXISTING_USER_PASS)
        response = self.client.get('/networks', headers = [auth])
        self.assert200(response)

        cidr = '{}/{}'.format(EXISTING_NETWORK_ADDRESS, EXISTING_NETWORK_PREFIXLEN)
        self.assertDictContainsSubset(dict(network=cidr,
            owner=EXISTING_USER_EMAIL),
            response.json['networks'][0])

    def test_list_network(self):
        auth = self._gen_auth_headers(EXISTING_USER_EMAIL, EXISTING_USER_PASS)
        url = '/networks/{}/{}'.format(EXISTING_NETWORK_ADDRESS,
            EXISTING_NETWORK_PREFIXLEN)
        response = self.client.get(url, headers = [auth])
        self.assert200(response)
        self.assertDictContainsSubset(dict(address=EXISTING_NETWORK_ADDRESS,
            prefixlen=EXISTING_NETWORK_PREFIXLEN, owner=EXISTING_USER_EMAIL),
            response.json['network'])

    def test_delete_network(self):
        self.assertEqual(1, Network.query.count())
        url = '/networks/{}/{}'.format(EXISTING_NETWORK_ADDRESS,
            EXISTING_NETWORK_PREFIXLEN)
        auth = self._gen_auth_headers(EXISTING_USER_EMAIL, EXISTING_USER_PASS)
        response = self.client.delete(url, headers = [auth])
        self.assert200(response)
        self.assertEqual(response.json, dict(message='success'))
        self.assertEqual(0, Network.query.count())
