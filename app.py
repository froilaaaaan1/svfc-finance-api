from flask import Flask, request, jsonify
from flask_mail import Mail, Message
import os
from flask_cors import CORS
import mysql.connector
from mysql.connector import errorcode
from dotenv import load_dotenv
import time

load_dotenv()

app = Flask(__name__)

CORS(app)

@app.route('/api-svfc-send-feedback', methods=['POST'])
def send_feedback():
  try:
    data = request.get_json()
    student_number = data.get('student_number')
    content = data.get('content')

    if not student_number or not content:
      return jsonify({'error': 'Please provide student_number and content'}), 400
    
    db_connection = mysql.connector.connect(
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
    
  except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      return jsonify({'error': 'Invalid credentials'}), 401
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
      return jsonify({'error': 'Database does not exist'}), 404
    else:
      return jsonify({'error': 'Something went wrong'}), 500
  except Exception as e:
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

@app.route('/api-svfc-post-student-bill', methods=['POST'])
def post_student_bill():
  try:
    unit_total = 0
    data = request.get_json()
    student_number = data.get('student_number')
    number_of_units = data.get('number_of_units')
    semester = data.get('semester')
    internet_connectivity = data.get('internet_connectivity')
    modules_ebook = data.get('modules_ebook')
    portal = data.get('portal')
    e_library = data.get('e_library')
    admission_registration = data.get('admission_registration')
    library = data.get('library')
    student_org = data.get('student_org')
    medical_dental = data.get('medical_dental')
    guidance = data.get('guidance')
    student_affairs = data.get('student_affairs')
    org_t_shirt = data.get('org_t_shirt')
    school_uniform_1_set = data.get('school_uniform_1_set')
    pe_activity_uniform_1_set = data.get('pe_activity_uniform_1_set')
    major_uniform_1_set = data.get('major_uniform_1_set')
    major_laboratory = data.get('major_laboratory')
    insurance = data.get('insurance')
    students_development_programs_activities = data.get('students_development_programs_activities')
    misc_fees = data.get('misc_fees', [])
    
    item_data = {
      'internet_connectivity': internet_connectivity,
      'modules_ebook': modules_ebook,
      'portal': portal,
      'e_library': e_library,
      'admission_registration': admission_registration,
      'library': library,
      'student_org': student_org,
      'medical_dental': medical_dental,
      'guidance': guidance,
      'student_affairs': student_affairs,
      'org_t_shirt': org_t_shirt,
      'school_uniform_1_set': school_uniform_1_set,
      'pe_activity_uniform_1_set': pe_activity_uniform_1_set,
      'major_uniform_1_set': major_uniform_1_set,
      'major_laboratory': major_laboratory,
      'insurance': insurance,
      'students_development_programs_activities': students_development_programs_activities
    }
    if misc_fees:
      for item in misc_fees:
        if not item.get('remarks'):
          return jsonify({'error': 'Remarks is required for every misc fee item'}), 400
    
    if not student_number or not internet_connectivity or not modules_ebook or not portal or not e_library or not admission_registration or not library or not student_org or not medical_dental or not guidance or not student_affairs or not org_t_shirt or not school_uniform_1_set or not pe_activity_uniform_1_set or not major_uniform_1_set or not major_laboratory or not insurance or not students_development_programs_activities:
      return jsonify({'error': 'Missing Fields Detected.'}), 400
    db_connection = mysql.connector.connect(
      user=os.getenv('USER'),
      password=os.getenv('PASSWORD'),
      port=os.getenv('PORT'),
      database='svfc_finance'
    )
    cursor = db_connection.cursor()
    query = "SELECT DISTINCT semester FROM bills_table WHERE student_number = %s"
    cursor.execute(query, (student_number,))
    rows = cursor.fetchall()
    semesters_with_bills = {row[0] for row in rows}
    if semester in semesters_with_bills:
      return jsonify({'error': 'Semester already billed.'}), 400

    unit_total = int(number_of_units) * 700
    other_fees_total = sum(int(item[1]) for item in data.items() if item[0] != 'student_number' and item[0] != 'number_of_units' and item[0] != 'misc_fees' and item[0] != 'semester')
    misc_total = sum(int(item['amount']) for item in misc_fees)
    grand_total = other_fees_total + misc_total + unit_total
    insert_in_bills_table_statement = "INSERT INTO bills_table(student_number, semester, total_amount) VALUES(%s, %s, %s)"
    cursor.execute(insert_in_bills_table_statement, (student_number, semester, grand_total))
    bill_id = cursor.lastrowid
    
    insert_in_bill_items_table_statement = "INSERT INTO bill_items_table (bill_id, item_name, amount, remarks) VALUES (%s, %s, %s, %s)"
    for item in misc_fees:
      cursor.execute(insert_in_bill_items_table_statement, (bill_id, 'misc', int(item['amount']), item['remarks']))
    
    item_data = {key: value for key, value in data.items() if key not in ['student_number', 'number_of_units', 'misc_fees', 'semester']}
    for item_name, amount in item_data.items():
      cursor.execute(insert_in_bill_items_table_statement, (bill_id, item_name, int(amount), ''))
    
    db_connection.commit()
    cursor.close()
    return jsonify({'message': 'Bill inserted successfully.'}), 200
  except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      return jsonify({'error': 'Invalid credentials'}), 401
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
      return jsonify({'error': 'Database does not exist'}), 404
    else:
      return jsonify({'error': 'Something went wrong'}), 500
  except Exception as e:
    return jsonify({'error': 'Something went wrong'}), 500
  

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
      query = "SELECT b.bills_id, p.payment_date, p.amount, b.semester, pm.payment_method_type FROM payments_table p JOIN bills_table b ON p.bill_id = b.bills_id JOIN payment_method pm ON p.payment_method_id = pm.payment_method_id WHERE b.student_number = %s"
      cursor.execute(query, (student_number,))
      rows = cursor.fetchall()
    transactions = []
    time.sleep(2)
    for row in rows:
      transactions.append({
        'bill_id': row[0],
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


if __name__ == '__main__':
	app.run(debug=True)