'''Application error handlers.'''
from functools import wraps

from flask import Blueprint, jsonify, request
from models.threatstack import ThreatStackError


errors = Blueprint('errors', __name__)


def initialize_error_handlers(application):
    from wrappers import errors
    application.register_blueprint(errors)


@errors.app_errorhandler(ThreatStackError)
def handle_error(error):
    message = [str(x) for x in error.args]
    status_code = 500
    success = False
    response = {
        'success': success,
        'error': {
            'type': error.__class__.__name__,
            'message': message
        }
    }

    return jsonify(response), status_code


@errors.app_errorhandler(Exception)
def handle_unexpected_error(error):
    message = [str(x) for x in error.args]
    status_code = 500
    success = False
    response = {
        'success': success,
        'error': {
            'type': 'UnexpectedException',
            'message': f'An unexpected error has occurred - {message}'
        }
    }

    return jsonify(response), status_code



def validate_json(f):
    @wraps(f)
    def wrapper(*args, **kw):
        try:
            request.json
        except Exception:
            msg = "not a valid json"
            return jsonify({"error": msg}), 400
        return f(*args, **kw)

    return wrapper


def require_auth_token(f):
    @wraps(f)
    def wrapper(*args, **kw):
        auth_header = request.headers.get('Authorization')
        if auth_header:
            auth_token = auth_header.split(" ")[1]
        else:
            auth_token = ''
        if not auth_token:
            return jsonify({"error": "No auth token"})
        return f(*args, **kw)

    return wrapper