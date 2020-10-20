import json
import os
from functools import wraps
from platform import system
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, sessionmaker
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

engine = create_engine(sqlite_connection_string)

Base = declarative_base(engine)
Salt ="ser_suhkra"


class Serializer(object):
    def serialize(self):
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}

    @staticmethod
    def serialize_list(l):
        return [m.serialize() for m in l]


class Contact(Base, Serializer):
    __tablename__ = 'contact'
    id = Column(Integer, primary_key=True)
    name = Column(String(140))
    surname = Column(String(140))
    age = Column(Integer)

    def __repr__(self):
        return '<Contact {}>'.format(self.name)


class AuthedUser(Base):
    __tablename__ = 'authed_user'
    user_id = Column(Integer, primary_key=True)
    auth_token = Column(String(140))
    user_random_hash = Column(String(140))


class VisitedProfile(Base):
    __tablename__ = 'visited_profile'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    visited_ids = Column(String(140))


class LikedProfile(Base):
    __tablename__ = 'liked_user'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    liked_ids = Column(String(140))


class User(Base, Serializer):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    email = Column(String(64), index=True, unique=True)
    password = Column(String(128))
    contact_id = Column(Integer, ForeignKey('contact.id'))
    contact = relationship("Contact")

    def serialize(self):
        d = Serializer.serialize(self)
        if d["contact"]:
            del d["contact"]
        return d

    def __repr__(self):
        return '<User {}>'.format(self.email)


Base.metadata.create_all(engine)
Session = sessionmaker(engine)
session = Session()


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
    contact = Contact(name=user_json["name"], surname=user_json["surname"], age=user_json["age"])
    user = User(email=user_json["email"], password=user_json["password"])
    user.contact = contact

    session.add(contact)
    session.add(user)
    session.commit()

    err = ''
    inp = user.email + user.password + Salt
    auth_token = hashlib.sha256(inp.encode('utf-8')).hexdigest()
    return jsonify({'error': err, 'auth_token': auth_token})


@app.route('/signin', methods=['POST'])
@validate_json
def signin():
    user_json = request.json
    user = session.query(User).filter_by(email=user_json["email"]).first()
    err = ''
    auth_token = ''

    if user:
        if user.password == user_json["password"]:
            inp = user.email + user.password + Salt
            inp2 = user.email + Salt
            auth_token = hashlib.sha256(inp.encode('utf-8')).hexdigest()
            user_random_hash = hashlib.sha256(inp2.encode('utf-8')).hexdigest()
            user_random_hash = hashlib.sha256(user_random_hash + "xer".encode('utf-8')).hexdigest()
            authed_user = AuthedUser(user_id=user.id, auth_token=auth_token, user_random_hash=user_random_hash)
            session.add(authed_user)
            session.commit()
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
    authed_user = session.query(AuthedUser).filter_by(user_random_hash=user_random_hash).first()
    if authed_user:
        visited_profiles = session.query(VisitedProfile).filter_by(user_id=authed_user.user_id).first()
        if visited_profiles:
            visited_ids = visited_profiles.visited_ids.split(',')
            arr = [u for u in session.query(User).filter(User.id.notin_(visited_ids))]
            result = User.serialize_list(arr)
        else:
            result = User.serialize_list(session.query(User).all())
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
    authed_user = session.query(AuthedUser).filter_by(user_random_hash=user_random_hash).first()
    if authed_user:
        visited_profiles = session.query(VisitedProfile).filter_by(user_id=authed_user.user_id).first()
        if visited_profiles:
            visited_i = visited_profiles.visited_ids.split(',')
            visited_i.append(liked_id)
            visited_profiles.visited_ids = ','.join(visited_i)

            liked_profiles = session.query(LikedProfile).filter_by(user_id=authed_user.user_id).first()
            if liked_profiles:
                liked_ids = liked_profiles.liked_ids.split(',')
                liked_ids.append(liked_id)
                liked_profiles.liked_ids = ','.join(liked_ids)
            else:
                session.add(LikedProfile(user_id=authed_user.user_id, liked_ids=liked_id))
        else:
            session.add(VisitedProfile(user_id=authed_user.user_id, visited_ids=liked_id))
            session.add(LikedProfile(user_id=authed_user.user_id, liked_ids=liked_id))
        session.commit()
    else:
        err = 'unexpected error'
    return jsonify({'error': err, 'success': success})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)