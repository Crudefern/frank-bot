import mysql.connector
import os
from dotenv import load_dotenv
from .cleaninty_abstractor import cleaninty_abstractor


class mySQL:
    def __init__(self):
        load_dotenv()
        self.connection = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASS"),
            database=os.getenv("MYSQL_DB"),
        )
        self.cursor = self.connection.cursor()

    def exit(self):
        self.connection.commit()
        self.connection.close()
        self.cursor.close()


    def write_donor(self, name, json):
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS donors (name VARCHAR(255) PRIMARY KEY, json_data VARCHAR(2048), last_transferred INT(12))"
        )
        cleaninty = cleaninty_abstractor()

        last_transferred = cleaninty.get_last_moved_time(json_string=json)
        sql = "INSERT INTO donors (name, json_data, last_transferred) VALUES (%s, %s, %s)"
        val = (name, json, last_transferred)
        try:
            self.cursor.execute(sql, val)
        except mysql.connector.errors.IntegrityError:
            return
        self.connection.commit()


        

    def read_index(self, table, index):
        pass