import mysql.connector
from mysql.connector import errorcode

# MySQL configuration
db_config = {
    'user': 'root',
    'password': '807ac496-ff5e-46bd-ae1e-bcd8c09c33e1',
    'host': 'localhost'
}

# Database and table creation queries
DB_NAME = 'med_info_db'

TABLES = {}
TABLES['users'] = (
    "CREATE TABLE `users` ("
    "  `id` INT AUTO_INCREMENT PRIMARY KEY,"
    "  `user_id` VARCHAR(50) NOT NULL,"
    "  `user_name` VARCHAR(100) NOT NULL,"
    "  UNIQUE (`user_id`)"
    ") ENGINE=InnoDB")

TABLES['medications'] = (
    "CREATE TABLE `medications` ("
    "  `id` INT AUTO_INCREMENT PRIMARY KEY,"
    "  `user_id` VARCHAR(50) NOT NULL,"
    "  `med_no` VARCHAR(50),"
    "  `date_of_preparation` DATE,"
    "  `dispensary` VARCHAR(100),"
    "  `phone_number` VARCHAR(20),"
    "  FOREIGN KEY (`user_id`) REFERENCES `users`(`user_id`)"
    ") ENGINE=InnoDB")

TABLES['drugs'] = (
    "CREATE TABLE `drugs` ("
    "  `id` INT AUTO_INCREMENT PRIMARY KEY,"
    "  `med_id` INT NOT NULL,"
    "  `drug_no` VARCHAR(50),"
    "  `effect` VARCHAR(100),"
    "  `code` VARCHAR(50),"
    "  `name` VARCHAR(100),"
    "  `component` VARCHAR(100),"
    "  `quantity` VARCHAR(50),"
    "  `dosage_per_once` VARCHAR(50),"
    "  `daily_dose` VARCHAR(50),"
    "  `total_dosing_days` VARCHAR(50),"
    "  FOREIGN KEY (`med_id`) REFERENCES `medications`(`id`)"
    ") ENGINE=InnoDB")

# Connect to MySQL server and create database
def create_database(cursor):
    try:
        cursor.execute(
            f"CREATE DATABASE {DB_NAME} DEFAULT CHARACTER SET 'utf8'")
    except mysql.connector.Error as err:
        print(f"Failed creating database: {err}")
        exit(1)

def create_tables(cursor):
    for table_name in TABLES:
        table_description = TABLES[table_name]
        try:
            print(f"Creating table {table_name}: ", end='')
            cursor.execute(table_description)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                print("already exists.")
            else:
                print(err.msg)
        else:
            print("OK")

def main():
    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()
        cursor.execute(f"USE {DB_NAME}")
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            create_database(cursor)
            cnx.database = DB_NAME
        else:
            print(err)
            exit(1)

    create_tables(cursor)

    cursor.close()
    cnx.close()

if __name__ == '__main__':
    main()
