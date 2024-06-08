import pytest
import json
from nm_server.app import app, db_config
import mysql.connector

@pytest.fixture
def client():
    app.config['TESTING'] = True
    client = app.test_client()

    yield client

def test_submit(client):
    response = client.post('/submit', json={
        'user_id': 'test_user_id',
        'user_name': 'test_user_name',
        'med_info': {
            'ResultList': [
                {
                    'No': 'sample string 1',
                    'DateOfPreparation': '2024-05-26',
                    'Dispensary': 'sample dispensary',
                    'PhoneNumber': '010-1234-5678',
                    'DrugList': [
                        {
                            'No': 'drug string 1',
                            'Effect': 'sample effect',
                            'Code': 'sample code',
                            'Name': 'sample name',
                            'Component': 'sample component',
                            'Quantity': 'sample quantity',
                            'DosagePerOnce': 'sample dosage',
                            'DailyDose': 'sample daily dose',
                            'TotalDosingDays': 'sample total days'
                        }
                    ]
                }
            ]
        }
    })

    assert response.status_code == 200
    assert b'Data submitted successfully' in response.data

def test_get_medications_pdf(client):
    # Insert test data
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    cursor.execute("INSERT INTO users (user_id, user_name, rrn) VALUES (%s, %s, %s)", ('test_user_id', 'test_user_name', '123456-1234567'))
    cursor.execute("INSERT INTO medications (user_id, med_no, date_of_preparation, dispensary, phone_number) VALUES (%s, %s, %s, %s, %s)",
                   ('test_user_id', 'sample string 1', '2024-05-26', 'sample dispensary', '010-1234-5678'))
    med_id = cursor.lastrowid
    cursor.execute("INSERT INTO drugs (med_id, drug_no, effect, code, name, component, quantity, dosage_per_once, daily_dose, total_dosing_days) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                   (med_id, 'drug string 1', 'sample effect', 'sample code', 'sample name', 'sample component', 'sample quantity', 'sample dosage', 'sample daily dose', 'sample total days'))
    connection.commit()
    cursor.close()
    connection.close()

    response = client.get('/medications/pdf?rrn=123456-1234567')

    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/pdf'
