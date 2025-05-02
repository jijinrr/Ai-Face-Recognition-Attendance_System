import tkinter as tk
from tkinter import messagebox, ttk
import logging
import mysql.connector
from database import Database
from face_recog import FaceRecognition
from attendance import AttendanceManager
from report import ReportGenerator
import re
from datetime import datetime
import os

logging.basicConfig(filename='app.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Attendance System")
        self.geometry("800x600")
        try:
            self.db = Database()
            self.fr = FaceRecognition()
            self.am = AttendanceManager(self.db)
            self.rg = ReportGenerator(self.db)
        except Exception as e:
            logging.error(f"Initialization error: {e}")
            messagebox.showerror("Error", f"Failed to initialize application: {e}")
            self.destroy()
            return
        self.frames = {}
        self.create_frames()
        self.show_frame("LoginFrame")

    def create_frames(self):
        self.frames["LoginFrame"] = LoginFrame(self)
        self.frames["RegisterFrame"] = RegisterFrame(self)
        self.frames["AdminFrame"] = AdminFrame(self)
        self.frames["FacultyFrame"] = FacultyFrame(self)
        self.frames["StudentManagementFrame"] = StudentManagementFrame(self)
        self.frames["EditStudentFrame"] = EditStudentFrame(self)
        self.frames["AdminReportFrame"] = AdminReportFrame(self)
        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

    def show_frame(self, frame_name):
        if frame_name in self.frames:
            frame = self.frames[frame_name]
            frame.tkraise()
            if hasattr(frame, 'refresh'):
                frame.refresh()
        else:
            logging.error(f"Frame {frame_name} not found")
            messagebox.showerror("Error", f"Frame {frame_name} not found")

class LoginFrame(tk.Frame):
    def __init__(self, controller):
        super().__init__(controller)
        self.controller = controller
        tk.Label(self, text="Username").grid(row=0, column=0, padx=10, pady=5)
        self.username_entry = tk.Entry(self)
        self.username_entry.grid(row=0, column=1, padx=10, pady=5)
        tk.Label(self, text="Password").grid(row=1, column=0, padx=10, pady=5)
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.grid(row=1, column=1, padx=10, pady=5)
        tk.Label(self, text="User Type").grid(row=2, column=0, padx=10, pady=5)
        self.user_type = ttk.Combobox(self, values=["Admin", "Faculty"], state="readonly")
        self.user_type.grid(row=2, column=1, padx=10, pady=5)
        self.user_type.set("Admin")
        tk.Button(self, text="Login", command=self.login).grid(row=3, column=0, columnspan=2, pady=10)
        tk.Button(self, text="Go to Register", command=lambda: self.controller.show_frame("RegisterFrame")).grid(row=4, column=0, columnspan=2, pady=10)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        user_type = self.user_type.get()
        if not username or not password:
            messagebox.showerror("Error", "Username and password are required")
            return
        try:
            if self.controller.db.validate_login(username, password, user_type):
                messagebox.showinfo("Success", f"Welcome, {username} ({user_type})")
                logging.info(f"User {username} ({user_type}) logged in successfully")
                self.controller.show_frame(f"{user_type}Frame")
                self.username_entry.delete(0, tk.END)
                self.password_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Error", "Invalid credentials")
                logging.warning(f"Failed login attempt for {username} ({user_type})")
        except Exception as e:
            logging.error(f"Login error for {username}: {e}")
            messagebox.showerror("Error", f"Login failed: {e}")

class RegisterFrame(tk.Frame):
    def __init__(self, controller):
        super().__init__(controller)
        self.controller = controller
        self.face_captured = False
        tk.Label(self, text="Roll No").grid(row=0, column=0, padx=10, pady=5)
        self.rollno_entry = tk.Entry(self)
        self.rollno_entry.grid(row=0, column=1, padx=10, pady=5)
        tk.Label(self, text="Name").grid(row=1, column=0, padx=10, pady=5)
        self.name_entry = tk.Entry(self)
        self.name_entry.grid(row=1, column=1, padx=10, pady=5)
        tk.Label(self, text="Email").grid(row=2, column=0, padx=10, pady=5)
        self.email_entry = tk.Entry(self)
        self.email_entry.grid(row=2, column=1, padx=10, pady=5)
        tk.Label(self, text="Phone").grid(row=3, column=0, padx=10, pady=5)
        self.phno_entry = tk.Entry(self)
        self.phno_entry.grid(row=3, column=1, padx=10, pady=5)
        tk.Label(self, text="DOB (YYYY-MM-DD)").grid(row=4, column=0, padx=10, pady=5)
        self.dob_entry = tk.Entry(self)
        self.dob_entry.grid(row=4, column=1, padx=10, pady=5)
        tk.Label(self, text="Batch ID").grid(row=5, column=0, padx=10, pady=5)
        self.batch_entry = tk.Entry(self)
        self.batch_entry.grid(row=5, column=1, padx=10, pady=5)
        tk.Button(self, text="Capture Face Images", command=self.capture_faces).grid(row=6, column=0, padx=10, pady=10)
        tk.Button(self, text="Save Student", command=self.save_student).grid(row=6, column=1, padx=10, pady=10)
        tk.Button(self, text="Back", command=lambda: self.controller.show_frame("AdminFrame")).grid(row=7, column=0, columnspan=2, pady=10)

    def validate_inputs(self, rollno, name, email, phno, dob, batch):
        if not rollno or len(rollno) > 20:
            raise ValueError("Roll number is required and must be 20 characters or less")
        if self.controller.db.check_rollno_exists(rollno):
            raise ValueError("Roll number already exists")
        if not name or len(name) > 20 or not name.replace(" ", "").isalpha():
            raise ValueError("Name is required, must be 20 characters or less, and contain only letters")
        if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email) or len(email) > 50:
            raise ValueError("Valid email is required and must be 50 characters or less")
        if self.controller.db.check_email_exists(email):
            raise ValueError("Email already exists")
        if not phno or not re.match(r"^\d{10}$", phno) or len(phno) > 20:
            raise ValueError("Phone number must be 10 digits")
        if self.controller.db.check_phno_exists(phno):
            raise ValueError("Phone number already exists")
        if not dob or not re.match(r"^\d{4}-\d{2}-\d{2}$", dob):
            raise ValueError("DOB must be in YYYY-MM-DD format")
        try:
            datetime.strptime(dob, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Invalid DOB value")
        if not batch or len(batch) > 5:
            raise ValueError("Batch ID is required and must be 5 characters or less")
        if not self.face_captured:
            raise ValueError("Face images must be captured and verified")
        return True

    def capture_faces(self):
        rollno = self.rollno_entry.get().strip()
        if not rollno:
            messagebox.showerror("Error", "Please enter a roll number")
            logging.error("Capture faces failed: No roll number provided")
            return
        try:
            self.controller.fr.capture_faces(rollno)
            # Verify face data
            face_dir = os.path.join("face_data", rollno)
            if not os.path.exists(face_dir) or len(os.listdir(face_dir)) != 10:
                raise ValueError("Failed to capture 10 valid face images")
            # Verify encodings
            valid_encodings = self.controller.fr.verify_face_data(rollno)
            if not valid_encodings:
                raise ValueError("No valid face encodings found in captured images")
            self.face_captured = True
            messagebox.showinfo("Success", f"Face images captured and verified for rollno: {rollno}")
            logging.info(f"Face images captured and verified for rollno: {rollno}")
        except Exception as e:
            logging.error(f"Error capturing faces for {rollno}: {e}")
            messagebox.showerror("Error", f"Failed to capture faces: {e}")

    def save_student(self):
        rollno = self.rollno_entry.get().strip()
        name = self.name_entry.get().strip()
        email = self.email_entry.get().strip()
        phno = self.phno_entry.get().strip()
        dob = self.dob_entry.get().strip()
        batch = self.batch_entry.get().strip()

        try:
            self.validate_inputs(rollno, name, email, phno, dob, batch)
            self.controller.db.add_student(rollno, name, email, phno, dob, batch)
            self.controller.fr.train_model()
            messagebox.showinfo("Success", f"Student {rollno} registered successfully")
            logging.info(f"Student {rollno} registered successfully")
            self.rollno_entry.delete(0, tk.END)
            self.name_entry.delete(0, tk.END)
            self.email_entry.delete(0, tk.END)
            self.phno_entry.delete(0, tk.END)
            self.dob_entry.delete(0, tk.END)
            self.batch_entry.delete(0, tk.END)
            self.face_captured = False
            self.controller.show_frame("AdminFrame")
        except ValueError as e:
            logging.error(f"Validation error for {rollno}: {e}")
            messagebox.showerror("Error", str(e))
        except mysql.connector.errors.Error as e:
            logging.error(f"Database error for {rollno}: {e}")
            messagebox.showerror("Error", f"Database error: {e}")
        except Exception as e:
            logging.error(f"Unexpected error for {rollno}: {e}")
            messagebox.showerror("Error", f"Failed to register student: {e}")

class AdminFrame(tk.Frame):
    def __init__(self, controller):
        super().__init__(controller)
        self.controller = controller
        tk.Label(self, text="Admin Dashboard", font=("Arial", 16)).grid(row=0, column=0, columnspan=2, pady=10)
        tk.Button(self, text="Register Student", command=lambda: self.controller.show_frame("RegisterFrame")).grid(row=1, column=0, padx=10, pady=5)
        tk.Button(self, text="Manage Students", command=lambda: self.controller.show_frame("StudentManagementFrame")).grid(row=1, column=1, padx=10, pady=5)
        tk.Button(self, text="Generate Report", command=lambda: self.controller.show_frame("AdminReportFrame")).grid(row=2, column=0, padx=10, pady=5)
        tk.Button(self, text="Change Password", command=self.change_password).grid(row=2, column=1, padx=10, pady=5)
        tk.Button(self, text="Logout", command=self.logout).grid(row=3, column=0, columnspan=2, pady=5)

    def change_password(self):
        change_window = tk.Toplevel(self)
        change_window.title("Change Password")
        change_window.geometry("300x200")
        tk.Label(change_window, text="Username").grid(row=0, column=0, padx=10, pady=5)
        username_entry = tk.Entry(change_window)
        username_entry.grid(row=0, column=1, padx=10, pady=5)
        tk.Label(change_window, text="New Password").grid(row=1, column=0, padx=10, pady=5)
        password_entry = tk.Entry(change_window, show="*")
        password_entry.grid(row=1, column=1, padx=10, pady=5)
        tk.Label(change_window, text="User Type").grid(row=2, column=0, padx=10, pady=5)
        user_type = ttk.Combobox(change_window, values=["Admin", "Faculty"], state="readonly")
        user_type.grid(row=2, column=1, padx=10, pady=5)
        user_type.set("Admin")
        tk.Button(change_window, text="Update Password", command=lambda: self.update_password(
            username_entry.get().strip(), password_entry.get().strip(), user_type.get(), change_window
        )).grid(row=3, column=0, columnspan=2, pady=10)

    def update_password(self, username, new_password, user_type, window):
        if not username or not new_password:
            messagebox.showerror("Error", "Username and new password are required")
            return
        try:
            self.controller.db.update_login_credentials(username, new_password, user_type)
            messagebox.showinfo("Success", f"Password updated for {username} ({user_type})")
            window.destroy()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update password: {e}")

    def logout(self):
        self.controller.show_frame("LoginFrame")
        logging.info("User logged out")

class FacultyFrame(tk.Frame):
    def __init__(self, controller):
        super().__init__(controller)
        self.controller = controller
        tk.Label(self, text="Faculty Dashboard", font=("Arial", 16)).grid(row=0, column=0, columnspan=3, pady=10)
        
        # Date input for attendance (default to current day)
        tk.Label(self, text="Select Date (YYYY-MM-DD)").grid(row=1, column=0, padx=5, pady=5)
        self.date_entry = tk.Entry(self)
        self.date_entry.grid(row=1, column=1, padx=5, pady=5)
        self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))  # Default to current date
        tk.Button(self, text="View Attendance", command=self.view_attendance).grid(row=1, column=2, padx=5, pady=5)
        
        # Treeview for attendance list
        self.tree = ttk.Treeview(self, columns=("Roll No", "Name", "Status", "Time"), show="headings")
        self.tree.heading("Roll No", text="Roll No")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Time", text="Time")
        self.tree.column("Roll No", width=100)
        self.tree.column("Name", width=150)
        self.tree.column("Status", width=100)
        self.tree.column("Time", width=100)
        self.tree.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        
        # Buttons for other actions
        tk.Button(self, text="Mark Attendance", command=self.mark_attendance).grid(row=3, column=0, padx=5, pady=5)
        tk.Button(self, text="Change Password", command=self.change_password).grid(row=3, column=1, padx=5, pady=5)
        tk.Button(self, text="Logout", command=self.logout).grid(row=3, column=2, padx=5, pady=5)
        
        # Initial load of current day's attendance
        self.view_attendance()

    def validate_date(self, date_str):
        if not date_str:
            raise ValueError("Date is required")
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            raise ValueError("Date must be in YYYY-MM-DD format")
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Invalid date value")
        return True

    def view_attendance(self):
        date_str = self.date_entry.get().strip()
        try:
            self.validate_date(date_str)
            for item in self.tree.get_children():
                self.tree.delete(item)
            records = self.controller.db.get_students_attendance_for_date(date_str)
            for record in records:
                try:
                    rollno, name, status, time = record
                    # Format time: show "N/A" for Absent students (where time is NULL)
                    time_str = str(time) if time else "N/A"
                    self.tree.insert("", "end", values=(rollno, name, status, time_str))
                except ValueError as e:
                    logging.error(f"Error unpacking record for {date_str}: {e}, record: {record}")
                    continue  # Skip malformed records
            if not records:
                messagebox.showinfo("Info", f"No students registered or no attendance records for {date_str}")
            logging.info(f"Displayed attendance for {date_str}")
        except ValueError as e:
            logging.error(f"Validation error for attendance view: {e}")
            messagebox.showerror("Error", str(e))
        except Exception as e:
            logging.error(f"Error displaying attendance for {date_str}: {e}")
            messagebox.showerror("Error", f"Failed to display attendance: {e}")

    def mark_attendance(self):
        try:
            if not self.controller.fr.known_faces:
                messagebox.showerror("Error", "No students registered with face data. Please register students first.")
                logging.warning("Mark attendance failed: No known faces loaded")
                return
            logging.info("Starting face recognition for attendance")
            students = self.controller.fr.recognize_faces()
            if not students:
                messagebox.showinfo("Info", "No students recognized. Ensure students are registered and face data is valid.")
                logging.info("No students recognized during attendance marking")
                return
            for rollno in students:
                try:
                    self.controller.am.mark_attendance(rollno, "faculty")
                    logging.debug(f"Marked attendance for {rollno}")
                except mysql.connector.errors.IntegrityError as e:
                    if e.errno == 1452:
                        messagebox.showerror("Error", f"Student {rollno} not found in database. Please register the student.")
                        logging.error(f"Foreign key error: Student {rollno} not in tbl_student")
                    else:
                        messagebox.showerror("Error", f"Database error marking attendance for {rollno}: {e}")
                        logging.error(f"Database error for {rollno}: {e}")
                    return
            messagebox.showinfo("Success", f"Attendance marked for: {', '.join(students)}")
            logging.info(f"Attendance marked for students: {', '.join(students)}")
            # Refresh attendance list after marking
            self.view_attendance()
        except Exception as e:
            logging.error(f"Error marking attendance: {e}")
            messagebox.showerror("Error", f"Failed to mark attendance: {e}")

    def change_password(self):
        change_window = tk.Toplevel(self)
        change_window.title("Change Password")
        change_window.geometry("300x200")
        tk.Label(change_window, text="Username").grid(row=0, column=0, padx=10, pady=5)
        username_entry = tk.Entry(change_window)
        username_entry.grid(row=0, column=1, padx=10, pady=5)
        tk.Label(change_window, text="New Password").grid(row=1, column=0, padx=10, pady=5)
        password_entry = tk.Entry(change_window, show="*")
        password_entry.grid(row=1, column=1, padx=10, pady=5)
        tk.Label(change_window, text="User Type").grid(row=2, column=0, padx=10, pady=5)
        user_type = ttk.Combobox(change_window, values=["Admin", "Faculty"], state="readonly")
        user_type.grid(row=2, column=1, padx=10, pady=5)
        user_type.set("Faculty")
        tk.Button(change_window, text="Update Password", command=lambda: self.update_password(
            username_entry.get().strip(), password_entry.get().strip(), user_type.get(), change_window
        )).grid(row=3, column=0, columnspan=2, pady=10)

    def update_password(self, username, new_password, user_type, window):
        if not username or not new_password:
            messagebox.showerror("Error", "Username and new password are required")
            return
        try:
            self.controller.db.update_login_credentials(username, new_password, user_type)
            messagebox.showinfo("Success", f"Password updated for {username} ({user_type})")
            window.destroy()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update password: {e}")

    def logout(self):
        self.controller.show_frame("LoginFrame")
        logging.info("User logged out")

class StudentManagementFrame(tk.Frame):
    def __init__(self, controller):
        super().__init__(controller)
        self.controller = controller
        tk.Label(self, text="Student Management", font=("Arial", 16)).grid(row=0, column=0, columnspan=3, pady=10)
        self.tree = ttk.Treeview(self, columns=("Roll No", "Name", "Email", "Phone", "DOB", "Batch"), show="headings")
        self.tree.heading("Roll No", text="Roll No")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Email", text="Email")
        self.tree.heading("Phone", text="Phone")
        self.tree.heading("DOB", text="DOB")
        self.tree.heading("Batch", text="Batch")
        self.tree.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        tk.Button(self, text="Edit", command=self.edit_student).grid(row=2, column=0, padx=5, pady=5)
        tk.Button(self, text="Delete", command=self.delete_student).grid(row=2, column=1, padx=5, pady=5)
        tk.Button(self, text="Back", command=lambda: self.controller.show_frame("AdminFrame")).grid(row=2, column=2, padx=5, pady=5)
        self.refresh()

    def refresh(self):
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)
            students = self.controller.db.get_all_students()
            for student in students:
                self.tree.insert("", "end", values=student)
        except Exception as e:
            logging.error(f"Error refreshing student list: {e}")
            messagebox.showerror("Error", f"Failed to load students: {e}")

    def edit_student(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a student to edit")
            return
        values = self.tree.item(selected[0])['values']
        self.controller.frames["EditStudentFrame"].set_student(values)
        self.controller.show_frame("EditStudentFrame")

    def delete_student(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a student to delete")
            return
        rollno = self.tree.item(selected[0])['values'][0]
        if messagebox.askyesno("Confirm", f"Delete student {rollno} and all associated data?"):
            try:
                # Delete face data first
                self.controller.fr.delete_face_data(rollno)
                # Delete database records (attendance and student)
                self.controller.db.delete_student(rollno)
                self.controller.fr.train_model()  # Retrain to remove stale encodings
                self.refresh()
                messagebox.showinfo("Success", f"Student {rollno} and all associated data deleted")
                logging.info(f"Student {rollno} deleted by admin, including face data")
            except mysql.connector.errors.Error as e:
                if e.errno == 1451:
                    messagebox.showerror("Error", f"Cannot delete {rollno} due to existing attendance records")
                    logging.error(f"Foreign key error deleting {rollno}: {e}")
                else:
                    messagebox.showerror("Error", f"Database error deleting {rollno}: {e}")
                    logging.error(f"Database error deleting {rollno}: {e}")
            except Exception as e:
                logging.error(f"Error deleting student {rollno}: {e}")
                messagebox.showerror("Error", f"Failed to delete student: {e}")

class EditStudentFrame(tk.Frame):
    def __init__(self, controller):
        super().__init__(controller)
        self.controller = controller
        tk.Label(self, text="Edit Student", font=("Arial", 16)).grid(row=0, column=0, columnspan=2, pady=10)
        tk.Label(self, text="Roll No").grid(row=1, column=0, padx=10, pady=5)
        self.rollno_entry = tk.Entry(self, state="readonly")
        self.rollno_entry.grid(row=1, column=1, padx=10, pady=5)
        tk.Label(self, text="Name").grid(row=2, column=0, padx=10, pady=5)
        self.name_entry = tk.Entry(self)
        self.name_entry.grid(row=2, column=1, padx=10, pady=5)
        tk.Label(self, text="Email").grid(row=3, column=0, padx=10, pady=5)
        self.email_entry = tk.Entry(self)
        self.email_entry.grid(row=3, column=1, padx=10, pady=5)
        tk.Label(self, text="Phone").grid(row=4, column=0, padx=10, pady=5)
        self.phno_entry = tk.Entry(self)
        self.phno_entry.grid(row=4, column=1, padx=10, pady=5)
        tk.Label(self, text="DOB (YYYY-MM-DD)").grid(row=5, column=0, padx=10, pady=5)
        self.dob_entry = tk.Entry(self)
        self.dob_entry.grid(row=5, column=1, padx=10, pady=5)
        tk.Label(self, text="Batch ID").grid(row=6, column=0, padx=10, pady=5)
        self.batch_entry = tk.Entry(self)
        self.batch_entry.grid(row=6, column=1, padx=10, pady=5)
        tk.Button(self, text="Update", command=self.update_student).grid(row=7, column=0, padx=10, pady=10)
        tk.Button(self, text="Back", command=lambda: self.controller.show_frame("StudentManagementFrame")).grid(row=7, column=1, padx=10, pady=10)

    def set_student(self, values):
        self.rollno_entry.config(state="normal")
        self.rollno_entry.delete(0, tk.END)
        self.rollno_entry.insert(0, values[0])
        self.rollno_entry.config(state="readonly")
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, values[1])
        self.email_entry.delete(0, tk.END)
        self.email_entry.insert(0, values[2])
        self.phno_entry.delete(0, tk.END)
        self.phno_entry.insert(0, values[3])
        self.dob_entry.delete(0, tk.END)
        self.dob_entry.insert(0, values[4])
        self.batch_entry.delete(0, tk.END)
        self.batch_entry.insert(0, values[5])

    def validate_inputs(self, rollno, name, email, phno, dob, batch):
        if not name or len(name) > 20 or not name.replace(" ", "").isalpha():
            raise ValueError("Name is required, must be 20 characters or less, and contain only letters")
        if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email) or len(email) > 50:
            raise ValueError("Valid email is required and must be 50 characters or less")
        existing_email = self.controller.db.check_email_exists(email, exclude_rollno=rollno)
        if existing_email:
            raise ValueError("Email already exists")
        if not phno or not re.match(r"^\d{10}$", phno) or len(phno) > 20:
            raise ValueError("Phone number must be 10 digits")
        existing_phno = self.controller.db.check_phno_exists(phno, exclude_rollno=rollno)
        if existing_phno:
            raise ValueError("Phone number already exists")
        if not dob or not re.match(r"^\d{4}-\d{2}-\d{2}$", dob):
            raise ValueError("DOB must be in YYYY-MM-DD format")
        try:
            datetime.strptime(dob, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Invalid DOB value")
        if not batch or len(batch) > 5:
            raise ValueError("Batch ID is required and must be 5 characters or less")
        return True

    def update_student(self):
        rollno = self.rollno_entry.get().strip()
        name = self.name_entry.get().strip()
        email = self.email_entry.get().strip()
        phno = self.phno_entry.get().strip()
        dob = self.dob_entry.get().strip()
        batch = self.batch_entry.get().strip()

        try:
            self.validate_inputs(rollno, name, email, phno, dob, batch)
            self.controller.db.update_student(rollno, name, email, phno, dob, batch)
            messagebox.showinfo("Success", f"Student {rollno} updated successfully")
            logging.info(f"Student {rollno} updated successfully")
            self.controller.show_frame("StudentManagementFrame")
        except ValueError as e:
            logging.error(f"Validation error for {rollno}: {e}")
            messagebox.showerror("Error", str(e))
        except mysql.connector.errors.Error as e:
            logging.error(f"Database error for {rollno}: {e}")
            messagebox.showerror("Error", f"Database error: {e}")
        except Exception as e:
            logging.error(f"Unexpected error for {rollno}: {e}")
            messagebox.showerror("Error", f"Failed to update student: {e}")

class AdminReportFrame(tk.Frame):
    def __init__(self, controller):
        super().__init__(controller)
        self.controller = controller
        tk.Label(self, text="Attendance Report", font=("Arial", 16)).grid(row=0, column=0, columnspan=4, pady=10)
        tk.Label(self, text="Start Date (YYYY-MM-DD)").grid(row=1, column=0, padx=5, pady=5)
        self.start_date_entry = tk.Entry(self)
        self.start_date_entry.grid(row=1, column=1, padx=5, pady=5)
        tk.Label(self, text="End Date (YYYY-MM-DD)").grid(row=1, column=2, padx=5, pady=5)
        self.end_date_entry = tk.Entry(self)
        self.end_date_entry.grid(row=1, column=3, padx=5, pady=5)
        tk.Button(self, text="Generate Report", command=self.generate_report).grid(row=2, column=0, columnspan=4, pady=5)
        self.tree = ttk.Treeview(self, columns=("Roll No", "Name", "Date", "Time"), show="headings")
        self.tree.heading("Roll No", text="Roll No")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Date", text="Date")
        self.tree.heading("Time", text="Time")
        self.tree.grid(row=3, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
        tk.Button(self, text="Generate PDF", command=self.generate_pdf).grid(row=4, column=0, columnspan=2, padx=5, pady=5)
        tk.Button(self, text="Back", command=lambda: self.controller.show_frame("AdminFrame")).grid(row=4, column=2, columnspan=2, padx=5, pady=5)

    def validate_dates(self, start_date, end_date):
        if not start_date or not end_date:
            raise ValueError("Start and end dates are required")
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", start_date) or not re.match(r"^\d{4}-\d{2}-\d{2}$", end_date):
            raise ValueError("Dates must be in YYYY-MM-DD format")
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            if start > end:
                raise ValueError("Start date must be before or equal to end date")
        except ValueError as e:
            if str(e).startswith("Start date"):
                raise
            raise ValueError("Invalid date format or value")
        return True

    def generate_report(self):
        start_date = self.start_date_entry.get().strip()
        end_date = self.end_date_entry.get().strip()
        try:
            self.validate_dates(start_date, end_date)
            for item in self.tree.get_children():
                self.tree.delete(item)
            records = self.controller.db.get_attendance_report(start_date, end_date)
            for record in records:
                self.tree.insert("", "end", values=record)
            if not records:
                messagebox.showinfo("Info", "No attendance records found for the selected date range")
            logging.info(f"Generated attendance report for {start_date} to {end_date}")
        except ValueError as e:
            logging.error(f"Validation error for report: {e}")
            messagebox.showerror("Error", str(e))
        except Exception as e:
            logging.error(f"Error generating report: {e}")
            messagebox.showerror("Error", f"Failed to generate report: {e}")

    def generate_pdf(self):
        start_date = self.start_date_entry.get().strip()
        end_date = self.end_date_entry.get().strip()
        try:
            self.validate_dates(start_date, end_date)
            self.controller.rg.generate_pdf_report(start_date, end_date)
            messagebox.showinfo("Success", f"PDF report generated: attendance_report_{start_date}_to_{end_date}.pdf")
            logging.info(f"PDF report generated for {start_date} to {end_date}")
        except ValueError as e:
            logging.error(f"Validation error for PDF report: {e}")
            messagebox.showerror("Error", str(e))
        except Exception as e:
            logging.error(f"Error generating PDF report: {e}")
            messagebox.showerror("Error", f"Failed to generate PDF report: {e}")