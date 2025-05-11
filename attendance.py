import logging
from datetime import datetime

logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class AttendanceManager:
    def __init__(self, db):
        self.db = db
    
    def mark_attendance(self, rollno, fac_id, subject, semester, start_time, end_time):
        try:
            current_time = datetime.now().time()
            start = datetime.strptime(start_time, '%H:%M').time()
            end = datetime.strptime(end_time, '%H:%M').time()
            if not (start <= current_time <= end):
                raise ValueError("Attendance marking is only allowed within the selected time interval")
            self.db.mark_attendance(rollno, fac_id, subject, semester)
            logging.info(f"Attendance marked for {rollno} by faculty {fac_id} for {subject}, {semester}")
        except ValueError as e:
            logging.error(f"Timeout error marking attendance for {rollno}: {e}")
            raise
        except Exception as e:
            logging.error(f"Error marking attendance for {rollno}: {e}")
            raise