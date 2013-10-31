from flask import jsonify, abort, request, g
from flask.views import MethodView
from models import User, Network, PasswordTooShortError
from errors import requires_auth
from app import app, db
from sqlalchemy.exc import IntegrityError

class UserAPI(MethodView):
    @requires_auth
    def get(self):
        return jsonify(user=g.user.as_dict())

    def post(self):
        try:
            user = User(request.form['email'], request.form['password'])
            db.session.add(user)
            db.session.commit()
            return jsonify(result='success')
        except AssertionError:
            error = 'email validation error'
        except IntegrityError:
            error = 'email already exists'
        except PasswordTooShortError:
            error = 'Password too short'

        return jsonify( { 'message': error } ), 400

    @requires_auth
    def put(self):
        if 'email' in request.form:
            g.user.email = request.form['email']

        if 'password' in request.form:
            g.user.password = request.form['password']

        db.session.add(g.user)
        db.session.commit()
        return jsonify(result='success')

    @requires_auth
    def delete(self):
        db.session.delete(g.user)
        db.session.commit()
        return jsonify(result='success')


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

        return jsonify(result='success')

    def put(self, address, prefixlen):
        network = Network.find(address, prefixlen).one()

        if 'address' in request.form:
            network.network_address = request.form['address']

        if 'prefixlen' in request.form:
            network.prefixlen = request.form['prefixlen']

        db.session.commit()

        return jsonify(result='success')

    def delete(self, address, prefixlen):
        network = Network.find(address, prefixlen).one()
        if network.owner != g.user:
            abort(401)

        db.session.delete(network)
        db.session.commit()
        return jsonify(result='success')


user_view = UserAPI.as_view('user')
app.add_url_rule('/user', view_func=user_view, methods=['GET', 'POST', 'PUT', 'DELETE'])

network_view = requires_auth(NetworkAPI.as_view('ips'))
app.add_url_rule('/ips', defaults={'address': None, 'prefixlen': None},
                         view_func=network_view, methods=['GET',])
app.add_url_rule('/ips', view_func=network_view, methods=['POST',])
app.add_url_rule('/ips/<string:address>', view_func=network_view)
app.add_url_rule('/ips/<string:address>/<int:prefixlen>',
                 view_func=network_view, methods=['GET', 'PUT', 'DELETE'])

