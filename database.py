import mysql.connector
import logging
from datetime import datetime

logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class Database:
    def __init__(self):
        try:
            self.connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="Jijin@12345",
                database="attendance_system"
            )
            self.cursor = self.connection.cursor()
            logging.info("Database connection established")
            self.create_tables()
        except mysql.connector.Error as e:
            logging.error(f"Error connecting to database: {e}")
            raise

    def create_tables(self):
        try:
            # Create tbl_login if not exists
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_login (
                    uname VARCHAR(50) PRIMARY KEY,
                    upass VARCHAR(50) NOT NULL,
                    utype ENUM('Admin', 'Faculty') NOT NULL
                )
            """)
            # Insert default admin and faculty accounts if not present
            self.cursor.execute("SELECT COUNT(*) FROM tbl_login")
            if self.cursor.fetchone()[0] == 0:
                self.cursor.execute("""
                    INSERT INTO tbl_login (uname, upass, utype) VALUES
                    ('admin', 'admin123', 'Admin'),
                    ('faculty', 'fac123', 'Faculty')
                """)
            
            # Create tbl_student if not exists
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_student (
                    S_rollno VARCHAR(20) PRIMARY KEY,
                    S_name VARCHAR(20) NOT NULL,
                    email VARCHAR(50) NOT NULL,
                    phno VARCHAR(20) NOT NULL,
                    dob DATE NOT NULL,
                    batchid VARCHAR(5) NOT NULL
                )
            """)
            
            # Create tbl_attendance if not exists
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS tbl_attendance (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    rollno VARCHAR(20) NOT NULL,
                    fac_id VARCHAR(50) NOT NULL,
                    date DATE NOT NULL,
                    time TIME NOT NULL,
                    FOREIGN KEY (rollno) REFERENCES tbl_student(S_rollno)
                )
            """)
            self.connection.commit()
            logging.info("Database tables created successfully")
        except mysql.connector.Error as e:
            logging.error(f"Error creating tables: {e}")
            raise

    def get_students_attendance_for_date(self, date):
        try:
            query = """
                SELECT s.S_rollno, s.S_name, 
                       CASE 
                           WHEN a.rollno IS NOT NULL THEN 'Present'
                           ELSE 'Absent'
                       END AS status,
                       a.time
                FROM tbl_student s
                LEFT JOIN (
                    SELECT rollno, date, MAX(time) as time
                    FROM tbl_attendance
                    WHERE date = %s
                    GROUP BY rollno, date
                ) a ON s.S_rollno = a.rollno
                ORDER BY s.S_rollno
            """
            self.cursor.execute(query, (date,))
            return self.cursor.fetchall()
        except mysql.connector.Error as e:
            logging.error(f"Error fetching students attendance for {date}: {e}")
            raise

    def validate_login(self, username, password, user_type):
        try:
            query = "SELECT * FROM tbl_login WHERE uname = %s AND upass = %s AND utype = %s"
            self.cursor.execute(query, (username, password, user_type))
            result = self.cursor.fetchone()
            logging.info(f"Login attempt: {username}, {user_type}, {'Success' if result else 'Failed'}")
            return result is not None
        except mysql.connector.Error as e:
            logging.error(f"Error validating login: {e}")
            return False

    def add_student(self, rollno, name, email, phno, dob, batch):
        try:
            self.cursor.execute("SELECT S_rollno FROM tbl_student WHERE S_rollno = %s", (rollno,))
            if self.cursor.fetchone():
                logging.error(f"Duplicate roll number: {rollno}")
                raise ValueError(f"Roll number {rollno} already exists")
            
            query = """
                INSERT INTO tbl_student (S_rollno, S_name, email, phno, dob, batchid)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            self.cursor.execute(query, (rollno, name, email, phno, dob, batch))
            self.connection.commit()
            logging.info(f"Added student: {rollno}")
        except mysql.connector.Error as e:
            logging.error(f"Database error adding student {rollno}: {e}")
            raise
        except ValueError as e:
            raise
        except Exception as e:
            logging.error(f"Unexpected error adding student {rollno}: {e}")
            raise

    def update_student(self, rollno, name, email, phno, dob, batch):
        try:
            query = """
                UPDATE tbl_student
                SET S_name = %s, email = %s, phno = %s, dob = %s, batchid = %s
                WHERE S_rollno = %s
            """
            self.cursor.execute(query, (name, email, phno, dob, batch, rollno))
            self.connection.commit()
            if self.cursor.rowcount == 0:
                logging.warning(f"No student found for rollno: {rollno}")
                raise ValueError(f"No student found with rollno: {rollno}")
            logging.info(f"Updated student: {rollno}")
        except mysql.connector.Error as e:
            logging.error(f"Database error updating student {rollno}: {e}")
            raise
        except ValueError as e:
            raise
        except Exception as e:
            logging.error(f"Unexpected error updating student {rollno}: {e}")
            raise

    def delete_student(self, rollno):
        try:
            self.cursor.execute("DELETE FROM tbl_attendance WHERE rollno = %s", (rollno,))
            self.cursor.execute("DELETE FROM tbl_student WHERE S_rollno = %s", (rollno,))
            self.connection.commit()
            if self.cursor.rowcount == 0:
                logging.warning(f"No student found for rollno: {rollno}")
                raise ValueError(f"No student found with rollno: {rollno}")
            logging.info(f"Deleted student: {rollno}")
        except mysql.connector.Error as e:
            logging.error(f"Database error deleting student {rollno}: {e}")
            raise
        except ValueError as e:
            raise
        except Exception as e:
            logging.error(f"Unexpected error deleting student {rollno}: {e}")
            raise

    def check_rollno_exists(self, rollno):
        try:
            self.cursor.execute("SELECT S_rollno FROM tbl_student WHERE S_rollno = %s", (rollno,))
            return self.cursor.fetchone() is not None
        except mysql.connector.Error as e:
            logging.error(f"Error checking rollno {rollno}: {e}")
            raise

    def check_email_exists(self, email, exclude_rollno=None):
        try:
            query = "SELECT email FROM tbl_student WHERE email = %s"
            params = (email,)
            if exclude_rollno:
                query += " AND S_rollno != %s"
                params = (email, exclude_rollno)
            self.cursor.execute(query, params)
            return self.cursor.fetchone() is not None
        except mysql.connector.Error as e:
            logging.error(f"Error checking email {email}: {e}")
            raise

    def check_phno_exists(self, phno, exclude_rollno=None):
        try:
            query = "SELECT phno FROM tbl_student WHERE phno = %s"
            params = (phno,)
            if exclude_rollno:
                query += " AND S_rollno != %s"
                params = (phno, exclude_rollno)
            self.cursor.execute(query, params)
            return self.cursor.fetchone() is not None
        except mysql.connector.Error as e:
            logging.error(f"Error checking phno {phno}: {e}")
            raise

    def get_all_students(self):
        try:
            query = "SELECT S_rollno, S_name, email, phno, dob, batchid FROM tbl_student ORDER BY S_rollno"
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except mysql.connector.Error as e:
            logging.error(f"Error fetching students: {e}")
            raise

    def mark_attendance(self, rollno, fac_id):
        try:
            query = """
                INSERT INTO tbl_attendance (rollno, fac_id, date, time)
                VALUES (%s, %s, %s, %s)
            """
            current_date = datetime.now().strftime('%Y-%m-%d')
            current_time = datetime.now().strftime('%H:%M:%S')
            self.cursor.execute(query, (rollno, fac_id, current_date, current_time))
            self.connection.commit()
            logging.info(f"Attendance marked for {rollno} by faculty {fac_id}")
        except mysql.connector.Error as e:
            logging.error(f"Error marking attendance: {e}")
            raise

    def get_attendance_report(self, start_date, end_date):
        try:
            query = """
                SELECT s.S_rollno, s.S_name, a.date, a.time
                FROM tbl_attendance a
                JOIN tbl_student s ON a.rollno = s.S_rollno
                WHERE a.date BETWEEN %s AND %s
                ORDER BY a.date, a.time
            """
            self.cursor.execute(query, (start_date, end_date))
            return self.cursor.fetchall()
        except mysql.connector.Error as e:
            logging.error(f"Error generating report: {e}")
            raise

    def update_login_credentials(self, username, new_password, user_type):
        try:
            query = "UPDATE tbl_login SET upass = %s WHERE uname = %s AND utype = %s"
            self.cursor.execute(query, (new_password, username, user_type))
            self.connection.commit()
            if self.cursor.rowcount == 0:
                logging.warning(f"No user found for {username} ({user_type})")
                raise ValueError(f"No user found for {username} ({user_type})")
            logging.info(f"Updated password for {username} ({user_type})")
        except mysql.connector.Error as e:
            logging.error(f"Error updating credentials for {username}: {e}")
            raise

    def __del__(self):
        try:
            self.cursor.close()
            self.connection.close()
            logging.info("Database connection closed")
        except mysql.connector.Error as e:
            logging.error(f"Error closing database connection: {e}")