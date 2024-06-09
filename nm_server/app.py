from flask import Flask, request, jsonify,send_file,after_this_request
from flask_cors import CORS
from api_request import *
import mysql.connector
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import json
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from base64 import b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# from utils import *

app = Flask(__name__)
CORS(app)

db_config = {
    'user': 'root',
    'password': '807ac496-ff5e-46bd-ae1e-bcd8c09c33e1',
    'host': 'localhost',
    'database': 'med_info_db'
}
@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    res = request_auth(data)
    with open(('./api_resp/'+data["rrn"]+ '.json'), 'w+', encoding='utf-8') as f:
        json.dump(res, f, ensure_ascii=False, indent=4)
        f.close()
    if res['Status'] == "OK":
        return 'Data received', 200
    else:
        return 'FAILED', 400

@app.route('/complete', methods=['POST'])
def complete():
    rrn = request.json.get('rrn')
    f = open('api_resp/'+rrn+ '.json')
    data = json.load(f)

    med = med_info(data['ResultData'],rrn)
    add = add_data_from_json(med, rrn, '-')
    if add == 200 and med['Status'] == "OK":
        return 'Completed', 200 
    else:
        return 'FAILED', 400

@app.route('/medication', methods=['POST'])
def get_medication():
    data = request.json
    rrn = data.get('rrn')

    data = query_database_to_json(rrn)
    data = json.dumps(data, ensure_ascii=False)

    response = app.response_class(
        response=data,
        status=200,
        mimetype='application/json'
    )
    return response 

def add_data_from_json(med_info, user_id, user_name):
    # Read the JSON file
    # with open(json_file_path, 'r', encoding='utf-8') as file:
    #     med_info = json.load(file)

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Insert user information
        cursor.execute(
            "INSERT INTO users (user_id, user_name) VALUES (%s, %s) ON DUPLICATE KEY UPDATE user_name=%s",
            (user_id, user_name, user_name)
        )
        connection.commit()

        # Insert medication information
        for med in med_info['ResultList']:
            cursor.execute(
                "INSERT IGNORE INTO medications (user_id, med_no, date_of_preparation, dispensary, phone_number) VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE med_no=%s",
                (user_id, med['No'], med['DateOfPreparation'], med['Dispensary'], med['PhoneNumber'],med['No'])
            )
            med_id = cursor.lastrowid

            # Insert drug information
            for drug in med['DrugList']:
                cursor.execute(
                    "INSERT IGNORE INTO drugs (med_id, drug_no, effect, code, name, component, quantity, dosage_per_once, daily_dose, total_dosing_days) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (med_id, drug['No'], drug['Effect'], drug['Code'], drug['Name'], drug['Component'], drug['Quantity'], drug['DosagePerOnce'], drug['DailyDose'], drug['TotalDosingDays'])
                )

        connection.commit()
        print("Data submitted successfully")
        return 200

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return 400

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def query_database_to_json(user_id):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return json.dumps({"Error": "User not found"})

        cursor.execute("SELECT * FROM medications WHERE user_id = %s", (user_id,))
        medications = cursor.fetchall()

        result_list = []
        for med in medications:
            cursor.execute("SELECT * FROM drugs WHERE med_id = %s", (med['id'],))
            drugs = cursor.fetchall()
            med_dict = {
                "No": med['med_no'],
                "DateOfPreparation": med['date_of_preparation'].strftime('%Y-%m-%d'),
                "Dispensary": med['dispensary'],
                "PhoneNumber": med['phone_number'],
                "DrugList": [
                    {
                        "No": drug['drug_no'],
                        "Effect": drug['effect'],
                        "Code": drug['code'],
                        "Name": drug['name'],
                        "Component": drug['component'],
                        "Quantity": drug['quantity'],
                        "DosagePerOnce": drug['dosage_per_once'],
                        "DailyDose": drug['daily_dose'],
                        "TotalDosingDays": drug['total_dosing_days']
                    } for drug in drugs
                ]
            }
            result_list.append(med_dict)

        result_json = {
            "ResultList": result_list,
            "ApiTxKey": "some_api_tx_key",  
            "Status": "OK",
            "StatusSeq": 0,
            "ErrorCode": 0,
            "Message": "성공",
            "ErrorLog": None,
            "TargetCode": None,
            "TargetMessage": None,
            "PointBalance": "8900.00"  
        }
        return result_json

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return json.dumps({"Error": str(err)})

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/medications/pdf', methods=['GET'])
def get_medications_pdf():
    rrn = request.args.get('rrn')
    path = rrn + '.pdf'
    if not rrn:
        return 'Missing RRN', 400
    rrn = decrypt_rrn(rrn)
    data = query_database_to_json(rrn)
    generate_pdf_from_json(data,path)
    @after_this_request
    def remove_file(response):
        try:
            os.remove(path)
        except Exception as error:
            app.logger.error("Error removing or closing downloaded file handle", error)
        return response
    return send_file('../'+path, as_attachment=True)

# def decrypt_rrn(encrypted_rrn):
#     key = b'1joonwooseunghonaegamuckneunyak1'  # 32 bytes key
#     iv = b'\x00' * 16  # 16 bytes IV

#     encrypted_rrn_bytes = base64.b64decode(encrypted_rrn)
#     cipher = Cipher(algorithms.AES(key), modes.CFB(iv))
#     decryptor = cipher.decryptor()
#     decrypted_rrn = decryptor.update(encrypted_rrn_bytes) + decryptor.finalize()
    
#     return decrypted_rrn.decode('utf-8')
def decrypt_rrn(rrn):
    # Encryption parameters
    key = b'4f1aaae66406e358'  # 16 bytes key
    iv = b'df1e180949793972'   # 16 bytes IV

    # Encrypted text from Dart output (replace with your actual encrypted text)


    # Decode the base64 encoded encrypted text
    encrypted_bytes = b64decode(rrn)

    # Create the cipher
    cipher = AES.new(key, AES.MODE_CBC, iv)

    # Decrypt and unpad the text
    decrypted_bytes = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
    decrypted_text = decrypted_bytes.decode('utf-8')

    return decrypted_text

# # Example usage:
# encrypted_rrn = 'Your_Encrypted_Base64_RRN'
# print(decrypt_rrn(encrypted_rrn))


def generate_pdf_from_json(data, output_pdf_path):
    pdfmetrics.registerFont(TTFont('NanumGothic', 'Nanum_Gothic/NanumGothic-Regular.ttf'))

    doc = SimpleDocTemplate(output_pdf_path, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name='TitleStyle', parent=styles['Title'], fontName='NanumGothic', fontSize=14)
    normal_style = ParagraphStyle(name='NormalStyle', parent=styles['Normal'], fontName='NanumGothic', fontSize=10)

    title = Paragraph("Medication Information", title_style)
    elements.append(title)

    for med in data['ResultList']:
        med_table_data = [
            [Paragraph("Medication No", normal_style), Paragraph(med['No'], normal_style)],
            [Paragraph("Date of Preparation", normal_style), Paragraph(med['DateOfPreparation'], normal_style)],
            [Paragraph("Dispensary", normal_style), Paragraph(med['Dispensary'], normal_style)],
            [Paragraph("Phone Number", normal_style), Paragraph(med['PhoneNumber'], normal_style)]
        ]

        med_table = Table(med_table_data, colWidths=[150, 350])
        med_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'NanumGothic'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(med_table)

        drug_table_data = [
            ["No", "Effect", "Code", "Name", "Component", "Quantity", "Dosage Per Once", "Daily Dose", "Total Dosing Days"]
        ]
        for drug in med['DrugList']:
            drug_table_data.append([
                Paragraph(drug['No'], normal_style),
                Paragraph(drug['Effect'], normal_style),
                Paragraph(drug['Code'], normal_style),
                Paragraph(drug['Name'], normal_style),
                Paragraph(drug['Component'], normal_style),
                Paragraph(drug['Quantity'], normal_style),
                Paragraph(drug['DosagePerOnce'], normal_style),
                Paragraph(drug['DailyDose'], normal_style),
                Paragraph(drug['TotalDosingDays'], normal_style)
            ])

        drug_table = Table(drug_table_data, colWidths=[30, 60, 60, 80, 80, 50, 60, 50, 60])
        drug_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'NanumGothic'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(drug_table)

        elements.append(Paragraph("<br/><br/>", normal_style))

    doc.build(elements)


@app.route('/add_medication', methods=['POST'])
def add_medication():
    data = request.get_json()
    rrn = data.get('RRN')
    preparation_no = '-'
    preparation_date = data.get('DateOfPreparation')
    if preparation_date == '-' or preparation_date == '':
        preparation_date = '0000-00-00'
    print(preparation_date)
    dispensary = data.get('Dispensary')
    phone_number = '-'
    drug_list = data.get('DrugList', [])

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Insert the medication preparation data into the database
        cursor.execute(
            """
            REPLACE INTO medications (user_id,med_no, date_of_preparation, dispensary, phone_number)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (rrn, preparation_no, preparation_date, dispensary, phone_number)
        )
        preparation_id = cursor.lastrowid

        # Insert each drug in the drug list
        for drug in drug_list:
            cursor.execute(
                """
                REPLACE INTO drugs (med_id, drug_no, effect, code, name, component, quantity, dosage_per_once, daily_dose, total_dosing_days)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    '-',
                    '-',
                    '-',
                    '-',
                    drug['Name'],
                    '-',
                    '-',
                    '-',
                    '-',
                    '-'
                )
            )

        connection.commit()
        return jsonify({"status": "success"}), 200
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=5000)
@app.route("/")
def index():
    return "<h1>Hello!</h1>"
if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)