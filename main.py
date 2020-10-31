import uuid
from datetime import datetime

from flask import request, jsonify
from sqlalchemy.exc import DatabaseError
import hashlib

from config import pusher_client
from db import *
from utils import *
from wrappers import validate_json, require_auth_token


@app.route('/')
def index():
    return "Hello, World!"


@app.route('/sign_up', methods=['POST'])
@validate_json
def sign_up():
    user_json = request.json
    user = User(id=user_json['id'],
                email=user_json['email'],
                password=user_json["password"],
                name=user_json["name"],
                surname=user_json["surname"],
                age=user_json["age"],
                sex=user_json["sex"],
                picture_url=user_json["picture_url"])
    err = ''
    inp = user.email + user.password + Salt
    inp2 = user.email + Salt
    auth_token = hashlib.sha256(inp.encode('utf-8')).hexdigest()
    user_random_hash = hashlib.sha256(inp2.encode('utf-8')).hexdigest()

    user_random_hash1 = (user_random_hash + "xer").encode('utf-8')
    user_random_hash1 = hashlib.sha256(user_random_hash1).hexdigest()
    authed_user = AuthedUser(auth_token=auth_token, user_random_hash=user_random_hash1)
    authed_user.user = user
    db.session.add(authed_user)
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


@app.route('/sign_in', methods=['POST'])
@validate_json
def sign_in():
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
            user_random_hash1 = hashlib.sha256(user_random_hash1).hexdigest()
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


@app.route('/sign_out', methods=['GET'])
@validate_json
def sign_out():
    user_random_hash = request.args.get('user_random_hash')
    authed_user = db.session.query(AuthedUser).filter_by(user_random_hash=user_random_hash).first()
    err = ''
    result = ''
    if authed_user:
        db.session.delete(authed_user)
        db.session.commit()
        result = 'OK'
    else:
        err = "Unexpected error"
    return jsonify({'error': err, 'result': result})


@app.route('/fetch_users', methods=['GET'])
@require_auth_token
def fetch_users():
    err = ''
    result = ''
    user_random_hash = request.args.get('user_random_hash')
    authed_user = db.session.query(AuthedUser).filter_by(user_random_hash=user_random_hash).first()
    if authed_user:
        
        right_ids = [r.target_id for r in
                     db.session.query(SwipeRight.target_id).filter_by(swiper_id=authed_user.user_id).all()]
        left_ids = [r.target_id for r in
                    db.session.query(SwipeLeft.target_id).filter_by(swiper_id=authed_user.user_id).all()]




        # возвращаем тех, кого не свайпали влево или вправо и не себя
        users_list = right_ids + left_ids
        if authed_user.user_id not in users_list:
            users_list.append(authed_user.user_id)

        # супер не оптимизированно, но пох
        users = db.session.query(User).filter(User.id.notin_(users_list)).all()

        me = db.session.query(User).filter_by(id=authed_user.user_id).first()

        # тотально медленно
        closest_users = closest(users, me)

        result = User.serialize_list(closest_users)
    else:
        err = 'Unexpected error'

    return jsonify({'err': err, 'result': result})


@app.route('/get_matches', methods=['GET'])
@require_auth_token
def get_matches():
    err = ''
    result = ''
    user_random_hash = request.args.get('user_random_hash')
    match_type = request.args.get('type')
    authed_user = db.session.query(AuthedUser).filter_by(user_random_hash=user_random_hash).first()
    if authed_user:
        if match_type == "both":
            u = db.aliased(User)
            matched_users = Match.query \
                .join(u, u.id == Match.second_user_id) \
                .with_entities(u) \
                .filter(Match.first_user_id == authed_user.user_id) \
                .all()
            result = User.serialize_list(matched_users)
        if match_type == "one":
            sub_query = db.session.query(SwipeRight.target_id).filter_by(swiper_id=authed_user.user_id).subquery()
            u = db.aliased(User)
            swiped_me_right_users = db.session.query(SwipeRight) \
                .join(u, u.id == SwipeRight.swiper_id) \
                .with_entities(u) \
                .filter(SwipeRight.swiper_id.notin_(sub_query), SwipeRight.target_id == authed_user.user_id) \
                .all()
            result = User.serialize_list(swiped_me_right_users)
    else:
        err = 'Unexpected error'

    return jsonify({'err': err, 'result': result})


@app.route('/like', methods=['GET'])
@require_auth_token
def like():
    err = ''
    target_id = request.args.get('id')
    is_liked = request.args.get('like')
    user_random_hash = request.args.get('user_random_hash')
    is_match = False
    authed_user = db.session.query(AuthedUser).filter_by(user_random_hash=user_random_hash).first()
    if authed_user:
        if is_liked == "1":
            db.session.add(SwipeRight(swiper_id=authed_user.user_id, target_id=target_id, created_on=datetime.now()))
            has_match = db.session.query(SwipeRight).filter_by(swiper_id=target_id,
                                                               target_id=authed_user.user_id).first()
            if has_match:
                match1 = Match(first_user_id=target_id, second_user_id=authed_user.user_id, created_on=datetime.now())
                match2 = Match(first_user_id=authed_user.user_id, second_user_id=target_id, created_on=datetime.now())
                db.session.add(match1)
                db.session.add(match2)
                is_match = True
        else:
            db.session.add(SwipeLeft(swiper_id=authed_user.user_id, target_id=target_id, created_on=datetime.now()))
        db.session.commit()
    else:
        err = 'unexpected error'
    return jsonify({'error': err, 'is_match': is_match})


@app.route('/fetch_rooms', methods=['GET'])
@require_auth_token
def fetch_rooms():
    err = ''
    result = []
    user_random_hash = request.args.get('user_random_hash')
    authed_user = db.session.query(AuthedUser).filter_by(user_random_hash=user_random_hash).first()
    room = ''
    user = ''
    last_messages = ''
    if authed_user:
        # подзапрос, чтобы вытащить последнее сообщение в беседе
        sub_query = db.session.query(db.func.max(Message.created_on), Message.message, Message.room_id) \
            .group_by(Message.room_id).subquery()

        # алиасы для запроса
        r, u = db.aliased(Room), db.aliased(User)

        # запрос на получение комнаты, пользователя-собеседника и последнего сообщения
        room_user_records = RoomUserRecord.query \
            .join(r, r.id == RoomUserRecord.room_id) \
            .join(u, u.id == RoomUserRecord.target_user_id) \
            .outerjoin(sub_query, sub_query.c.room_id == RoomUserRecord.room_id) \
            .with_entities(r, u, sub_query) \
            .filter(RoomUserRecord.user_id == authed_user.user_id).all()

        print(room_user_records)
        for (z, y, message_created_on, message, room_id) in room_user_records:
            d = {}
            if z is not None:
                d["room"] = Room.serialize(z)
            if y is not None:
                d["user"] = User.serialize(y)
            if message is not None:
                d["last_message"] = message
            result.append(d)
    else:
        err = 'Unexpected error'

    return jsonify({'err': err, 'result': result})


@app.route('/send_message', methods=['POST'])
@validate_json
def send_message():
    user_json = request.json
    err = ''
    success = True
    user_random_hash = request.args.get('user_random_hash')
    authed_user = db.session.query(AuthedUser).filter_by(user_random_hash=user_random_hash).first()
    if authed_user:
        message = Message(id=user_json["id"], message=user_json["message"], from_user_id=authed_user.user_id,
                room_id=user_json["room_id"], created_on=datetime.now())
        db.session.add(message)
        db.session.commit()
        pusher_client.trigger('raider', 'new_message', {'message': Message.serialize(message)})
    else:
        err = 'Unexpected error'
        success = False
    return jsonify({'error': err, 'result': success})


@app.route('/fetch_messages', methods=['GET'])
@require_auth_token
def fetch_messages():
    err = ''
    result = ''
    user_random_hash = request.args.get('user_random_hash')
    room_id = request.args.get('room_id')
    authed_user = db.session.query(AuthedUser).filter_by(user_random_hash=user_random_hash).first()
    if authed_user:

        messages = db.session.query(Message).filter_by(room_id=room_id).all()
        result = Message.serialize_list(messages)
        print(result)
    else:
        err = 'Unexpected error'

    return jsonify(result)


@app.route('/update_location', methods=['GET'])
@require_auth_token
def update_location():
    err = ''
    result = ''
    user_random_hash = request.args.get('user_random_hash')
    long = request.args.get('long')
    lat = request.args.get('lat')
    authed_user = db.session.query(AuthedUser).filter_by(user_random_hash=user_random_hash).first()
    if authed_user:
        user = db.session.query(User).filter_by(id=authed_user.user_id).first()
        user.long = long
        user.lat = lat
        db.session.commit()
    else:
        err = 'Unexpected error'

    return jsonify(result)


@app.route('/create_room', methods=['GET'])
@require_auth_token
def create_room():
    err = ''
    result = ''
    user_random_hash = request.args.get('user_random_hash')
    target_user_id = request.args.get('target_user_id')
    authed_user = db.session.query(AuthedUser).filter_by(user_random_hash=user_random_hash).first()
    room_id = ''
    if authed_user:
        has_match = db.session.query(SwipeRight).filter_by(swiper_id=authed_user.user_id,
                                                           target_id=target_user_id).first()
        if has_match:
            room_id = uuid.uuid4().hex
            room = Room(id=room_id, unique_users_id=authed_user.user_id + target_user_id, opened_by=authed_user.user_id)
            new_id = uuid.uuid4().hex
            room_user_record1 = RoomUserRecord(id=new_id)
            new_id = uuid.uuid4().hex
            room_user_record2 = RoomUserRecord(id=new_id)

            room_user_record1.room = room
            room_user_record2.room = room
            user1 = User.query.filter(User.id == target_user_id).first()
            user2 = User.query.filter(User.id == authed_user.user_id).first()
            room_user_record1.user = user1
            room_user_record2.user = user2
            room_user_record1.target_user = user2
            room_user_record2.target_user = user1
            room.opened_by = user2
            db.session.add(room)
            db.session.add(room_user_record1)
            db.session.add(room_user_record2)
            Match.query.filter_by(first_user_id=authed_user.user_id, second_user_id=target_user_id).delete()
            Match.query.filter_by(first_user_id=authed_user.user_id, second_user_id=target_user_id).delete()
            db.session.commit()
        else:
            err = 'Cannot create a room - Not a match'

    else:
        err = 'Unexpected error'

    return jsonify({'error': err, 'result': room_id})


if __name__ == '__main__':
    create_simple_data()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
