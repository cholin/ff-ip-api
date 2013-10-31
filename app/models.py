from flask import g, url_for
from ipaddress import ip_address
from sqlalchemy.orm import validates, reconstructor
from validate_email import validate_email
from utils import get_prefix_len, hash_password, gen_network
from app import db, SALT

class PasswordTooShortError(ValueError):
    pass

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(128), nullable = False, unique = True)
    password_hash = db.Column(db.String(128), nullable = False)
    networks = db.relationship('Network', backref='owner', lazy='dynamic',
                               cascade='all')

    def __init__(self, email, password):
        self.email = email
        self.password = password

    @property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, password):
        if len(password) < 6:
            from errors import PasswordTooShortError
            raise PasswordTooShortError

        self.password_hash = hash_password(SALT, password)

    @staticmethod
    def auth(email, password):
        hashed_pass = hash_password(SALT, password)
        try:
            qry = User.query.filter_by(email = email, password_hash=hashed_pass)
            g.user = qry.one()
            return True
        except:
            return False

    @validates('email')
    def validate_email(self, key, email):
        assert validate_email(email), "Invalid email"
        return email

    def as_dict(self):
        return {
          'id' : self.id,
          'email' : self.email,
          'ips' : map(lambda n: n.as_dict(exclude_owner=True), self.networks)
        }

    def __repr__(self):
        return '<User {}>'.format(self.email)


class Network(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    address_packed = db.Column(db.BigInteger, nullable = False)
    num_addresses = db.Column(db.Integer, nullable = False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)

    def __init__(self, address, prefixlen, owner):
        self.network = gen_network(address, prefixlen)
        self.address_packed = int(self.network.network_address)
        self.num_addresses = self.network.num_addresses
        self.owner = owner

    @reconstructor
    def init_on_load(self):
        addr = ip_address(self.address_packed)
        prefixlen = get_prefix_len(addr.max_prefixlen, self.num_addresses)
        self.network = gen_network(addr.exploded, prefixlen)

    @staticmethod
    def overlaps_with(address, prefixlen = 32):
        net = gen_network(address, prefixlen)
        addr = int(net.network_address)
        num_addr = net.num_addresses
        return Network.query.filter(Network.address_packed <= addr)\
                            .filter(addr + num_addr <=\
                                    Network.address_packed + Network.num_addresses)

    @staticmethod
    def find(address, prefixlen):
        net = gen_network(address, prefixlen)
        return Network.query.filter_by(address_packed = int(net.network_address),
                                       num_addresses = net.num_addresses)

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

    def as_dict(self, compact=True, exclude_owner=False):
        data = {
            'network'   : self.cidr,
        }

        if not exclude_owner:
            data['owner'] = self.owner.email

        if compact:
            data['url'] = url_for('ips', address=self.network_address,
                              prefixlen=self.prefixlen, _external=True)
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
