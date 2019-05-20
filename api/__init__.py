import os

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

db = SQLAlchemy(app)

CORS(app)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:mvjunetwo@localhost/bookshelf'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123456789@localhost/bookshelf'
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['USE_SESSION_FOR_NEXT'] = True
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['SECRET_KEY'] = 'thisissecret'
app.secret_key = os.urandom(24)

#rttr


#def createDB():
#    engine = sqlalchemy.create_engine('postgresql://postgres:mvjunetwo@localhost') #connects to server
#    conn = engine.connect()
#    conn.execute("commit")
#    conn.execute("create database bookshelf")
#    conn.close()

#def createTables():
db.create_all()


# =======
# def createDB():
#     engine = sqlalchemy.create_engine('postgresql://postgres:postgres@localhost') #connects to server
#     conn = engine.connect()
#     conn.execute("commit")
#     conn.execute("create database bookshelf")
#     conn.close()


#createDB()
#createTables()
