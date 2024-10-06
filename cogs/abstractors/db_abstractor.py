import mysql.connector
import os
import datetime
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
        cleaninty = cleaninty_abstractor()

        last_transferred = cleaninty.get_last_moved_time(json_string=json)

        sql = (
            "INSERT INTO donors (name, json_data, last_transferred) VALUES (%s, %s, %s)"
        )
        val = (name, json, last_transferred)

        try:
            self.cursor.execute(sql, val)
        except mysql.connector.errors.IntegrityError:
            return

        self.connection.commit()

    def update_donor(self, name, json):
        sql = "DELETE FROM donors WHERE name = %s"

        try:
            self.cursor.execute(sql, (name,))
        except mysql.connector.errors.IntegrityError:
            return

        self.write_donor(name, json)

    def get_donor_json_ready_for_transfer(self):
        utc_time = datetime.datetime.now(datetime.UTC)
        utc_time_ready_for_transfer = int(utc_time.timestamp()) - 604800

        try:
            self.cursor.fetchall()
        except Exception:
            pass

        self.cursor.execute(
            "SELECT * FROM donors WHERE last_transferred < %s ORDER BY last_transferred ASC",
            (utc_time_ready_for_transfer,),
        )
        result = self.cursor.fetchone()

        try:
            self.cursor.fetchall()
        except Exception:
            pass

        return result[0], result[1]

    def read_index(self, table, index_field_name, index):
        try:
            self.cursor.fetchall()
        except Exception:
            pass

        sql = "SELECT * FROM %s WHERE %s = %s"
        val = (table, index_field_name, index)

        try:
            self.cursor.execute(sql, val)
        except mysql.connector.errors.IntegrityError:
            return

        return self.cursor.fetchone()

    def read_table(self, table):
        try:
            self.cursor.fetchall()
        except Exception:
            pass

        self.cursor.execute(f"SELECT * FROM {table}")

        return self.cursor.fetchall()
