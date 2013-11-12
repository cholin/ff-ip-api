# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, abort, request, g, render_template
from flask.views import MethodView
from flask.ext.mail import Message
from itsdangerous import BadTimeSignature
from sqlalchemy.exc import IntegrityError
from socket import error as socket_error
from utils import gen_random_hash, requires_auth, get_max_prefixlen
from models import User, Network, PasswordTooShortError
from .exts import db, mail

api = Blueprint('api', __name__)

class UserAPI(MethodView):
    @requires_auth
    def get(self):
        return jsonify(user=g.user.as_dict())

    def post(self):
        try:
            user = User(request.form['email'], request.form['password'])
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
            db.session.add(user)
            db.session.commit()
            return jsonify(message='success')
        except AssertionError as e:
            error = str(e)
        except IntegrityError:
            error = 'Email already exists'
        except PasswordTooShortError:
            error = 'Password too short'
        except socket_error:
            abort(500)

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
    user = User.query.filter_by(email=email).first_or_404()
    body = render_template('lost_password_request.txt',
              name = user.name, domain = 'ip.berlin.freifunk.net',
              url = user.verify_url)

    msg = Message("Your confirmation is needed!",
              sender="no-reply@ip.berlin.freifunk.net",
              recipients=[user.email],
              body = body)
    mail.send(msg)
    return jsonify(
        message='A confirmation mail has been sent to {}'.format(user.email))


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
                body = render_template('new_password.txt',
                  name = user.name, domain = 'ip.berlin.freifunk.net',
                  new_password = new_password)

                msg = Message("Your new password!",
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
        if address is None or prefixlen is None:
            no_networks = request.args.get('no_networks', type=bool, default=False)
            networks = Network.get_all(no_networks = no_networks)
            return jsonify(networks=map(lambda n: n.as_dict(), networks))

        network = Network.get(address).first_or_404()
        return jsonify(network=network.as_dict(compact=False))

    def post(self):
        if 'address' in request.form:
            address = request.form['address']
            prefixlen = request.form.get('prefixlen', type=int, default=
                            get_max_prefixlen(address))
            try:
                qry = Network.overlaps_with(address, prefixlen)
            except ValueError as e:
                return jsonify( { 'error': str(e) } ), 400

            if qry.count() > 0:
                conflicts = ','.join(map(lambda n: n.cidr, qry.all()))
                msg = 'ip address conflict: {}'.format(conflicts)
                return jsonify( { 'error':  msg} ), 400

        else:
            prefixlen = request.form.get('prefixlen', type=int, default=32)
            address = Network.next_unused_network(prefixlen)

        try:
            network = Network(g.user, address, prefixlen)
            db.session.add(network)
            db.session.commit()
        except AssertionError as e:
            return jsonify( { 'error' : str(e) }), 400

        return jsonify(message='success', network=network.as_dict(compact=False))

    def put(self, address, prefixlen):
        network = Network.get(address, prefixlen).first_or_404()

        if 'address' in request.form:
            network.network_address = request.form['address']

        if 'prefixlen' in request.form:
            network.prefixlen = int(request.form['prefixlen'])

        db.session.commit()

        return jsonify(message='success')

    def delete(self, address, prefixlen):
        network = Network.get(address, prefixlen).first_or_404()
        if network.owner != g.user:
            abort(401)

        db.session.delete(network)
        db.session.commit()
        return jsonify(message='success')


user_view = UserAPI.as_view('user')
api.add_url_rule('/user', view_func=user_view, methods=['GET', 'POST', 'PUT', 'DELETE'])

network_view = requires_auth(NetworkAPI.as_view('networks'))
api.add_url_rule('/networks', defaults={'address': None, 'prefixlen': None},
                         view_func=network_view, methods=['GET',])
api.add_url_rule('/networks', view_func=network_view, methods=['POST',])
api.add_url_rule('/networks/<string:address>', view_func=network_view)
api.add_url_rule('/networks/<string:address>/<int:prefixlen>',
                 view_func=network_view, methods=['GET', 'PUT', 'DELETE'])
