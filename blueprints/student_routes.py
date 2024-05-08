from flask import Blueprint, make_response, jsonify
import dotenv
import logging
from flask_cors import CORS

dotenv.load_dotenv()
student_routes = Blueprint('student_routes', __name__)
CORS(student_routes, resources={r"/*": {"origins": "*"}})
file_handler = logging.FileHandler('student_routes.log')
file_handler.setLevel(logging.WARNING)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)

logger = logging.getLogger()
logger.setLevel(logging.WARNING)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


@student_routes.route('/course/college', methods=['GET'])
def get_college_courses():
  courses = ['BSED English - Bachelor of Secondary Education major in English',
            'BSED Filipino - Bachelor of Secondary Education major in Filipino',
            'BSED Social Studies - Bachelor of Secondary Education major in Social Studies',
            'BEED GenEd - Bachelor of Elementary Education major in General Education',
            'BSIT - Bachelor of Science in Information Technology',
            'BSHM - Bachelor of Science in Hospitality Management',
            'BSA - Bachelor of Science in Accountancy']
  return make_response(jsonify(courses), 200)
