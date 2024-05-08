from flask import Blueprint, request, jsonify
from mysql.connector import Error, connect, errorcode
from dotenv import load_dotenv
from flask_cors import CORS
import time

load_dotenv()
reporting = Blueprint('reporting', __name__)
CORS(reporting)

@reporting.route('/api/send_feeback', methods=['POST'])
def send_feedback():
  try:
    data = request.get_json()
    student_number = data.get('student_number')
    content = data.get('content')
    time.sleep(20)
    if not student_number or not content:
      return jsonify({'error': 'Please provide student_number and content'}), 400

    db_connection = connect(
      user='root',
      password='2003',
      port=3306,
      database='svfc_finance'
    )
    cursor = db_connection.cursor()
    sql_statement = "INSERT INTO feedbacks_table(student_number, content) VALUES(%s, %s)"
    cursor.execute(sql_statement, (student_number, content))
    db_connection.commit()
    cursor.close()
    db_connection.close()
    return jsonify({'message': 'Feedback inserted successfully.'}), 200

  except Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      return jsonify({'error': 'Invalid credentials'}), 401
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
      return jsonify({'error': 'Database does not exist'}), 404
    else:
      return jsonify({'error': 'Something went wrong'}), 500
  except Exception as e:
    return jsonify({'error': 'Something went wrong'}), 500
