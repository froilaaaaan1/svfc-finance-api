from flask import Blueprint, make_response, request, jsonify
from mysql.connector import Error, connect, errorcode
import dotenv
import os
import logging
from html import escape
from datetime import datetime
from flask_cors import CORS

dotenv.load_dotenv()
conversation_routes = Blueprint('conversation_routes', __name__)
CORS(conversation_routes, resources={r"/*": {"origins": "*"}})
file_handler = logging.FileHandler('conversation_routes.log')
file_handler.setLevel(logging.WARNING)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)

logger = logging.getLogger()
logger.setLevel(logging.WARNING)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

@conversation_routes.route('/api/get_all_admin', methods=['GET'])
def get_all_admin():
  try:
    connection = connect(
      user=os.getenv('USER'),
      password=os.getenv('PASSWORD'),
      port=os.getenv('PORT'),
      database='svfc_finance'
    )
    student_number = request.args.get('student_number')

    admins = []
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT apt.admin_number, apt.first_name, apt.middle_name, apt.last_name
            FROM admin_profile_table apt
            LEFT JOIN conversations_table ct ON apt.admin_number = ct.admin_number
            WHERE ct.admin_number IS NULL OR ct.student_number != %s
        """, (student_number,))
        print("Query executed successfully")
        for row in cursor.fetchall():
          admins.append({
              'admin_number': row[0],
              'first_name': row[1],
              'middle_name': row[2],
              'last_name': row[3]
          })
    connection.close()
    return make_response(jsonify(admins), 200)
  except Error as e:
    print("MySQL Error:", e)
    return make_response(jsonify({'error': str(e)}), 500)
  except Exception as e:
    print("Exception:", e)
    return make_response(jsonify({'error': str(e)}), 500)

@conversation_routes.route('/api/get_all_student', methods=['GET'])
def get_all_student():
  try:
    connection = connect(
      user=os.getenv('USER'),
      password=os.getenv('PASSWORD'),
      port=os.getenv('PORT'),
      database='svfc_finance'
    )
    admin_number = request.args.get('admin_number')

    students = []
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT spt.student_number, spt.firstname, spt.middlename, spt.lastname
            FROM student_profile_table spt
            LEFT JOIN conversations_table ct ON spt.student_number = ct.student_number
            WHERE ct.student_number IS NULL OR ct.admin_number != %s
        """, (admin_number,))
        print("Query executed successfully")
        for row in cursor.fetchall():
          students.append({
              'student_number': row[0],
              'first_name': row[1],
              'middle_name': row[2],
              'last_name': row[3]
          })
    connection.close()
    return make_response(jsonify(students), 200)
  except Error as e:
    print("MySQL Error:", e)
    return make_response(jsonify({'error': str(e)}), 500)
  except Exception as e:
    print("Exception:", e)
    return make_response(jsonify({'error': str(e)}), 500)

# get all the conversation of the admin and the recent message of each conversation
@conversation_routes.route('/api/get_all_conversation_of_admin', methods=['GET'])
def get_all_conversation():
  try:
    connection = connect(
      user=os.getenv('USER'),
      password=os.getenv('PASSWORD'),
      port=os.getenv('PORT'),
      database='svfc_finance'
    )

    admin_number = request.args.get('admin_number')
    conversations = []
    with connection.cursor() as cursor:
        cursor.execute("""
          SELECT c.conversation_id, spt.firstname, spt.lastname, c.student_number, m.content, m.timestamp
          FROM conversations_table c
          LEFT JOIN (
            SELECT m1.conversation_id, m1.content, m1.timestamp
            FROM messages_table m1
            INNER JOIN (
              SELECT conversation_id, MAX(timestamp) as max_timestamp
              FROM messages_table
              GROUP BY conversation_id
            ) m2 ON m1.conversation_id = m2.conversation_id AND m1.timestamp = m2.max_timestamp
          ) m ON c.conversation_id = m.conversation_id
          JOIN student_profile_table spt ON c.student_number = spt.student_number
          WHERE c.admin_number =  %s
        """, (admin_number,))
        print("Query executed successfully")
        for row in cursor.fetchall():
          conversations.append({
              'conversation_id': row[0],
              'full_name': row[1] + " " + row[2],
              'student_number': row[3],
              'recent_message': row[4],
              'message_timestamp': row[5]
          })
    connection.close()
    return make_response(jsonify(conversations), 200)
  except Error as e:
    print("MySQL Error:", e)
    return make_response(jsonify({'error': str(e)}), 500)
  except Exception as e:
    print("Exception:", e)
    return make_response(jsonify({'error': str(e)}), 500)


@conversation_routes.route('/api/get_all_conversation_of_student', methods=['GET'])
def get_all_conversation_of_student():
  try:
    connection = connect(
      user=os.getenv('USER'),
      password=os.getenv('PASSWORD'),
      port=os.getenv('PORT'),
      database='svfc_finance'
    )

    student_number = request.args.get('student_number')
    conversations = []
    with connection.cursor() as cursor:
        cursor.execute("""
          SELECT c.conversation_id, apt.first_name, apt.last_name, c.admin_number, m.content, m.timestamp
          FROM conversations_table c
          LEFT JOIN (
            SELECT m1.conversation_id, m1.content, m1.timestamp
            FROM messages_table m1
            INNER JOIN (
              SELECT conversation_id, MAX(timestamp) as max_timestamp
              FROM messages_table
              GROUP BY conversation_id
            ) m2 ON m1.conversation_id = m2.conversation_id AND m1.timestamp = m2.max_timestamp
          ) m ON c.conversation_id = m.conversation_id
          JOIN admin_profile_table apt ON c.admin_number = apt.admin_number
          WHERE c.student_number =  %s
        """, (student_number,))
        print("Query executed successfully")
        for row in cursor.fetchall():
          conversations.append({
              'conversation_id': row[0],
              'full_name': row[1] + " " + row[2],
              'admin_number': row[3],
              'recent_message': row[4],
              'message_timestamp': row[5]
          })
    connection.close()
    return make_response(jsonify(conversations), 200)
  except Error as e:
    print("MySQL Error:", e)
    return make_response(jsonify({'error': str(e)}), 500)
  except Exception as e:
    print("Exception:", e)
    return make_response(jsonify({'error': str(e)}), 500)

@conversation_routes.route('/api/send_message', methods=['POST'])
def send_message():
  try:
    connection = connect(
      user=os.getenv('USER'),
      password=os.getenv('PASSWORD'),
      port=os.getenv('PORT'),
      database='svfc_finance'
    )
    data = request.get_json()
    conversation_id = data['conversation_id']
    sender_number = data['sender_number']
    content = data['content']
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    is_read = 0

    with connection.cursor() as cursor:
        cursor.execute("""INSERT INTO messages_table (conversation_id, sender_number, content, timestamp, is_read)
                          VALUES (%s, %s, %s, %s, %s)""", (conversation_id, sender_number, content, timestamp, is_read))
        connection.commit()
        print("Query executed successfully")
    connection.close()
    return make_response(jsonify({'message': 'Message sent successfully'}), 200)
  except Error as e:
    print("MySQL Error:", e)
    return make_response(jsonify({'error': str(e)}), 500)
  except Exception as e:
    print("Exception:", e)
    return make_response(jsonify({'error': str(e)}), 500)

@conversation_routes.route('/api/get_all_message_on_conversation', methods=['GET'])
def get_all_message_on_conversation():
  try:
    connection = connect(
      user=os.getenv('USER'),
      password=os.getenv('PASSWORD'),
      port=os.getenv('PORT'),
      database='svfc_finance'
    )

    conversation_id = request.args.get('conversation_id')
    if not conversation_id:
      return make_response(jsonify({'error': 'conversation_id is required'}), 400)

    messages = []
    with connection.cursor() as cursor:
        cursor.execute("""SELECT messages_id, conversation_id, sender_number, content, timestamp, is_read
                          FROM messages_table
                          WHERE conversation_id = %s""", (conversation_id,))
        print("Query executed successfully")
        for row in cursor.fetchall():
          messages.append({
              'messages_id': row[0],
              'conversation_id': row[1],
              'sender_number': row[2],
              'content': row[3],
              'timestamp': row[4],
              'is_read': row[5]
          })
    connection.close()
    return make_response(jsonify(messages), 200)
  except Error as e:
    print("MySQL Error:", e)
    return make_response(jsonify({'error': str(e)}), 500)
  except Exception as e:
    print("Exception:", e)
    return make_response(jsonify({'error': str(e)}), 500)

@conversation_routes.route('/api/create_new_conversation', methods=['POST'])
def create_new_conversation():
  try:
    connection = connect(
      user=os.getenv('USER'),
      password=os.getenv('PASSWORD'),
      port=os.getenv('PORT'),
      database='svfc_finance'
    )
    data = request.get_json()
    student_number = data['student_number']
    admin_number = data['admin_number']
    if not student_number or not admin_number:
      return make_response(jsonify({'error': 'student_number and admin_number is required'}), 400)
    if student_number == admin_number:
      return make_response(jsonify({'error': 'student_number and admin_number must be different'}), 400)

    with connection.cursor() as cursor:
        cursor.execute("""INSERT INTO conversations_table (student_number, admin_number)
                          VALUES (%s, %s)""", (student_number, admin_number))
        connection.commit()
        print("Query executed successfully")
        conversation_id = cursor.lastrowid
    connection.close()
    return make_response(jsonify({'message': 'Conversation created successfully', 'conversation_id': conversation_id}), 200)
  except Error as e:
    print("MySQL Error:", e)
    return make_response(jsonify({'error': str(e)}), 500)
  except Exception as e:
    print("Exception:", e)
    return make_response(jsonify({'error': str(e)}), 500)

@conversation_routes.route('/api/thread', methods=['GET'])
def get_thread():
  try:
    connection = connect(
      user=os.getenv('USER'),
      password=os.getenv('PASSWORD'),
      port=os.getenv('PORT'),
      database='svfc_finance'
    )

    conversation_id = request.args.get('conversation_id')
    if not conversation_id:
      return make_response(jsonify({'error': 'conversation_id is required'}), 400)
    thread = []
    with connection.cursor() as cursor:
        cursor.execute("""
          SELECT m.sender_number,
            COALESCE(aa.first_name, spt.firstname) AS firstname,
            COALESCE(aa.last_name, spt.lastname) AS lastname,
            m.content,
            m.timestamp,
            u.avatar
          FROM messages_table m
          JOIN users_table u ON m.sender_number = u.user_number
          LEFT JOIN admin_profile_table aa ON m.sender_number = aa.admin_number
          LEFT JOIN student_profile_table spt ON m.sender_number = spt.student_number
          WHERE m.conversation_id = %s
          ORDER BY m.timestamp
        """, (conversation_id,))
        print("Query executed successfully")
        for row in cursor.fetchall():
          thread.append({
              'sender_number': row[0],
              'first_name': row[1],
              'last_name': row[2],
              'content': row[3],
              'timestamp': row[4],
              'avatar': row[5],
          })
    connection.close()
    return make_response(jsonify(thread), 200)
  except Error as e:
    print("MySQL Error:", e)
    return make_response(jsonify({'error': str(e)}), 500)
  except Exception as e:
    print("Exception:", e)
    return make_response(jsonify({'error': str(e)}), 500)
