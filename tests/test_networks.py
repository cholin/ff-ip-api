# -*- coding: utf-8 -*-

from app.models import Network
from tests import BaseCase, EXISTING_USER_EMAIL, EXISTING_USER_PASS,\
    EXISTING_NETWORK_ADDRESS, EXISTING_NETWORK_PREFIXLEN, AUTH

NETWORK_ADDRESS=u'10.0.0.0'
NETWORK_PREFIXLEN=28

ADDRESS=u'172.16.0.1'

class TestNetworks(BaseCase):
    def test_create_new_network(self):
        self.assertEqual(1, Network.query.count())
        response = self.client.post('/networks', auth = AUTH, data=dict(
            address=NETWORK_ADDRESS,
            prefixlen=NETWORK_PREFIXLEN
            ))
        self.assert200(response)
        self.assertEqual(response.json, dict(message='success'))

        network = Network.get(NETWORK_ADDRESS, NETWORK_PREFIXLEN).one()
        self.assertEqual(network.network_address, NETWORK_ADDRESS)
        self.assertEqual(network.prefixlen, NETWORK_PREFIXLEN)
        self.assertEqual(2, Network.query.count())

    def test_create_existing_network_failure(self):
        response = self.client.post('/networks', auth = AUTH, data=dict(
            address=EXISTING_NETWORK_ADDRESS,
            prefixlen=29
            ))
        self.assert400(response)
        msg = 'ip address conflict: 192.168.0.0/26'
        self.assertEqual(response.json, dict(error=msg))

    def test_create_new_address(self):
        self.assertEqual(1, Network.query.count())
        response = self.client.post('/networks', auth = AUTH, data=dict(
            address=ADDRESS
            ))
        self.assert200(response)
        self.assertEqual(response.json, dict(message='success'))

        network = Network.get(ADDRESS).one()
        self.assertEqual(network.network_address, ADDRESS)
        self.assertEqual(network.prefixlen, 32)
        self.assertEqual(2, Network.query.count())

    def test_list_networks(self):
        response = self.client.get('/networks', auth = AUTH)
        self.assert200(response)

        cidr = '{}/{}'.format(EXISTING_NETWORK_ADDRESS, EXISTING_NETWORK_PREFIXLEN)
        self.assertDictContainsSubset(dict(network=cidr,
            owner=EXISTING_USER_EMAIL),
            response.json['networks'][0])

    def test_list_network(self):
        url = '/networks/{}/{}'.format(EXISTING_NETWORK_ADDRESS,
            EXISTING_NETWORK_PREFIXLEN)
        response = self.client.get(url, auth = AUTH)
        self.assert200(response)
        self.assertDictContainsSubset(dict(address=EXISTING_NETWORK_ADDRESS,
            prefixlen=EXISTING_NETWORK_PREFIXLEN, owner=EXISTING_USER_EMAIL),
            response.json['network'])

    def test_delete_network(self):
        self.assertEqual(1, Network.query.count())
        url = '/networks/{}/{}'.format(EXISTING_NETWORK_ADDRESS,
            EXISTING_NETWORK_PREFIXLEN)
        response = self.client.delete(url, auth = AUTH)
        self.assert200(response)
        self.assertEqual(response.json, dict(message='success'))
        self.assertEqual(0, Network.query.count())
