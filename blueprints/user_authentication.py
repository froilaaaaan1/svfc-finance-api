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

dotenv.load_dotenv()
user_authentication = Blueprint('user_authentication', __name__)
CORS(user_authentication, resources={r"/*": {"origins": "*"}})
file_handler = logging.FileHandler('authentication.log')
file_handler.setLevel(logging.WARNING)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)

logger = logging.getLogger()
logger.setLevel(logging.WARNING)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

@user_authentication.route('/login', methods=['POST'])
def login():
  # Login the user
  # It requires three parameters: role, password, and user_number
  # It returns the avatar and user_number of the user
  try:
    data = request.get_json()
    role = data['role']
    password = data['password']
    user_number = data['user_number']
    connection = connect(
      user=os.getenv('USER'),
      password=os.getenv('PASSWORD'),
      port=os.getenv('PORT'),
      database='svfc_finance'
    )
    # sanitize the input
    role = escape(role)
    password = escape(password)
    user_number = escape(user_number)
    if not role or not password or not user_number:
      return jsonify({'error': 'Missing parameters', 'status': 400}), 400
    if role not in ['Admin', 'Student']:
      return jsonify({'error': 'Invalid role', 'status': 400}), 400
    try:
      with connection.cursor() as cursor:
        get_hash_salt = f"SELECT password, salt, avatar FROM users_table WHERE user_number = '{user_number}' AND role = '{role}'"
        cursor.execute(get_hash_salt)
        result = cursor.fetchone()
        if not result:
          return jsonify({'error': 'User not found', 'status': 404, 'message': 'User Not Found'}), 404
        hash_password_database = result[0]
        salt = result[1]
        avatar = result[2]
        password = password.encode('utf-8')
        salt = salt.encode('utf-8')
        hashed_password = bcrypt.hashpw(password, salt).decode('utf-8')

        if hash_password_database == hashed_password:
          args = [role, user_number] + [None]*12
          result_args = cursor.callproc('fetch_user_info', args)
          if role == 'Admin':
            first_name, middle_name, last_name, email, phone_number, birthdate, gender, home_address, barangay, city = result_args[2:12]
            return jsonify({
              'first_name': first_name,
              'middle_name': middle_name,
              'last_name': last_name,
              'email': email,
              'phone_number': phone_number,
              'birthdate': birthdate,
              'gender': gender,
              'home_address': home_address,
              'barangay': barangay,
              'city': city,
              'avatar': avatar,
              'status': 200,
              'message': 'Login successful'
            }), 200
          else:
            first_name, middle_name, last_name, email, phone, birthdate, gender, home_address, barangay, city, academic_program, year_level = result_args[2:14]
            return jsonify({
              'first_name': first_name,
              'middle_name': middle_name,
              'last_name': last_name,
              'email': email,
              'phone': phone,
              'birthdate': birthdate,
              'gender': gender,
              'home_address': home_address,
              'barangay': barangay,
              'city': city,
              'academic_program': academic_program,
              'year_level': year_level,
              'avatar': avatar,
              'status': 200,
              'message': 'Login successful'
            }), 200

        else:
          return jsonify({'error': 'Incorrect password', 'status': 401, 'message': 'Incorrect Password'}), 401

    except Error as err:
      logging.exception('An error occurred')
      return jsonify({'error': 'Something went wrong'}), 500
    finally:
      connection.close()
  except Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      return jsonify({'error': 'Invalid credentials'}), 401
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
      return jsonify({'error': 'Database does not exist'}), 404
    else:
      logging.exception('An error occurred')
      return jsonify({'error': 'Something went wrong'}), 500
  except:
    logging.exception('An error occurred')
    return jsonify({'message': 'Internal Server Error'}), 500


@user_authentication.route('/register', methods=['POST'])
def register():
  if request.method == 'OPTIONS':
    return _build_cors_preflight_response()
  else:
    return _handle_register_request()

def _handle_register_request():
  # Register a new user
  # It requires the following parameters: role, password, user_number, first_name, middle_name, last_name, email, phone_number, birthdate, gender, home_address, barangay, city, and avatar and conditional parameters: academic_program and year_level
  # It returns a message if the user is registered successfully
  # However, it returns an error based on what happened or what went wrong
  try:
    connection = connect(
      user=os.getenv('USER'),
      password=os.getenv('PASSWORD'),
      port=os.getenv('PORT'),
      database='svfc_finance'
    )
    data = request.get_json()
    role = data['role']
    password = data['password']
    user_number = data['user_number']
    first_name = data['first_name']
    middle_name = data['middle_name']
    last_name = data['last_name']
    email = data['email']
    phone_number = data['phone_number']
    birthdate = data['birthdate']
    gender = data['gender']
    home_address = data['home_address']
    barangay = data['barangay']
    city = data['city']
    avatar = data['avatar']

    if role not in ['Admin', 'Student']:
      print("Invalid role")
      return jsonify({'error': 'Invalid role', 'status_code': 400}), 400
    if not validate_email(email):
      print("Invalid email")
      return jsonify({'error': 'Invalid email', 'status_code': 400}), 400
    if gender not in ['Male', "Female", 'Non-Binary', 'Others']:
      print("Invalid Gender")
      return jsonify({'error': 'Invalid Gender', 'status_code': 400}), 400
    if len(password) < 8:
      print("Password must be at least 8 characters long")
      return jsonify({'error': 'Password must be at least 8 characters long', 'status_code': 400}), 400
    if not role or not password or not user_number or not first_name or not middle_name or not last_name or not email or not phone_number or not birthdate or not gender or not home_address or not barangay or not city or not avatar:
      print("Missing parameters")
      return jsonify({'error': 'Missing parameters', 'status_code': 400}), 400

    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    if role == 'Student':
        academic_program = data['academic_program']
        if academic_program not in ['BSED English - Bachelor of Secondary Education major in English', 'BSED Filipino - Bachelor of Secondary Education major in Filipino', 'BSED Social Studies - Bachelor of Secondary Education major in Social Studies', 'BEED GenEd - Bachelor of Elementary Education major in General Education', 'BSIT - Bachelor of Science in Information Technology', 'BSHM - Bachelor of Science in Hospitality Management', 'BSA - Bachelor of Science in Accountancy']:
          return jsonify({'error': 'Invalid academic program', 'status_code': 400}), 400
        year_level = data['year_level']
        sql = f"""
        CALL insert_user_profile(
          '{user_number}',
          '{hashed_password}',
          '{role}',
          '{avatar}',
          '{salt.decode('utf-8')}',
          '{first_name}',
          '{middle_name}',
          '{last_name}',
          '{email}',
          '{phone_number}',
          '{birthdate}',
          '{gender}',
          '{home_address}',
          '{barangay}',
          '{city}',
          '{academic_program}',
          '{year_level}'
        )
        """
    else:
        sql = f"""
        CALL insert_user_profile(
          '{user_number}',
          '{hashed_password}',
          '{role}',
          '{avatar}',
          '{salt.decode('utf-8')}',
          '{first_name}',
          '{middle_name}',
          '{last_name}',
          '{email}',
          '{phone_number}',
          '{birthdate}',
          '{gender}',
          '{home_address}',
          '{barangay}',
          '{city}',
          NULL,
          NULL
        )
        """

    try:
      with connection.cursor() as cursor:
        cursor.execute(sql)
        connection.commit()
    except Error as err:
      if err.errno == errorcode.ER_DUP_ENTRY:
        return jsonify({'error': 'User already exists'}), 409
      else:
        logging.exception('An error occurred')
        return jsonify({'error': 'Something went wrong'}), 500
    finally:
      connection.close()

    return jsonify({'message': 'User registered successfully'}), 201
  except Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      return jsonify({'error': 'Invalid credentials'}), 401
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
      return jsonify({'error': 'Database does not exist'}), 404
    else:
      logging.exception('An error occurred')
      return jsonify({'error': 'Something went wrong'}), 500
  except ValueError as err:
    print("ValueError: ", err)
    return jsonify({'error': 'Invalid date format'}), 400
  except:
    logging.exception('An error occurred')
    return jsonify({'message': 'Internal Server Error'}), 500

def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response
