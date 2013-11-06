# -*- coding: utf-8 -*-

from flask import Flask, make_response, jsonify
from .api import api
from .config import DefaultConfig
from .exts import db, mail, migrate

def create_app(config=None):
    """Creates the Flask app."""
    app = Flask(__name__)

    configure_app(app, config)
    configure_extensions(app)
    configure_error_handlers(app)

    for blueprint in [api]:
        app.register_blueprint(blueprint)

    return app


def configure_app(app, config=None):
    """Different ways of configurations."""

    # http://flask.pocoo.org/docs/api/#configuration
    app.config.from_object(DefaultConfig)

    # http://flask.pocoo.org/docs/config/#instance-folders
    app.config.from_pyfile('production.cfg', silent=True)

    if config:
        app.config.from_object(config)


def configure_extensions(app):
    # flask-sqlalchemy
    db.init_app(app)

    # flask-mail
    mail.init_app(app)

    # flask-migrate
    migrate.init_app(app, db)


def configure_error_handlers(app):
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
    def method_not_allowed(e):
        return make_response(jsonify( { 'message': 'Method not allowd' } ), 405)

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return make_response(jsonify( { 'message': 'internal server error' } ), 500)

