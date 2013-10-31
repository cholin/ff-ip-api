from functools import wraps
from flask import jsonify, make_response, request, abort
from models import User
from app import app, db

@app.errorhandler(400)
def bad_request(e):
    return make_response(jsonify( { 'message': 'bad request' } ), 404)

@app.errorhandler(401)
def unauthorized(e):
    return make_response(jsonify( { 'message': 'Unauthorized access' } ), 401,
      {'WWW-Authenticate': 'Basic realm="Login Required"'})

@app.errorhandler(404)
def not_found(e):
    return make_response(jsonify( { 'message': 'Not found' } ), 404)

@app.errorhandler(405)
def not_allowed(e):
    return make_response(jsonify( { 'message': 'Method not allowd' } ), 405)

@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return make_response(jsonify( { 'message': 'internal server error' } ), 500)

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not User.auth(auth.username, auth.password):
            abort(401)
        return f(*args, **kwargs)
    return decorated

