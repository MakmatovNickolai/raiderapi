import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
from platform import system
import wrappers

app = Flask(__name__)
wrappers.initialize_error_handlers(app)
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
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String(140))
    surname = db.Column(db.String(140))
    age = db.Column(db.Integer)
    picture_url = db.Column(db.String(140))
    sex = db.Column(db.String(10))
    long = db.Column(db.Float)
    lat = db.Column(db.Float)
    email = db.Column(db.String(64), index=True, unique=True)
    password = db.Column(db.String(128))

    def serialize(self):
        d = Serializer.serialize(self)
        if d["password"]:
            del d["password"]
        if d["email"]:
            del d["email"]
        return d


class AuthedUser(db.Model):
    __tablename__ = 'authed_user'
    id = db.Column(db.Integer, primary_key=True)
    auth_token = db.Column(db.String(140))
    user_random_hash = db.Column(db.String(140))
    user_id = db.Column(db.String, db.ForeignKey('user.id'))
    user = db.relationship(User)


class SwipeRight(db.Model):
    __tablename__ = 'swipe_right'
    id = db.Column(db.Integer, primary_key=True)
    swiper_id = db.Column(db.String, db.ForeignKey('user.id'))
    target_id = db.Column(db.String, db.ForeignKey('user.id'))
    target = db.relationship(User, foreign_keys=[target_id])
    swiper = db.relationship(User, foreign_keys=[swiper_id])
    created_on = db.Column(db.DateTime)


class SwipeLeft(db.Model):
    __tablename__ = 'swipe_left'
    id = db.Column(db.Integer, primary_key=True)
    swiper_id = db.Column(db.String, db.ForeignKey('user.id'))
    target_id = db.Column(db.String, db.ForeignKey('user.id'))
    target = db.relationship(User, foreign_keys=[target_id])
    swiper = db.relationship(User, foreign_keys=[swiper_id])
    created_on = db.Column(db.DateTime)


class Match(db.Model):
    __tablename__ = 'match'
    id = db.Column(db.Integer, primary_key=True)
    first_user_id = db.Column(db.String, db.ForeignKey('user.id'))
    second_user_id = db.Column(db.String, db.ForeignKey('user.id'))
    first_user = db.relationship(User, foreign_keys=[first_user_id])
    second_user = db.relationship(User, foreign_keys=[second_user_id])
    created_on = db.Column(db.DateTime)


class Room(db.Model, Serializer):
    __tablename__ = 'room'
    id = db.Column(db.String, primary_key=True)
    unique_users_id = db.Column(db.String)
    opened_by_id = db.Column(db.String, db.ForeignKey('user.id'))
    opened_by = db.relationship(User)

    def serialize(self):
        d = Serializer.serialize(self)
        if d["opened_by"]:
            del d["opened_by"]
        return d


class RoomUserRecord(db.Model):
    __tablename__ = 'room_user_record'
    id = db.Column(db.String, primary_key=True)
    room_id = db.Column(db.String, db.ForeignKey('room.id'))
    room = db.relationship(Room)
    user_id = db.Column(db.String, db.ForeignKey('user.id'))
    user = db.relationship(User, foreign_keys=[user_id])
    target_user_id = db.Column(db.String, db.ForeignKey('user.id'))
    target_user = db.relationship(User, foreign_keys=[target_user_id])


    def serialize(self):
        d = Serializer.serialize(self)
        return d


class Message(db.Model, Serializer):
    __tablename__ = 'message'
    id = db.Column(db.String, primary_key=True)
    message = db.Column(db.String)
    from_user_id = db.Column(db.String)
    room_id = db.Column(db.String, db.ForeignKey('room.id'))
    room = db.relationship("Room")
    created_on = db.Column(db.DateTime)

    def serialize(self):
        d = Serializer.serialize(self)
        if d["room"]:
            del d["room"]
        return d



db.create_all()

def create_simple_data():
    import uuid
    id = uuid.uuid4().hex
    import hashlib
    user1 = User(id=id,
                email="mail@mail.ru",
                password=hashlib.sha256("LYtq2sT6".encode('utf-8')).hexdigest(),
                name="Xer.ru",
                surname="brata",
                age="23",
                sex="female",
                picture_url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/b68dd7dec11fc8914ab78e93713eaab6d5a8a4ff1022b90ded64cdf0b06213b1.jpg",
                 long =-86.1519681,
                 lat=39.7612992)

    db.session.add(user1)
    id = uuid.uuid4().hex
    user2 = User(id=id,
                email="mail@mail.com",
                password=hashlib.sha256("LYtq2sT6".encode('utf-8')).hexdigest(),
                name="Xer.com",
                surname="brata",
                age="23",
                sex="female",
                 long=-86.158436,
                 lat=39.762241,
                picture_url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/f4b9d68ae31fc834dc25811867fd2049ffed5810a9a74e8390710a39ed6068b0.jpg")
    db.session.add(user2)
    id = uuid.uuid4().hex
    user5 = User(id=id,
                email="mail@mail.de",
                password=hashlib.sha256("LYtq2sT6".encode('utf-8')).hexdigest(),
                name="Xer.de",
                surname="brata",
                age="23",
                sex="female",
                 long=-86.148436,
                 lat=41.762241,
                picture_url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/f636a5e41467e9101b9cbe1ba67f3edd51a697bd6f4ed9d503853986cb8ca5b1.jpg")
    db.session.add(user5)
    id = uuid.uuid4().hex
    user3 = User(id=id,
                email="mail@mail.fr",
                password=hashlib.sha256("LYtq2sT6".encode('utf-8')).hexdigest(),
                name="Xer.fr",
                surname="brata",
                age="23",
                 long=-86.258436,
                 lat=39.662241,
                sex="female",
                picture_url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/88571be52a03b7fef4301def71017ecb785d6480082b5ed9dd83fc5898f5ac19.jpg")
    db.session.add(user3)
    id = uuid.uuid4().hex
    user4 = User(id=id,
                email="mail@mail.se",
                password=hashlib.sha256("LYtq2sT6".encode('utf-8')).hexdigest(),
                name="Xer.se",
                surname="brata",
                age="23",
                 long=-86.1519750,
                 lat=39.7622290,
                sex="female",
                picture_url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/181219d9d3be79e0ed68ee74bdd9866596d9591939ddfcd544380e174e432ae3.jpg")
    db.session.add(user4)
    id = uuid.uuid4().hex
    user4 = User(id=id,
                 email="mail@mail.da",
                 password=hashlib.sha256("LYtq2sT6".encode('utf-8')).hexdigest(),
                 name="Xer.da",
                 surname="brata",
                 age="23",
                 long=-86.1578917,
                 lat=39.7622292,
                 sex="female",
                 picture_url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/7e8682d4bc75c57807e00cad0ffe0b7a8161d1537c8bfe8a5340ddb2896e8e85.jpg")
    db.session.add(user4)
    try:
        db.session.commit()
    except Exception:
        print("xz")
