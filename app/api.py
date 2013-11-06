# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, abort, request, g, render_template
from flask.views import MethodView
from flask.ext.mail import Message
from models import User, Network, PasswordTooShortError
from itsdangerous import BadTimeSignature
from utils import gen_random_hash, requires_auth
from .exts import db, mail
from sqlalchemy.exc import IntegrityError

api = Blueprint('api', __name__)

class UserAPI(MethodView):
    @requires_auth
    def get(self):
        return jsonify(user=g.user.as_dict())

    def post(self):
        try:
            user = User(request.form['email'], request.form['password'])
            db.session.add(user)
            db.session.commit()
            body = render_template('registration_confirmation.txt',
                name = user.name,
                url = user.verify_url,
                domain = 'ip.berlin.freifunk.net',
            )

            msg = Message("Your confirmation is needed!",
                      sender="no-reply@ip.berlin.freifunk.net",
                      recipients=[user.email],
                      body = body)
            mail.send(msg)
            return jsonify(message='success')
        except AssertionError:
            error = 'email validation error'
        except IntegrityError:
            error = 'email already exists'
        except PasswordTooShortError:
            error = 'Password too short'

        db.session.rollback()
        return jsonify( { 'message': error } ), 400

    @requires_auth
    def put(self):
        if 'email' in request.form:
            g.user.email = request.form['email']

        if 'password' in request.form:
            g.user.password = request.form['password']

        db.session.add(g.user)
        db.session.commit()
        return jsonify(message='success')

    @requires_auth
    def delete(self):
        db.session.delete(g.user)
        db.session.commit()
        return jsonify(message='success')


@api.route('/users/<string:email>/lost_password')
def user_lost_password(email):
    user = User.query.filter_by(email=email).one()
    body = render_template('lost_password.txt',
              name = user.name, domain = 'ip.berlin.freifunk.net',
              url = user.verify_url)

    msg = Message("Your confirmation is needed!",
              sender="no-reply@ip.berlin.freifunk.net",
              recipients=[user.email],
              body = body)
    mail.send(msg)
    return jsonify(message='success')


@api.route('/users/<string:email>/verify/<string:token>')
def user_verify(email, token):
    user = User.query.filter_by(email=email).one()
    try:
        if user.verify_signed_token(token, user.verify_namespace):
            if user.verify_namespace == 'registration':
                user.verified = True
            else:
                new_password = gen_random_hash(32)
                user.password = new_password
                body = render_template('new_password',
                  name = user.name, domain = 'ip.berlin.freifunk.net',
                  new_password = new_password)

                msg = Message("Your confirmation is needed!",
                          sender="no-reply@ip.berlin.freifunk.net",
                          recipients=[user.email],
                          body = body)
                mail.send(msg)

            db.session.add(user)
            db.session.commit()
            return jsonify(message='success')
    except BadTimeSignature:
        return jsonify( { 'message': 'token does not match' } ), 400

    return jsonify( { 'message': 'error...' } ), 400


class NetworkAPI(MethodView):
    def get(self, address, prefixlen = None):
        if address is None and prefixlen is None:
            networks = Network.query.all()
            return jsonify(networks=map(lambda n: n.as_dict(), networks))
        network = Network.overlaps_with(address).one()
        return jsonify(network=network.as_dict(compact=False))

    def post(self):
        address = request.form['address']
        prefixlen = request.form['prefixlen']

        try:
            qry = Network.overlaps_with(address, prefixlen)
        except ValueError:
            return jsonify( { 'error': 'invalid ip address' } ), 400

        if qry.count() > 0:
            return jsonify( { 'error': 'ip address conflict' } ), 400

        network = Network(address, prefixlen, g.user)
        db.session.add(network)
        db.session.commit()

        return jsonify(message='success')

    def put(self, address, prefixlen):
        network = Network.find(address, prefixlen).one()

        if 'address' in request.form:
            network.network_address = request.form['address']

        if 'prefixlen' in request.form:
            network.prefixlen = request.form['prefixlen']

        db.session.commit()

        return jsonify(message='success')

    def delete(self, address, prefixlen):
        network = Network.find(address, prefixlen).one()
        if network.owner != g.user:
            abort(401)

        db.session.delete(network)
        db.session.commit()
        return jsonify(message='success')


user_view = UserAPI.as_view('user')
api.add_url_rule('/user', view_func=user_view, methods=['GET', 'POST', 'PUT', 'DELETE'])

network_view = requires_auth(NetworkAPI.as_view('ips'))
api.add_url_rule('/ips', defaults={'address': None, 'prefixlen': None},
                         view_func=network_view, methods=['GET',])
api.add_url_rule('/ips', view_func=network_view, methods=['POST',])
api.add_url_rule('/ips/<string:address>', view_func=network_view)
api.add_url_rule('/ips/<string:address>/<int:prefixlen>',
                 view_func=network_view, methods=['GET', 'PUT', 'DELETE'])

