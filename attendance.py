import logging

logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class AttendanceManager:
    def __init__(self, db):
        self.db = db
    
    def mark_attendance(self, rollno, fac_id):
        try:
            self.db.mark_attendance(rollno, fac_id)
            logging.info(f"Attendance marked for {rollno} by faculty {fac_id}")
        except Exception as e:
            logging.error(f"Error marking attendance for {rollno}: {e}")
            raise