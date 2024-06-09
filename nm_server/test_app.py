import unittest
from flask import Flask, json
from flask_testing import TestCase
from app import app, db_config, add_data_from_json, decrypt_rrn, query_database_to_json, generate_pdf_from_json
import mysql.connector
from unittest.mock import patch, MagicMock
from io import BytesIO

class MyTest(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app

    @patch('app.request_auth')
    def test_submit(self, mock_request_auth):
        mock_request_auth.return_value = {'Status': 'OK'}
        response = self.client.post('/submit', json={
            'rrn': '010101-1234567',
            'other_data': 'test_data'
        })
        self.assertEqual(response.status_code, 200)

    def test_get_medication(self):
        with patch('app.query_database_to_json') as mock_query_db:
            mock_query_db.return_value = {'ResultList': [], 'Status': 'OK'}
            response = self.client.post('/medication', json={'rrn': '010101-1234567'})
            self.assertEqual(response.status_code, 200)

    def test_add_data_from_json(self):
        med_info = {
            'ResultList': [
                {
                    'No': '1',
                    'DateOfPreparation': '2024-04-26',
                    'Dispensary': 'Test Dispensary',
                    'PhoneNumber': '1234567890',
                    'DrugList': [
                        {
                            'No': '1',
                            'Effect': 'Test Effect',
                            'Code': '123',
                            'Name': 'Test Drug',
                            'Component': 'Test Component',
                            'Quantity': '10',
                            'DosagePerOnce': '1',
                            'DailyDose': '2',
                            'TotalDosingDays': '5'
                        }
                    ]
                }
            ]
        }
        with patch('mysql.connector.connect') as mock_connect:
            mock_connection = MagicMock()
            mock_connect.return_value = mock_connection
            mock_cursor = mock_connection.cursor.return_value
            mock_cursor.lastrowid = 1

            result = add_data_from_json(med_info, '010101-1234567', 'John Doe')
            self.assertEqual(result, 200)

    def test_decrypt_rrn(self):
        encrypted_rrn = 'fPscGzYaIU39fbN4v00DVQ=='  # Replace with your actual encrypted text
        decrypted_rrn = decrypt_rrn(encrypted_rrn)
        self.assertEqual(decrypted_rrn, '980929-1222518')  # Replace with expected decrypted RRN


    def test_generate_pdf_from_json(self):
        data = {
            'ResultList': [
                {
                    'No': '1',
                    'DateOfPreparation': '2024-04-26',
                    'Dispensary': 'Test Dispensary',
                    'PhoneNumber': '1234567890',
                    'DrugList': [
                        {
                            'No': '1',
                            'Effect': 'Test Effect',
                            'Code': '123',
                            'Name': 'Test Drug',
                            'Component': 'Test Component',
                            'Quantity': '10',
                            'DosagePerOnce': '1',
                            'DailyDose': '2',
                            'TotalDosingDays': '5'
                        }
                    ]
                }
            ]
        }
        output_pdf_path = 'test_med_info.pdf'
        generate_pdf_from_json(data, output_pdf_path)
        with open(output_pdf_path, 'rb') as f:
            self.assertTrue(f.read())

if __name__ == '__main__':
    unittest.main()
