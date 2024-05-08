from flask import Flask, render_template, request, jsonify, make_response
from flask_mail import Mail, Message
import os
from flask_cors import CORS
import mysql.connector
from mysql.connector import errorcode
from dotenv import load_dotenv
import re
from datetime import datetime
from validate_email import validate_email
from flask_socketio import SocketIO, emit
from blueprints.admin_routes import admin_routes
from blueprints.student_routes import student_routes
from blueprints.user_authentication import user_authentication
from blueprints.announcements import announcements
from blueprints.reporting import reporting
from blueprints.conversation_routes import conversation_routes
from blueprints.feedbacks_routes import feedback_routes

load_dotenv()

app = Flask(__name__)
__all__ = ['send_user_number']

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = True
app.register_blueprint(user_authentication)
app.register_blueprint(admin_routes)
app.register_blueprint(student_routes)
app.register_blueprint(announcements)
app.register_blueprint(reporting)
app.register_blueprint(conversation_routes)
app.register_blueprint(feedback_routes)
mail = Mail(app)
CORS(app, cors_allowed_origins="*")
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
  socketio.emit('connected', {'data': 'Connected to server'})
  print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
  print('Client disconnected')


@socketio.on('mark_as_read')
def mark_as_read(data):
  try:
    mark_as_read(data)
    socketio.emit('mark_as_read', data)
    socketio.emit('request_announcements')
  except Exception as e:
    print(e)

@app.route('/send_mail', methods=['POST'])
def send_mail():
  try:
    data = request.get_json()
    email = data.get('email')
    message = data.get('message')
    subject = data.get('subject')
    if not validate_email(email):
      return jsonify({'error': 'Invalid email address'}), 400
    if not message or not subject:
      return jsonify({'error': 'Message and subject are required'}), 400
    msg = Message('SVFC Finance', sender=os.getenv('MAIL_USERNAME'), recipients=[email])
    msg.body = message
    mail.send(msg)
    return jsonify({'message': 'Email sent successfully.'}), 200
  except Exception as e:
    return jsonify({'error': 'Something went wrong'}), 500

@app.route('/mark_as_read', methods=['POST'])
def mark_as_read():
  try:
    data = request.get_json()
    announcement_id = data.get('announcement_id')
    user_number = data.get('user_number')

    db_connection = mysql.connector.connect(
      user=os.getenv('USER'),
      password=os.getenv('PASSWORD'),
      port=os.getenv('PORT'),
      database='svfc_finance'
    )

    with db_connection.cursor() as cursor:
      query = "INSERT INTO announcement_read_status (user_number, announcement_id, read_status, read_at) VALUES (%s, %s, 1, NOW())"
      cursor.execute(query, (user_number, announcement_id))
    db_connection.commit()

    socketio.emit('mark_as_read', {'announcement_id': announcement_id})
    return jsonify({'message': 'Marked as read successfully.'}), 200

  except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      return jsonify({'error': 'Invalid credentials'}), 401
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
      return jsonify({'error': 'Database does not exist'}), 404
    else:
      return jsonify({'error': 'Something went wrong'}), 500

  except Exception as e:
    return jsonify({'error': 'Something went wrong'}), 500

@app.route('/api/check_card_validity', methods=['POST'])
def check_card_validity():
  data = request.get_json()
  card_number = data.get('card_number', '')
  expiry_date = data.get('expiry_date', '')
  cvv = data.get('cvv', '')

  if not is_valid_card_number(card_number): return jsonify({'valid': False, 'message': 'Invalid card number.'}), 400

  if not is_valid_expiry_date(expiry_date): return jsonify({'valid': False, 'message': 'Invalid expiry date. Use MM/YY format.'}), 400

  if not is_valid_cvv(cvv): return jsonify({'valid': False, 'message': 'Invalid CVV. Use 3 or 4 digits.'}), 400

  return jsonify({'valid': True, 'message': 'Card details appear valid.'}), 200

def is_valid_card_number(card_number):
  return re.match(r'^[0-9]{13,19}$', card_number) is not None

def is_valid_expiry_date(expiry_date):
  if not re.match(r'^(0[1-9]|1[0-2])\/[0-9]{2}$', expiry_date):
    return False
  exp_month, exp_year = map(int, expiry_date.split('/'))
  expiry_datetime = datetime(year=2000 + exp_year, month=exp_month, day=1)
  current_datetime = datetime.now()
  return expiry_datetime > current_datetime

def is_valid_cvv(cvv):
  return re.match(r'^[0-9]{3,4}$', cvv) is not None

@app.route('/send-receipt', methods=['POST'])
def send_receipt():
  try:
    db_connection = mysql.connector.connect(
      user=os.getenv('USER'),
      password=os.getenv('PASSWORD'),
      port=os.getenv('PORT'),
      database='svfc_finance'
    )
    data = request.get_json()
    amount = data.get('amount')
    payment_method_name = data.get('payment_method_name')
    bill_id = data.get('bill_id')
    get_bill_info = "SELECT student_number, total_amount, semester, bill_date FROM bills_table WHERE bills_id = %s"
    cursor = db_connection.cursor()
    cursor.execute(get_bill_info, (bill_id,))
    bill_info = cursor.fetchone()
    student_number, total_amount, semester, bill_date = bill_info

    # get student name
    get_student_info = "SELECT firstname, email, lastname FROM student_profile_table WHERE student_number = %s"
    cursor.execute(get_student_info, (student_number,))
    student_info = cursor.fetchone()
    first_name = student_info[0]
    last_name = student_info[2]
    student_email = student_info[1]

    html_email = render_template('send_receipt_template.html', student_name=f'{first_name} {last_name}', student_number=student_number, amount=amount, semester=semester, payment_method_name=payment_method_name, total_amount=total_amount, bill_date=bill_date)

    msg = Message('SVFC Payment Receipt', sender=os.getenv('MAIL_USERNAME'), recipients=[student_email])
    msg.html = html_email
    mail.send(msg)

    return jsonify({'message': 'Email sent successfully.'}), 200
  except Exception as e:
    print(e)
    return jsonify({'error': 'Something went wrong'}), 500



@app.route('/api-svfc-get-all-feedbacks', methods=['GET'])
def get_feedback():
  try:
    db_connection = mysql.connector.connect(
      user='root',
      password='2003',
      port=3306,
      database='svfc_finance'
    )
    cursor = db_connection.cursor()
    stored_procedure = "CALL get_all_feedbacks()"
    cursor.callproc(stored_procedure)
    feedbacks = cursor.fetchall()
    cursor.close()
    db_connection.close()
    return jsonify({'feedbacks': feedbacks}), 200
  except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      return jsonify({'error': 'Invalid credentials'}), 401
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
      return jsonify({'error': 'Database does not exist'}), 404
    else:
      return jsonify({'error': 'Something went wrong'}), 500
  except Exception as e:
    return jsonify({'error': 'Something went wrong'}), 500


@app.route('/api-svfc-fetch_semesters', methods=['POST'])
def fetch_semesters():
  try:
    db_connection = mysql.connector.connect(
      user='root',
      password='2003',
      port=3306,
      database='svfc_finance'
    )
    data = request.get_json()
    student_number = data.get('student_number')
    with db_connection.cursor() as cursor:
      query = "SELECT DISTINCT semester FROM bills_table WHERE student_number = %s"
      cursor.execute(query, (student_number,))
      rows = cursor.fetchall()
    semesters_with_bills = {row[0] for row in rows}
    all_semesters = [
      '1st year 1st sem', '1st year 2nd sem',
      '2nd year 1st sem', '2nd year 2nd sem',
      '3rd year 1st sem', '3rd year 2nd sem',
      '4th year 1st sem', '4th year 2nd sem',
      '5th year 1st sem', '5th year 2nd sem'
    ]
    semesters_without_bills = list(set(all_semesters) - semesters_with_bills)
    options = [{'semester': semester} for semester in semesters_without_bills]

    return jsonify(options), 200

  except Exception as e:
    return jsonify({'error': str(e)}), 500

  finally:
    db_connection.close()


@app.route('/api-svfc-total-student-bills', methods=['POST'])
def get_student_total_bills():
  try:
    db_connection = mysql.connector.connect(
      user=os.getenv('USER'),
      password=os.getenv('PASSWORD'),
      port=os.getenv('PORT'),
      database='svfc_finance'
    )
    data = request.get_json()
    if not data.get('student_number'):
      return jsonify({'error': 'Student number is required'}), 400
    student_number = data.get('student_number')
    with db_connection.cursor() as cursor:
      query = "SELECT * FROM bills_table WHERE student_number = %s"
      cursor.execute(query, (student_number,))
      rows = cursor.fetchall()
    total_bills = 0
    for row in rows:
      total_bills += row[4]
    return jsonify({'total_bill': total_bills}), 200
  except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      return jsonify({'error': 'Invalid credentials'}), 401
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
      return jsonify({'error': 'Database does not exist'}), 404
    else:
      return jsonify({'error': 'Something went wrong', 'info': err}), 500
  except Exception as e:
    return jsonify({'error': 'Something went wrong', 'info': e}), 500
  finally:
    db_connection.close()

@app.route('/api-svfc-get-student-bills', methods=['POST'])
def get_student_bills():
  try:
    db_connection = mysql.connector.connect(
      user=os.getenv('USER'),
      password=os.getenv('PASSWORD'),
      port=os.getenv('PORT'),
      database='svfc_finance'
    )
    data = request.get_json()
    student_number = data.get('student_number')

    list_of_bills = []
    with db_connection.cursor() as cursor:
      query = "SELECT * FROM bills_table WHERE student_number = %s"
      cursor.execute(query, (student_number,))
      rows = cursor.fetchall()
      for row in rows:
        list_of_bills.append({
          'bills_id': row[0],
          'semester': row[2],
          'bill_date': row[3].isoformat(),
          'amount': row[4]
        })

    bills = []
    for row in rows:
      bill_id = row[0]
      semester = row[2]
      total_amount = row[3]

      with db_connection.cursor() as cursor:
        query = "SELECT * FROM bill_items_table WHERE bill_id = %s"
        cursor.execute(query, (bill_id,))
        items = cursor.fetchall()

      bill_items = []
      for item in items:
        bill_items.append({
          'item_name': item[2],
          'amount': item[3],
          'remarks': item[4]
        })

      bills.append({
        'bill_id': bill_id,
        'semester': semester,
        'total_amount': total_amount,
        'items': bill_items
      })
    return jsonify({'bills': bills, 'list_of_bills': list_of_bills}), 200
  except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      return jsonify({'error': 'Invalid credentials'}), 401
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
      return jsonify({'error': 'Database does not exist'}), 404
    else:
      return jsonify({'error': 'Something went wrong'}), 500
  except Exception as e:
    return jsonify({'error': 'Something went wrong'}), 500
  finally:
    db_connection.close()


@app.route('/api-svfc-get-student-transactions', methods=['POST'])
def get_student_transaction():
  try:
    db_connection = mysql.connector.connect(
      user=os.getenv('USER'),
      password=os.getenv('PASSWORD'),
      port=os.getenv('PORT'),
      database='svfc_finance'
    )
    data = request.get_json()
    student_number = data.get('student_number')
    with db_connection.cursor() as cursor:
      query = "SELECT p.payment_id, p.payment_date, p.amount, b.semester, pm.payment_method_type FROM payments_table p JOIN bills_table b ON p.bill_id = b.bills_id JOIN payment_method pm ON p.payment_method_id = pm.payment_method_id WHERE b.student_number = %s ORDER BY p.payment_date DESC"
      cursor.execute(query, (student_number,))
      rows = cursor.fetchall()
    transactions = []
    for row in rows:
      transactions.append({
        'payment_id': row[0],
        'payment_date': row[1].isoformat(),
        'amount': row[2],
        'semester': row[3],
        'payment_method': row[4]
      })
    return jsonify({'transactions': transactions}), 200
  except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      return jsonify({'error': 'Invalid credentials'}), 401
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
      return jsonify({'error': 'Database does not exist'}), 404
    else:
      error_info = {
        'error': 'Database error',
        'message': str(err.msg) if hasattr(err, 'msg') else 'Unknown error'
      }
      return jsonify(error_info), 500
  except Exception as e:
    return jsonify({'error': 'Something went wrong', 'info': e}), 500


@app.route('/submit-payment', methods=['POST'])
def submit_payment():
  try:
    data = request.get_json()
    bill_id = data.get('bill_id')
    payment_method_name = data.get('payment_method_name')
    amount_paid = data.get('amount_paid')
    if not bill_id or not payment_method_name or not amount_paid:
      return jsonify({'error': 'Missing Fields Detected.'}), 400
    db_connection = mysql.connector.connect(
      user=os.getenv('USER'),
      password=os.getenv('PASSWORD'),
      port=os.getenv('PORT'),
      database='svfc_finance'
    )
    cursor = db_connection.cursor()
    query = "SELECT payment_method_id FROM payment_method WHERE payment_method_type = %s"
    cursor.execute(query, (payment_method_name,))
    payment_method_id = cursor.fetchone()[0]
    insert_in_payments_table_statement = "INSERT INTO payments_table(bill_id, payment_date, amount, payment_method_id) VALUES(%s, NOW(), %s, %s)"
    cursor.execute(insert_in_payments_table_statement, (bill_id, amount_paid, payment_method_id))
    update_bills_table_statement = "UPDATE bills_table SET total_amount = total_amount - %s WHERE bills_id = %s"
    cursor.execute(update_bills_table_statement, (amount_paid, bill_id))
    db_connection.commit()
    cursor.close()
    return jsonify({'message': 'Payment inserted successfully.'}), 200

  except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      return jsonify({'error': 'Invalid credentials'}), 401
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
      return jsonify({'error': 'Database does not exist'}), 404
    else:
      return jsonify({'error': 'Something went wrong'}), 500
  except Exception as e:
    print(e)
    return jsonify({'error': 'Something went wrong'}), 500

@app.route('/payment/bank', methods=['POST'])
def bank():
  form_fields = [
      {
        'id': 'bankName',
        'label': "Your Bank Name",
        'type': 'text',
        'placeholder': "Your Bank Name",
        'name': 'bankName',
        'required': True
      },
      {
        'id': 'bankCode',
        'label': "Your Bank Code",
        'type': 'number',
        'placeholder': "Your Bank Code",
        'name': 'bankCode',
        'required': True
      },
      {
        'id': 'bankNumber',
        'label': 'Your Bank Number',
        'type': 'number',
        'placeholder': 'Your Bank Number',
        'name': 'bankNumber',
        'required': True
      },
      {
        'id': 'name',
        'label': 'Your Name',
        'type': 'text',
        'placeholder': 'Your Name',
        'name': 'name',
        'required': True
      }
    ]
  data = request.get_json()
  bill_id = data.get('bill_id')
  amount_to_be_paid = data.get('amount_to_be_paid')
  payment_method = data.get('payment_method')
  return render_template('bank.html', form_fields=form_fields, bill_id=bill_id, amount_to_be_paid=amount_to_be_paid, payment_method=payment_method)

@app.route('/payment/card', methods=['POST'])
def card():
  data = request.get_json()
  bill_id = data.get('bill_id')
  amount_to_be_paid = data.get('amount_to_be_paid')
  payment_method = data.get('payment_method')
  return render_template('card.html', bill_id=bill_id, amount_to_be_paid=amount_to_be_paid, payment_method=payment_method)

@app.route('/payment/gcash', methods=['POST'])
def gcash():
  data = request.get_json()
  bill_id = data.get('bill_id')
  amount_to_be_paid = data.get('amount_to_be_paid')
  payment_method = data.get('payment_method')
  return render_template('gcash.html', bill_id=bill_id, amount_to_be_paid=amount_to_be_paid, payment_method=payment_method)

@app.route('/success', methods=['GET'])
def success():
  return render_template('payment_success.html')

if __name__ == '__main__':
	socketio.run(app, host='127.0.0.1', port=5000, allow_unsafe_werkzeug=True, debug=True)
