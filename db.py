import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
from platform import system
import wrappers
from flask_marshmallow import Marshmallow



app = Flask(__name__)
wrappers.initialize_error_handlers(app)
current_directory = os.getcwd()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS '] = False
system = system()

# sqlite на бутылку отправлятся через 24 часа на хероку, надо ставить постргрес
#sqlite_connection_string = f'sqlite:////{current_directory}/database.db'
sqlite_connection_string = f'sqlite://// postgresql-clear-67820'
DATABASE_URL = os.environ['DATABASE_URL']
if system == "Windows":
    sqlite_connection_string = f'sqlite:///{current_directory}\\database.db'

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL

Salt = "ser_suhkra"


db = SQLAlchemy(app)
ma = Marshmallow(app)

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
    city = db.Column(db.String(140))
    description = db.Column(db.String(140))
    age = db.Column(db.Integer)
    sex = db.Column(db.String(10))
    long = db.Column(db.Float)
    lat = db.Column(db.Float)
    email = db.Column(db.String(64), index=True, unique=True)
    password = db.Column(db.String(128))
    main_picture_url = db.Column(db.String(128))
    picture_urls = db.relationship('PictureUrl', backref='user', lazy='dynamic')


class PictureUrl(db.Model, Serializer):
    __tablename__ = 'picture_url'
    url = db.Column(db.String(140), unique=True, nullable=False, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('user.id'))



class PictureUrlSchema(ma.SQLAlchemySchema):
    class Meta:
        model = PictureUrl
        fields = ["url"]



class UserSchema(ma.SQLAlchemySchema):
    class Meta:
        model = User
        fields = ("id", "name", "picture_urls", "main_picture_url", "city", "description", "age", "sex", "long", "lat",)

    #picture_urls = ma.List(ma.Nested(PictureUrlSchema))
    picture_urls = ma.Pluck(PictureUrlSchema, "url", many=True)


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
        if d["created_on"]:
            del d["created_on"]
        return d



db.create_all()

def create_simple_data():
    import uuid
    id = uuid.uuid4().hex
    import hashlib
    user = User(id=id,
                 email="mail@mail.ru",
                 password=hashlib.sha256("LYtq2sT6".encode('utf-8')).hexdigest(),
                 name="Xer.ru",
                 city="brata",
                description="brata",
                 age="23",
                 sex="Мужчина",
                 long=-86.1519681,
                 lat=39.7612992,
                main_picture_url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/b68dd7dec11fc8914ab78e93713eaab6d5a8a4ff1022b90ded64cdf0b06213b1.jpg")
    db.session.add(PictureUrl(url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/b68dd7dec11fc8914ab78e93713eaab6d5a8a4ff1022b90ded64cdf0b06213b1.jpg",
                              user_id=user.id))
    db.session.add(PictureUrl(
        url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/122de609b5dc50c6b24d0b2ff2d9e2996d6ca2c0ed22c19d6ea65869204130fe.jpg",
        user_id=user.id))
    db.session.add(PictureUrl(
        url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/138d378e3e7c5219d76369dfe700dab7bdf85ad565f56445b7094cafd8dcd990.jpg",
        user_id=user.id))
    db.session.add(user)
    id = uuid.uuid4().hex
    user = User(id=id,
                 email="mail@mail.com",
                 password=hashlib.sha256("LYtq2sT6".encode('utf-8')).hexdigest(),
                 name="Xer.com",
                 city="brata",
                 age="23",
                 sex="Женщина",
                description="brata",
                 long=-86.158436,
                 lat=39.762241,
                main_picture_url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/1a394516a0af24065def1367f11d6b131b1fc00c4b0e170116ea786c7c0e940e.jpg")
    db.session.add(PictureUrl(
        url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/f4b9d68ae31fc834dc25811867fd2049ffed5810a9a74e8390710a39ed6068b0.jpg",
        user_id=user.id))

    db.session.add(PictureUrl(
        url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/1a394516a0af24065def1367f11d6b131b1fc00c4b0e170116ea786c7c0e940e.jpg",
        user_id=user.id))
    db.session.add(PictureUrl(
        url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/2ed3c5defb1a578c5b4432376c9acbfd9c1a07d60314f8b1ed7672aa37a8d22c.jpg",
        user_id=user.id))
    db.session.add(user)
    id = uuid.uuid4().hex
    user = User(id=id,
                email="mail@mail.de",
                password=hashlib.sha256("LYtq2sT6".encode('utf-8')).hexdigest(),
                name="Xer.de",
                city="brata",
                age="23",
                description="brata",
                sex="Женщина",
                long=-86.148436,
                lat=41.762241,
                main_picture_url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/2f576b87bc5b58bef615471878c0f16c4a3211d181a94c3720f7aa722de5eda3.jpg"
                )
    db.session.add(PictureUrl(
        url = "https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/f636a5e41467e9101b9cbe1ba67f3edd51a697bd6f4ed9d503853986cb8ca5b1.jpg",
        user_id=user.id))
    db.session.add(PictureUrl(
        url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/2f576b87bc5b58bef615471878c0f16c4a3211d181a94c3720f7aa722de5eda3.jpg",
        user_id=user.id))


    db.session.add(user)
    id = uuid.uuid4().hex
    user = User(id=id,
                email="mail@mail.fr",
                password=hashlib.sha256("LYtq2sT6".encode('utf-8')).hexdigest(),
                name="Xer.fr",
                city="brata",
                age="23",
                description="brata",
                 long=-86.258436,
                 lat=39.662241,
                sex="Женщина",
                main_picture_url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/5929d1a7ecd860bf0b6f0b5949a336ed70fd10b94375442f6ec6808bd30d08a3.jpg"
                )
    db.session.add(user)
    db.session.add(PictureUrl(
        url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/5929d1a7ecd860bf0b6f0b5949a336ed70fd10b94375442f6ec6808bd30d08a3.jpg",
        user_id=user.id))
    db.session.add(PictureUrl(
        url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/5b11c9e675ae6bb9c50407cfccab45ee8c192a97e073b196d5d4f93b3576be72.jpg",
        user_id=user.id))
    id = uuid.uuid4().hex
    user = User(id=id,
                email="mail@mail.se",
                password=hashlib.sha256("LYtq2sT6".encode('utf-8')).hexdigest(),
                name="Xer.se",
                description="brata",
                city="brata",
                age="23",
                 long=-86.1519750,
                 lat=39.7622290,
                sex="Мужчина",
                main_picture_url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/181219d9d3be79e0ed68ee74bdd9866596d9591939ddfcd544380e174e432ae3.jpg"
                )
    db.session.add(user)
    db.session.add(PictureUrl(
        url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/181219d9d3be79e0ed68ee74bdd9866596d9591939ddfcd544380e174e432ae3.jpg",
        user_id=user.id))
    db.session.add(PictureUrl(
        url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/6294a617de6ff456fc89e72343491899ffbf1e3607b601c235aa3c720cf2174f.jpg",
        user_id=user.id))
    db.session.add(PictureUrl(
        url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/6509a6e89bb7f3595e65e981beb15eae5a97ef58ebc62b2c0925054878b7a41a.jpg",
        user_id=user.id))
    id = uuid.uuid4().hex
    user = User(id=id,
                 email="mail@mail.da",
                 password=hashlib.sha256("LYtq2sT6".encode('utf-8')).hexdigest(),
                 name="Xer.da",
                 city="brata",
                 description="brata",
                 age="23",
                 long=-86.1578917,
                 lat=39.7622292,
                 sex="Мужчина",
                 main_picture_url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/7e8682d4bc75c57807e00cad0ffe0b7a8161d1537c8bfe8a5340ddb2896e8e85.jpg"
                 )
    db.session.add(user)
    db.session.add(PictureUrl(
        url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/7e8682d4bc75c57807e00cad0ffe0b7a8161d1537c8bfe8a5340ddb2896e8e85.jpg",
        user_id=user.id))

    db.session.add(PictureUrl(
        url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/88571be52a03b7fef4301def71017ecb785d6480082b5ed9dd83fc5898f5ac19.jpg",
        user_id=user.id))
    db.session.add(PictureUrl(
        url="https://raiders3225357-dev.s3.eu-central-1.amazonaws.com/public/9e95ccbaf1c4abe7af34f39265cda62f115438e726eeb0dc9a340a7d63ac7a96.jpg",
        user_id=user.id))
    try:
        db.session.commit()
    except Exception as e:
        print(e)


user_schema = UserSchema(many=True)
user_schema_one = UserSchema()