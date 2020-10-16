import os
import sqlite3
import click
from flask import current_app, g
from flask.cli import with_appcontext

DATABASE = 'database.db'
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db(app):
    if not os.path.isfile(DATABASE):
        with app.app_context():
            db = get_db()
            with app.open_resource('sql.sql', mode='r') as f:
                db.cursor().executescript(f.read())
            db.commit()
    else:
        print("DB already exists")