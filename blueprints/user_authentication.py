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

# CREATE DEFINER=`root`@`localhost` PROCEDURE `get_user_details_for_login`(
#     IN p_user_number VARCHAR(45),
#     IN p_role ENUM('Admin', 'Student'),
#     OUT p_avatar ENUM('avatar_1.png','avatar_2.png','avatar_3.png','avatar_4.png','avatar_5.png','avatar_6.png','avatar_7.png','avatar_8.png','avatar_9.png','avatar_10.png','avatar_11.png','avatar_12.png')
# )
# BEGIN
# 	DECLARE is_valid_user BOOLEAN DEFAULT FALSE;
#     -- Validate user_number exists and retrieve salt and avatar
#   SELECT salt, avatar
#        FROM users_table
#        WHERE user_number = user_number AND role = p_role
#        LIMIT 1;  -- Limit to one row

#   SET is_valid_user = (FOUND_ROWS() > 0);  -- Check if a row was found

#   IF is_valid_user THEN
#     SELECT salt, avatar;  -- Return only salt and avatar
#   ELSE
#     SELECT NULL AS salt, NULL AS avatar;  -- Return NULL for non-existent user
#   END IF;
# END


dotenv.load_dotenv()
user_authentication = Blueprint('user_authentication', __name__)
CORS(user_authentication, resources={r"/*": {"origins": "*"}})
# Create a file handler
file_handler = logging.FileHandler('authentication.log')
file_handler.setLevel(logging.WARNING)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)

# Create a logger and add the handlers
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

    try: 
      with connection.cursor() as cursor:
        cursor.callproc('get_user_details_for_login', [user_number, role])
        for result in cursor.stored_results():
          user = result.fetchone()
          if user is None:
            return jsonify({'error': 'User does not exist'}), 404
          salt = user['salt']
          avatar = user['avatar']
          hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt.encode('utf-8')).decode('utf-8')
          if hashed_password == user['password']:
            return jsonify({'avatar': avatar, 'user_number': user_number}), 200
          else:
            return jsonify({'error': 'Invalid credentials'}), 401

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
  # It requires the following parameters: role, password, user_number, first_name, middle_name, last_name, email, phone_number, birthdate, gender, home_address, barangay, city, and avatar
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