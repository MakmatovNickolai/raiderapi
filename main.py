import os
from functools import wraps
from platform import system

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, ForeignKey, String, Column

import error


app = Flask(__name__)
error.initialize_error_handlers(app)
current_directory = os.getcwd()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS '] = False
system = system()
if system == "Windows":
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{current_directory}\\database.db'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:////{current_directory}/database.db'
db = SQLAlchemy(app)
db.create_all()

Base = declarative_base()


class Contact(Base):
    __tablename__ = 'contact'
    id = Column(Integer, primary_key=True)
    name = Column(String(140))
    surname = Column(String(140))
    age = Column(Integer)

    def __repr__(self):
        return '<Contact {}>'.format(self.name)


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    email = Column(String(64), index=True, unique=True)
    password = Column(String(128))
    contact_id = Column(Integer, ForeignKey('contact.id'))
    contact = relationship("Contact")

    def __repr__(self):
        return '<User {}>'.format(self.email)


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
    user_json = request.json
    contact = Contact(name=user_json["name"], surname=user_json["surname"], age=user_json["age"])
    user = User(email=user_json["email"], password=user_json["password"])
    user.contact = contact

    db.session.add(contact)
    db.session.add(user)
    db.session.commit()
    return "Success"


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)