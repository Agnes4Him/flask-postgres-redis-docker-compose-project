from flask import Flask, request, jsonify
import os
import json
import psycopg
from redis import Redis
from datetime import datetime

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")

redis = Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

create_table_statement = """
create table if not exists users(
	timestamp timestamp,
    id integer,
    name varchar,
    age integer
);
"""
with psycopg.connect("host={} port={} user={} password={}".format(DB_HOST, DB_PORT, DB_USER, DB_PASSWORD),  autocommit=True) as conn:
    with conn.cursor() as curr:
        curr.execute("SELECT 1 FROM pg_database WHERE datname='flask_db'")
        database = curr.fetchall()
        if len(database) == 0:
            curr.execute("create database flask_db;")

with psycopg.connect("host={} port={} dbname={} user={} password={}".format(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)) as conn:
    with conn.cursor() as curr:
        curr.execute(create_table_statement)

@app.route('/')
def ping():
    return {
        'message': 'Welcome to flask CRUD API demo app'
    }

@app.route('/create-user', methods=['POST'])
def create_user():
    user = request.get_json()
    now = datetime.now()
    id = user['id']
    name = user['name']
    age = user['age']

    try:
        with psycopg.connect("host={} port={} dbname={} user={} password={}".format(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)) as conn:
            with conn.cursor() as curr:
                curr.execute(
                    "insert into users(timestamp, id, name, age) values (%s, %s, %s, %s)",
                    (now, id, name, age)
                )

        user['created_at'] = str(now)

        data = {
            'message': 'user successfully created',
            'user': user
        }

        return jsonify(data)
    except:
        return 'Unable to create user. Try again later.'

@app.route('/get-users')
def get_users():
    try:
        with psycopg.connect("host={} port={} dbname={} user={} password={}".format(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)) as conn:
            with conn.cursor() as curr:
                curr.execute('select * from users')
                result = curr.fetchall()
            
                if len(result) != 0:       
                    users = []

                    for user in result:
                        user_dict = {}
                        user_dict['created_at'] = str(user[0])
                        user_dict['id'] = user[1]
                        user_dict['name'] = user[2]
                        user_dict['age'] = user[3]
                        users.append(user_dict)
                    return users
                else:
                    return 'No users at the moment...'
    except:
        return f'Unable to fetch users at the moment. Try again later'

@app.route('/get-user/<int:id>')
def get_user(id):
    try:
        redis_user = redis.execute_command('JSON.GET', str(id))
        if redis_user is not None:
            return redis_user
        else:
            with psycopg.connect("host={} port={} dbname={} user={} password={}".format(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)) as conn:
                with conn.cursor() as curr:
                    curr.execute('select * from users where id = %s', (str(id),))
                    result = curr.fetchall()
            
            if len(result) == 0:
                return f'User with id {id} does not exist.'
            else:
                user = {}
                
                for item in result:
                    user['created_at'] = str(item[0])
                    user['id'] = item[1]
                    user['name'] = item[2]
                    user['age'] = item[3]

                redis.execute_command('JSON.SET', str(id), '.', json.dumps(user))
                return user
    except:
        return f'Unable to fetch user with id {id}. Try again later'

@app.route('/update-user/<int:id>', methods = ['GET','POST'])
def update_user(id):
    user = request.get_json()

    for k, v in user.items():
        field = k
        value = v

    try:
        with psycopg.connect("host={} port={} dbname={} user={} password={}".format(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)) as conn:
            with conn.cursor() as curr:
                curr.execute('update users set ' + field + '= %s where id = %s', (value, str(id),))

        # Delete this record from Redis cache
        redis.execute_command('JSON.DEL', str(id))

        return f'User with id {id} successfully updated'
    except:
        return f'Could not update user with id {id} Try again'

@app.route('/delete-user/<int:id>', methods=['POST'])
def delete_user(id):
    try:
        with psycopg.connect("host={} port={} dbname={} user={} password={}".format(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD)) as conn:
            with conn.cursor() as curr:
                curr.execute('delete from users where id = %s', (str(id),))

        # Delete this record from Redis cache
        redis.execute_command('JSON.DEL', str(id))

        return f'User with id {id} successfully deleted'
    except:
        return f'Unable to delete user with id {id}. Try again later'

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)