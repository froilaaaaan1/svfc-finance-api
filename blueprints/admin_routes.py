from flask import Blueprint, make_response, request, jsonify
from mysql.connector import Error, connect, errorcode
import dotenv
import os
import logging
from html import escape
from datetime import datetime
from validate_email import validate_email
from flask_cors import CORS

dotenv.load_dotenv()
admin_routes = Blueprint('admin_routes', __name__)
CORS(admin_routes, resources={r"/*": {"origins": "*"}})
file_handler = logging.FileHandler('admin_routes.log')
file_handler.setLevel(logging.WARNING)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)

logger = logging.getLogger()
logger.setLevel(logging.WARNING)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

@admin_routes.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
  try:
    connection = connect(
      user=os.getenv('USER'),
      password=os.getenv('PASSWORD'),
      port=os.getenv('PORT'),
      database='svfc_finance'
    )
    program_counts = {}
    programs = [
      'BSED English - Bachelor of Secondary Education major in English', 
      'BSED Filipino - Bachelor of Secondary Education major in Filipino',
      'BSED Social Studies - Bachelor of Secondary Education major in Social Studies',
      'BEED GenEd - Bachelor of Elementary Education major in General Education',
      'BSIT - Bachelor of Science in Information Technology',
      'BSHM - Bachelor of Science in Hospitality Management',
      'BSA - Bachelor of Science in Accountancy'
    ]
    
    for program in programs:
      cursor = connection.cursor()
      args = [program, 0]
      result_args = cursor.callproc('get_student_by_program', args)
      student_count = result_args[1]
      program_counts[program] = student_count
      cursor.close()

    connection.close()
    
    return make_response(jsonify(program_counts), 200)
  except Error as e:
    logger.error(f'Error: {e}')
    return make_response(jsonify({'error': str(e)}), 500)