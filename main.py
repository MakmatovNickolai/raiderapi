import json
import os
from functools import wraps
from platform import system
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, ForeignKey, String, Column, MetaData, Table, create_engine
import hashlib
import error
from sqlalchemy.inspection import inspect

app = Flask(__name__)
error.initialize_error_handlers(app)
current_directory = os.getcwd()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS '] = False
system = system()
sqlite_connection_string = f'sqlite:////{current_directory}/database.db'
if system == "Windows":
    sqlite_connection_string = f'sqlite:///{current_directory}\\database.db'

app.config['SQLALCHEMY_DATABASE_URI'] = sqlite_connection_string

Salt = "ser_suhkra"
db = SQLAlchemy(app)


class Serializer(object):
    def serialize(self):
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}

    @staticmethod
    def serialize_list(l):
        return [m.serialize() for m in l]


class User(db.Model, Serializer):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), index=True, unique=True)
    password = db.Column(db.String(128))
    contact = db.relationship("Contact", uselist=False, back_populates="user")

    def serialize(self):
        d = Serializer.serialize(self)
        if d["contact"]:
            del d["contact"]
        return d


class Contact(db.Model, Serializer):
    __tablename__ = 'contact'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140))
    surname = db.Column(db.String(140))
    age = db.Column(db.Integer)
    picture_url = db.Column(db.String(140))
    sex = db.Column(db.String(10))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship("User", back_populates="contact")

    def serialize(self):
        d = Serializer.serialize(self)
        if d["user_id"]:
            del d["user_id"]
        if d["user"]:
            del d["user"]
        return d


class AuthedUser(db.Model):
    __tablename__ = 'authed_user'
    user_id = db.Column(db.Integer, primary_key=True)
    auth_token = db.Column(db.String(140))
    user_random_hash = db.Column(db.String(140))


class VisitedProfile(db.Model):
    __tablename__ = 'visited_profile'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    visited_ids = db.Column(db.String(140))


class LikedProfile(db.Model):
    __tablename__ = 'liked_user'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    liked_ids = db.Column(db.String(140))


db.create_all()


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


@app.route('/')
def index():
    return "Hello, World!"


@app.route('/signup', methods=['POST'])
@validate_json
def signup():
    user_json = request.json

    user = User(email=user_json["email"], password=user_json["password"])
    contact = Contact(name=user_json["name"], surname=user_json["surname"], age=user_json["age"], sex=user_json["sex"],
                      picture_url=user_json["picture_url"])
    user.contact = contact
    err = ''
    inp = user.email + user.password + Salt
    inp2 = user.email + Salt
    auth_token = hashlib.sha256(inp.encode('utf-8')).hexdigest()
    user_random_hash = hashlib.sha256(inp2.encode('utf-8')).hexdigest()

    user_random_hash1 = (user_random_hash + "xer").encode('utf-8')
    user_random_hash1 = hashlib.sha256().hexdigest()
    authed_user = AuthedUser(user_id=user.id, auth_token=auth_token, user_random_hash=user_random_hash1)
    db.session.add(authed_user)
    db.session.add(contact)
    db.session.add(user)
    try:
        db.session.commit()
    except DatabaseError as e:
        db.session.rollback()
        err = str(e)
        auth_token = ''
        user_random_hash = ''

    inp = user.email + user.password + Salt
    auth_token = hashlib.sha256(inp.encode('utf-8')).hexdigest()
    return jsonify({'error': err, 'auth_token': auth_token, 'user_random_hash': user_random_hash})


@app.route('/signin', methods=['POST'])
@validate_json
def signin():
    user_json = request.json
    user = db.session.query(User).filter_by(email=user_json["email"]).first()
    err = ''
    auth_token = ''
    user_random_hash = ''
    if user:
        if user.password == user_json["password"]:
            inp = user.email + user.password + Salt
            inp2 = user.email + Salt
            auth_token = hashlib.sha256(inp.encode('utf-8')).hexdigest()
            user_random_hash = hashlib.sha256(inp2.encode('utf-8')).hexdigest()

            user_random_hash1 = (user_random_hash + "xer").encode('utf-8')
            user_random_hash1 = hashlib.sha256().hexdigest()
            authed_user = AuthedUser(user_id=user.id, auth_token=auth_token, user_random_hash=user_random_hash1)
            db.session.add(authed_user)
            try:
                db.session.commit()
            except DatabaseError as e:
                db.session.rollback()
                print(e)
        else:
            err = "Wrong password"
    else:
        err = "No such user"
    return jsonify({'error': err, 'auth_token': auth_token, 'user_random_hash': user_random_hash})


@app.route('/fetch_users', methods=['GET'])
@require_auth_token
def fetch_users():
    err = ''
    result = ''
    user_random_hash = request.args.get('user_random_hash')
    authed_user = db.session.query(AuthedUser).filter_by(user_random_hash=user_random_hash).first()
    if authed_user:
        visited_profiles = db.session.query(VisitedProfile).filter_by(user_id=authed_user.user_id).first()
        if visited_profiles:
            visited_ids = visited_profiles.visited_ids.split(',')
            arr = [u for u in db.session.query(Contact).filter(Contact.id.notin_(visited_ids))]
            result = Contact.serialize_list(arr)
        else:
            result = Contact.serialize_list(db.session.query(Contact).all())
    else:
        err = 'Unexpected error'

    return jsonify({'err': err, 'result': result})


@app.route('/like', methods=['GET'])
@require_auth_token
def like():
    err = ''
    success = False
    liked_id = request.args.get('id')
    user_random_hash = request.args.get('user_random_hash')
    success = True
    authed_user = db.session.query(AuthedUser).filter_by(user_random_hash=user_random_hash).first()
    if authed_user:
        visited_profiles = db.session.query(VisitedProfile).filter_by(user_id=authed_user.user_id).first()
        if visited_profiles:
            visited_i = visited_profiles.visited_ids.split(',')
            visited_i.append(liked_id)
            visited_profiles.visited_ids = ','.join(visited_i)

            liked_profiles = db.session.query(LikedProfile).filter_by(user_id=authed_user.user_id).first()
            if liked_profiles:
                liked_ids = liked_profiles.liked_ids.split(',')
                liked_ids.append(liked_id)
                liked_profiles.liked_ids = ','.join(liked_ids)
            else:
                db.session.add(LikedProfile(user_id=authed_user.user_id, liked_ids=liked_id))
        else:
            db.session.add(VisitedProfile(user_id=authed_user.user_id, visited_ids=liked_id))
            db.session.add(LikedProfile(user_id=authed_user.user_id, liked_ids=liked_id))
        db.session.commit()
    else:
        err = 'unexpected error'
    return jsonify({'error': err, 'success': success})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
