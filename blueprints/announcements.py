from flask import Blueprint, make_response, request, jsonify
from mysql.connector import Error, connect, errorcode
from dotenv import load_dotenv
import os
from flask_cors import CORS

load_dotenv()
announcements = Blueprint('announcements', __name__)
CORS(announcements)

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
    return make_response(jsonify({'message': 'Announcement created successfully'}), 201)

  except Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      return jsonify({'error': 'Invalid credentials'}), 401
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
      return jsonify({'error': 'Database does not exist'}), 404
    else:
      return jsonify({'error': 'Something went wrong'}), 500
  except Exception as e:
    print(e)
    return jsonify({'error': 'Something went wrong'}), 500

def fetch_announcement():
  try:
    db_connection = connect(
      user=os.getenv('USER'),
      password=os.getenv('PASSWORD'),
      port=os.getenv('PORT'),
      database='svfc_finance'
    )
    announcements = []
    unread_announcements = []

    with db_connection.cursor() as cursor:
      query = "SELECT aa.announcement_id, aa.title, aa.content, aa.admin_number, aa.created_at FROM admin_announcement aa LEFT JOIN announcement_read_status ars ON aa.announcement_id = ars.announcement_id WHERE ars.read_status IS NULL OR ars.read_status = 0;"
      cursor.execute(query)
      rows = cursor.fetchall()
    
    for row in rows:
      unread_announcements.append({
        'announcement_id': row[0],
        'title': row[1],
        'content': row[2],
        'admin_number': row[3],
        'created_at': row[4].isoformat()
      })

    with db_connection.cursor() as cursor:
      query = "SELECT aa.announcement_id, aa.title, aa.content, aa.admin_number, aa.created_at FROM admin_announcement aa JOIN announcement_read_status ars ON aa.announcement_id = ars.announcement_id WHERE ars.read_status = 1;"
      cursor.execute(query)
      rows = cursor.fetchall()

    for row in rows:
      announcements.append({
        'announcement_id': row[0],
        'title': row[1],
        'content': row[2],
        'admin_number': row[3],
        'created_at': row[4].isoformat()
      })

    return {'unread_announcements': unread_announcements, 'announcements': announcements}

  except Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      return jsonify({'error': 'Invalid credentials'}), 401
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
      return jsonify({'error': 'Database does not exist'}), 404
    else:
      return jsonify({'error': 'Something went wrong'}), 500
  except Exception as e:
    return jsonify({'error': 'Something went wrong'}), 500

@announcements.route('/api/announcement', methods=['GET'])
def get_announcement():
  return jsonify(fetch_announcement()), 200

@announcements.route('/api/admin/announcements', methods=['GET'])
def get_all_announcements():
  try:
    get_announcements = F"SELECT * FROM admin_announcement"
    db_connection = connect(
      user=os.getenv('USER'),
      password=os.getenv('PASSWORD'),
      port=os.getenv('PORT'),
      database='svfc_finance'
    )
    with db_connection.cursor() as cursor:
      cursor.execute(get_announcements)
      rows = cursor.fetchall()
    announcements = []
    for row in rows:
      announcements.append({
        'announcement_id': row[0],
        'title': row[1],
        'content': row[2],
        'admin_number': row[3],
        'created_at': row[4].isoformat()
      })
    return jsonify(announcements), 200
  except Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      return jsonify({'error': 'Invalid credentials'}), 401
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
      print('Database does not exist')
      return jsonify({'error': 'Database does not exist'}), 404
    else:
      return jsonify({'error': 'Something went wrong'}), 500
  except Exception as e:
    return jsonify({'error': 'Something went wrong'}), 500
  
@announcements.route('/api/announcement/delete', methods=['GET'])
def delete_announcement():
  try:
    db_connection = connect(
      user=os.getenv('USER'),
      password=os.getenv('PASSWORD'),
      port=os.getenv('PORT'),
      database='svfc_finance'
    )
    announcement_id = request.args.get('announcement_id')
    with db_connection.cursor() as cursor:
      query = "DELETE FROM admin_announcement WHERE announcement_id = %s"
      cursor.execute(query, (announcement_id,))
    db_connection.commit()
    return jsonify({'message': 'Announcement deleted successfully'}), 200
  except Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      return jsonify({'error': 'Invalid credentials'}), 401
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
      return jsonify({'error': 'Database does not exist'}), 404
    else:
      return jsonify({'error': 'Something went wrong'}), 500
  except Exception as e:
    return jsonify({'error': 'Something went wrong'}), 500