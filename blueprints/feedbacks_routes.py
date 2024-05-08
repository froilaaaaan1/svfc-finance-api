from flask import Blueprint, make_response, jsonify
from mysql.connector import Error, connect, errorcode
import dotenv
import os
import logging
from flask_cors import CORS

dotenv.load_dotenv()
feedback_routes = Blueprint('feedback_routes', __name__)
CORS(feedback_routes, resources={r"/*": {"origins": "*"}})
file_handler = logging.FileHandler('feedback_routes.log')
file_handler.setLevel(logging.WARNING)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)

logger = logging.getLogger()
logger.setLevel(logging.WARNING)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

@feedback_routes.route('/get_feedbacks', methods=['GET'])
def get_feedbacks():
  try:
    connection = connect(
      user=os.getenv('USER'),
      password=os.getenv('PASSWORD'),
      port=os.getenv('PORT'),
      database='svfc_finance'
    )
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM feedbacks_table')
    feedbacks = cursor.fetchall()
    cursor.close()
    connection.close()

    return make_response(jsonify(feedbacks), 200)
  except Error as e:
    logger.error(f'Error: {e}')
    return make_response(jsonify({'error': str(e)}), 500)
