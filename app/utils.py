from ipaddress import ip_network
from hashlib import sha256

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
