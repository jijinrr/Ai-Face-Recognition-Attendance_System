import logging
from datetime import datetime
import mysql.connector
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class ReportGenerator:
    def __init__(self, db):
        self.db = db

    def generate_pdf_report(self, start_date, end_date, subject, semester):
        try:
            records = self.db.get_attendance_report(start_date, end_date, subject, semester)
            if not records:
                logging.warning(f"No records found for report: {start_date} to {end_date}, {subject}, {semester}")
                raise ValueError("No attendance records found for the selected criteria")
            
            filename = f"attendance_report_{start_date}_to_{end_date}_{subject}_{semester}.pdf"
            doc = SimpleDocTemplate(filename, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []

            # Title
            title = Paragraph(f"Attendance Report: {start_date} to {end_date}<br/>Subject: {subject}<br/>Semester: {semester}", styles['Title'])
            elements.append(title)

            # Table data
            data = [['Roll No', 'Name', 'Date', 'Time']]
            for record in records:
                rollno, name, date, time = record
                data.append([rollno, name, str(date), str(time)])

            # Create table
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)

            # Build PDF
            doc.build(elements)
            logging.info(f"Generated PDF report: {filename}")
        except mysql.connector.Error as e:
            logging.error(f"Database error generating PDF report: {e}")
            raise
        except Exception as e:
            logging.error(f"Error generating PDF report: {e}")
            raise