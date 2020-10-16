'''Application error handlers.'''
from flask import Blueprint, jsonify
from models.threatstack import ThreatStackError


errors = Blueprint('errors', __name__)


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