import os
from functools import wraps
from flask import Flask, request, jsonify
import db

def _initialize_errorhandlers(application):
    '''
        Initialize error handlers
    '''
    from error import errors
    application.register_blueprint(errors)
def create_app():
    application = Flask(__name__)

    _initialize_errorhandlers(application)

    db.init_db(application)
    return application

app = create_app()


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

@app.route('/')
def index():
    return "Hello, World!"


@app.route('/signup', methods=['POST'])
@validate_json
def signup():
    data = request.json
    return jsonify(data)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)