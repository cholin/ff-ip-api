# -*- coding: utf-8 -*-

from flask import g, url_for, current_app
from ipaddress import ip_address, ip_network
from sqlalchemy.orm import validates, reconstructor
from validate_email import validate_email
from itsdangerous import URLSafeTimedSerializer
from utils import get_prefix_len, hash_password, gen_network, gen_random_hash,\
                  get_max_prefixlen, get_num_addresses
from .exts import db

VALID_NETWORKS = [
    ip_network(u'10.0.0.0/8'),
    ip_network(u'172.16.0.0/12'),
    ip_network(u'192.168.0.0/16')
]

class PasswordTooShortError(ValueError):
    pass

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(128), nullable = False, unique = True)
    password_hash = db.Column(db.String(128), nullable = False)
    token  = db.Column(db.String(128))
    networks = db.relationship('Network', backref='owner', lazy='dynamic',
                               cascade='all')
    verified = db.Column(db.Boolean, default = False)

    def __init__(self, email, password):
        self.email = email
        self.password = password

    @property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, password):
        if len(password) < 6:
            raise PasswordTooShortError

        self.password_hash = hash_password(current_app.config['SALT'], password)
        self.token = gen_random_hash(32)

    @staticmethod
    def auth(email, password):
        hashed_pass = hash_password(current_app.config['SALT'], password)
        try:
            qry = User.query.filter_by(email = email, password_hash=hashed_pass)
            g.user = qry.one()
            return g.user.verified
        except:
            return False

    def verify_signed_token(self, signed_token, namespace, timeout = 3600):
        secret = current_app.config['SECRET']
        serializer = URLSafeTimedSerializer(secret, namespace)
        return self.token == serializer.loads(signed_token, max_age=timeout)

    def gen_signed_token(self, namespace):
        secret = current_app.config['SECRET']
        serializer = URLSafeTimedSerializer(secret, namespace)
        return serializer.dumps(self.token)

    @property
    def verify_namespace(self):
        return 'lost_password' if self.verified else 'registration'

    @property
    def verify_url(self):
        return url_for('.user_verify', email = self.email,
                  token = self.gen_signed_token(self.verify_namespace),
                  _external=True)
    @property
    def name(self):
        return self.email[:self.email.index('@')]

    @validates('email')
    def validate_email(self, key, email):
        assert validate_email(email), "Invalid email"
        return email

    def as_dict(self):
        return {
          'id' : self.id,
          'email' : self.email,
          'networks' : map(lambda n: n.as_dict(exclude_owner=True), self.networks)
        }

    def __repr__(self):
        return '<User {}>'.format(self.email)


class Network(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    address_packed = db.Column(db.BigInteger, nullable = False)
    num_addresses = db.Column(db.Integer, nullable = False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    pinged_at = db.Column(db.DateTime())

    def __init__(self, owner, address, prefixlen = 32):
        self.network = gen_network(address, prefixlen)
        self.address_packed = int(self.network.network_address)
        self.num_addresses = self.network.num_addresses
        self.owner = owner

    @reconstructor
    def init_on_load(self):
        addr = ip_address(self.address_packed)
        prefixlen = get_prefix_len(addr.max_prefixlen, self.num_addresses)
        self.network = gen_network(addr.exploded, prefixlen)

    @validates('address_packed')
    def validate_address_packed(self, key, address_packed):
        msg =  'Only subnetworks of the following networks are allowed {}'.format(
            ', '.join(map(lambda n: str(n), VALID_NETWORKS))
        )
        assert any(map(lambda n: self.network.overlaps(n), VALID_NETWORKS)), msg
        return address_packed

    @staticmethod
    def overlaps_with(address, prefixlen = None):
        if prefixlen is None:
            prefixlen = get_max_prefixlen(address)
        net = gen_network(address, prefixlen)
        addr = int(net.network_address)
        return Network.query.filter(
            Network.address_packed <= addr + net.num_addresses,
            addr <= Network.address_packed + Network.num_addresses)

    @staticmethod
    def next_unused_network(prefixlen, ip_version=4):
        for net in VALID_NETWORKS:
            addr = net.network_address.exploded
            # TODO: use SQLAlchemy with a subquery
            qry = Network.overlaps_with(addr, net.prefixlen)

            if qry.count() == 0:
                return addr

            entries = qry.all()
            pre = entries[0]
            used =  pre.address_packed + pre.num_addresses
            num_addresses = get_num_addresses(prefixlen)
            for current in entries[1:]:
                used =  pre.address_packed + pre.num_addresses
                if used + num_addresses < current.address_packed:
                    break
                else:
                    used =  current.address_packed + current.num_addresses
                pre = current

        return ip_address(used).exploded

    @staticmethod
    def get(address, prefixlen = None):
        if prefixlen is None:
            return Network.overlaps_with(address)
        net = gen_network(address, prefixlen)
        return Network.query.filter_by(address_packed = int(net.network_address),
                                       num_addresses = net.num_addresses)

    @staticmethod
    def get_all(no_networks = False):
        if no_networks:
            return Network.query.filter(Network.num_addresses == 1)

        return Network.query.all()

    @property
    def cidr(self):
        return self.network.exploded

    @property
    def network_address(self):
        return self.network.network_address.exploded

    @network_address.setter
    def network_address(self, address):
        self.network = gen_network(address, self.prefixlen)
        self.address_packed = int(self.network.network_address)

    @property
    def prefixlen(self):
        return self.network.prefixlen

    @prefixlen.setter
    def prefixlen(self, prefixlen):
        self.network = gen_network(self.network_address, prefixlen)
        self.num_addresses = self.network.num_addresses

    def _address_as_dict(self, compact = True):
        ip = self.network.network_address

        data =  {
            'address' : ip.exploded,
            'owner' : self.owner.email,
            'url' : url_for('.networks', address=ip.exploded, _external=True)

        }

        if compact:
            return data

        data.update({
            'is_private': ip.is_private,
            'is_multicast' : ip.is_multicast,
            'is_unspecified': ip.is_unspecified,
            'is_reserverd': ip.is_reserved,
            'version' : ip.version
        })

        return data

    def as_dict(self, compact=True, exclude_owner=False):
        if self.prefixlen == self.network.max_prefixlen:
              return self._address_as_dict(compact)

        data = {
            'network'   : self.cidr,
        }

        if not exclude_owner:
            data['owner'] = self.owner.email

        if compact:
            data['url'] = url_for('.networks', address=self.network_address,
                prefixlen=self.prefixlen, _external=True, _method='GET')
            return data

        data.update({
            'address'   : self.network_address,
            'prefixlen' : self.prefixlen,
            'netmask'   : self.network.netmask.compressed,
            'hosts'     : map(str, self.network.hosts()),
            'broadcast' : self.network.broadcast_address.compressed,
            'is_private': self.network.is_private,
        })

        return data

    def __repr__(self):
        return 'Network({})'.format(self.network.compressed)
