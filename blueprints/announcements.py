from flask import Blueprint, make_response, request, jsonify
from mysql.connector import Error, connect, errorcode
import dotenv
import os
import logging
import bcrypt
from html import escape
from datetime import datetime
from validate_email import validate_email
from flask_cors import CORS
from flask_socketio import SocketIO, emit, on

dotenv.load_dotenv()
announcements = Blueprint('announcements', __name__)

@announcements.route('/api/create_announcement', methods=['POST'])
def create_announcement():
  try:
    db_connection = connect(
      user=os.getenv('USER'),
      password=os.getenv('PASSWORD'),
      port=os.getenv('PORT'),
      database='svfc_finance'
    )
    data = request.get_json()
    title = data.get('title')
    content = data.get('content')
    admin_number = data.get('admin_number')
    with db_connection.cursor() as cursor:
      query = "INSERT INTO admin_announcement (title, content, admin_number) VALUES (%s, %s, %s)"
      cursor.execute(query, (title, content, admin_number))
    db_connection.commit()
    socketio.emit('new_announcement', {'title': title, 'content': content, 'admin_number': admin_number, 'created_at': datetime.now().isoformat()})
    return jsonify({'message': 'Announcement created successfully.'}), 200

  except Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      return jsonify({'error': 'Invalid credentials'}), 401
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
      return jsonify({'error': 'Database does not exist'}), 404
    else:
      print(err)
      return jsonify({'error': 'Something went wrong'}), 500
  except Exception as e:
    return jsonify({'error': 'Something went wrong'}), 500
