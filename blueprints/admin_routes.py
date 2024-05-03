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


@admin_routes.route('/dashboard/statistics/total_transactions', methods=['GET'])
def get_total_transactions():
  try:
    connection = connect(
      user=os.getenv('USER'),
      password=os.getenv('PASSWORD'),
      port=os.getenv('PORT'),
      database='svfc_finance'
    )
    total_amount = 0
    with connection.cursor() as cursor:
      cursor.execute("""SELECT SUM(amount) FROM payments_table""")
      total_amount = cursor.fetchone()[0]
    connection.close()
    # "{:,.2f}".format(total_amount)
    total_amount = f'{total_amount:,.2f}'
    return make_response(jsonify({'total_amount': total_amount}), 200)
  except Error as e:
    logger.error(f'Error: {e}')
    return make_response(jsonify({'error': str(e)}), 500)

@admin_routes.route('/dashboard/transactions/all', methods=['GET'])
def get_all_transactions():
  try:
    connection = connect(
      user=os.getenv('USER'),
      password=os.getenv('PASSWORD'),
      port=os.getenv('PORT'),
      database='svfc_finance'
    )
    transactions = []
    with connection.cursor() as cursor:
      cursor.execute("""SELECT pt.amount , bt.semester, ut.user_number, pm.payment_method_type, pt.payment_date
                FROM payments_table pt
                JOIN bills_table bt ON pt.bill_id = bt.bills_id
                JOIN users_table ut ON bt.student_number = ut.user_number
                JOIN payment_method pm ON pm.payment_method_id = pt.payment_method_id""")
      for row in cursor.fetchall():
        transactions.append({
          'amount': row[0],
          'semester': row[1],
          'student_number': row[2],
          'payment_method': row[3],
          'payment_date': row[4]
        })
    connection.close()
    return make_response(jsonify(transactions), 200)
  except Error as e:
    logger.error(f'Error: {e}')
    return make_response(jsonify({'error': str(e)}), 500)

@admin_routes.route('/dashboard/post-bill', methods=['POST'])
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
          return jsonify({'message': 'Remarks is required for every misc fee item'}), 400

    if not student_number or not internet_connectivity or not modules_ebook or not portal or not e_library or not admission_registration or not library or not student_org or not medical_dental or not guidance or not student_affairs or not org_t_shirt or not school_uniform_1_set or not pe_activity_uniform_1_set or not major_uniform_1_set or not major_laboratory or not insurance or not students_development_programs_activities:
      return jsonify({'message': 'Missing Fields Detected.'}), 400
    db_connection = connect(
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
      return jsonify({'message': 'Semester already billed.'}), 400

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
  except Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      return jsonify({'message': 'Invalid credentials'}), 401
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
      return jsonify({'message': 'Database does not exist'}), 404
    else:
      return jsonify({'message': 'Something went wrong'}), 500
  except Exception as e:
    return jsonify({'message': str(e)}), 500

@admin_routes.route('/api/get_five_recent_payment', methods=['GET'])
def get_five_recent_payment():
  try:
    connection = connect(
      user=os.getenv('USER'),
      password=os.getenv('PASSWORD'),
      port=os.getenv('PORT'),
      database='svfc_finance'
    )
    with connection.cursor() as cursor:
      cursor.execute("""SELECT pt.amount, bt.semester, ut.user_number, pm.payment_method_type, pt.payment_date
                FROM payments_table pt
                JOIN bills_table bt ON pt.bill_id = bt.bills_id
                JOIN users_table ut ON bt.student_number = ut.user_number
                JOIN payment_method pm ON pm.payment_method_id = pt.payment_method_id
                ORDER BY pt.payment_date DESC LIMIT 5""")
      transactions = []
      for row in cursor.fetchall():
        transactions.append({
          'amount': row[0],
          'semester': row[1],
          'student_number': row[2],
          'payment_method': row[3],
          'payment_date': row[4]
        })
    connection.close()
    return make_response(jsonify(transactions), 200)
  except Error as e:
    logger.error(f'Error: {e}')
    return make_response(jsonify({'error': str(e)}), 500)
