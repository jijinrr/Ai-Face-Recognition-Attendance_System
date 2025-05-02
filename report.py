from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import logging
from datetime import datetime

logging.basicConfig(filename='app.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class ReportGenerator:
    def __init__(self, db):
        self.db = db

    def generate_pdf_report(self, start_date, end_date):
        try:
            # Fetch attendance records
            records = self.db.get_attendance_report(start_date, end_date)
            if not records:
                logging.warning(f"No attendance records found for {start_date} to {end_date}")
                return

            # Create PDF
            file_name = f"attendance_report_{start_date}_to_{end_date}.pdf"
            doc = SimpleDocTemplate(file_name, pagesize=letter)
            elements = []

            # Styles
            styles = getSampleStyleSheet()
            title = Paragraph(f"Attendance Report: {start_date} to {end_date}", styles['Title'])
            elements.append(title)
            elements.append(Spacer(1, 12))

            # Table data
            data = [["Roll No", "Name", "Date", "Time"]]
            for record in records:
                data.append(list(record))

            # Create table
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(table)

            # Build PDF
            doc.build(elements)
            logging.info(f"Generated PDF report: {file_name}")
        except Exception as e:
            logging.error(f"Error generating PDF report for {start_date} to {end_date}: {e}")
            raise