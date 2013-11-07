# -*- coding: utf-8 -*-

import string

from ipaddress import ip_address, ip_network
from hashlib import sha256
from random import choice
from functools import wraps
from flask import request, abort

def get_factors_by(factor, num):
    amount_num_factors = 0
    while(num % factor == 0):
        num //= factor
        amount_num_factors +=1
    return amount_num_factors

def get_prefix_len(max_prefixlen, num_addresses):
    return max_prefixlen-get_factors_by(2, num_addresses)

def hash_password(salt, password):
    return sha256('{}{}'.format(salt, password)).hexdigest()

def gen_network( address, prefixlen):
    return ip_network(u'{}/{}'.format(address, prefixlen))

def get_max_prefixlen(address):
    addr = ip_address(address)
    return addr.max_prefixlen

def gen_random_hash(length):
    digits = string.ascii_letters + string.digits
    return ''.join(choice(digits) for x in range(length))

def requires_auth(f):
    from models import User
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not User.auth(auth.username, auth.password):
            abort(401)
        return f(*args, **kwargs)
    return decorated
