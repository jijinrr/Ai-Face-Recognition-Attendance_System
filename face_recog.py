import cv2
import os
import face_recognition
import numpy as np
from collections import defaultdict
import logging

logging.basicConfig(filename='app.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class FaceRecognition:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        if self.face_cascade.empty():
            logging.error("Failed to load face cascade classifier")
            raise ValueError("Failed to load face cascade classifier")
        self.known_faces = []
        self.known_names = []
        self.load_known_faces()

    def load_known_faces(self):
        self.known_faces = []
        self.known_names = []
        face_data_dir = "face_data"
        if not os.path.exists(face_data_dir):
            logging.warning("Face data directory not found")
            return
        for rollno in os.listdir(face_data_dir):
            rollno_path = os.path.join(face_data_dir, rollno)
            if os.path.isdir(rollno_path):
                for img_name in os.listdir(rollno_path):
                    img_path = os.path.join(rollno_path, img_name)
                    try:
                        image = face_recognition.load_image_file(img_path)
                        encodings = face_recognition.face_encodings(image)
                        if encodings:
                            self.known_faces.append(encodings[0])
                            self.known_names.append(rollno)
                            logging.debug(f"Loaded encoding for {img_path}")
                        else:
                            logging.warning(f"No face encodings found in {img_path}")
                    except Exception as e:
                        logging.error(f"Error loading face encoding for {img_path}: {e}")
        logging.info(f"Loaded {len(self.known_faces)} known faces from {len(set(self.known_names))} students")

    def capture_faces(self, rollno):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            logging.error("Failed to open webcam")
            raise ValueError("Failed to open webcam")
        
        face_dir = os.path.join("face_data", rollno)
        if os.path.exists(face_dir):
            import shutil
            shutil.rmtree(face_dir)
        os.makedirs(face_dir)
        
        count = 0
        max_images = 10
        try:
            while count < max_images:
                ret, frame = cap.read()
                if not ret:
                    logging.error("Failed to capture frame from webcam")
                    raise ValueError("Failed to capture frame")
                
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
                
                for (x, y, w, h) in faces:
                    face_img = frame[y:y+h, x:x+w]
                    rgb_face = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
                    encodings = face_recognition.face_encodings(rgb_face)
                    if encodings:
                        cv2.imwrite(os.path.join(face_dir, f"{count}.jpg"), face_img)
                        count += 1
                        logging.debug(f"Captured face image {count} for {rollno}")
                
                cv2.putText(frame, f"Captured: {count}/{max_images}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.imshow("Capturing Faces", frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            if count < max_images:
                logging.warning(f"Only captured {count} face images for {rollno}")
                raise ValueError(f"Only captured {count} face images. Need {max_images}.")
            
            logging.info(f"Captured {count} face images for {rollno}")
        finally:
            cap.release()
            cv2.destroyAllWindows()

    def verify_face_data(self, rollno):
        face_dir = os.path.join("face_data", rollno)
        if not os.path.exists(face_dir):
            logging.error(f"Face data directory not found for {rollno}")
            return False
        valid_encodings = False
        for img_name in os.listdir(face_dir):
            img_path = os.path.join(face_dir, img_name)
            try:
                image = face_recognition.load_image_file(img_path)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    valid_encodings = True
                else:
                    logging.warning(f"No face encodings found in {img_path}")
            except Exception as e:
                logging.error(f"Error verifying face encoding for {img_path}: {e}")
                return False
        return valid_encodings

    def recognize_faces(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            logging.error("Failed to open webcam")
            raise ValueError("Failed to open webcam")
        
        recognized_counts = defaultdict(int)
        confidence_threshold = 5
        max_frames = 300
        frame_count = 0
        try:
            while frame_count < max_frames:
                ret, frame = cap.read()
                if not ret:
                    logging.error("Failed to capture frame from webcam")
                    raise ValueError("Failed to capture frame")
                
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_frame)
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                
                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                    matches = face_recognition.compare_faces(self.known_faces, face_encoding, tolerance=0.6)
                    name = "Unknown"
                    if True in matches:
                        first_match_index = matches.index(True)
                        name = self.known_names[first_match_index]
                        recognized_counts[name] += 1
                        logging.debug(f"Recognized {name} at frame {frame_count}, count: {recognized_counts[name]}")
                    
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.putText(frame, f"{name} ({recognized_counts[name]})", (left, top-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                
                cv2.imshow("Face Recognition", frame)
                
                for name, count in recognized_counts.items():
                    if count >= confidence_threshold:
                        logging.info(f"Confident recognition of {name} after {count} detections")
                        cap.release()
                        cv2.destroyAllWindows()
                        return [name]
                
                frame_count += 1
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            logging.info("No students recognized within max frames")
            return []
        finally:
            cap.release()
            cv2.destroyAllWindows()

    def delete_face_data(self, rollno):
        face_dir = os.path.join("face_data", rollno)
        try:
            if os.path.exists(face_dir):
                import shutil
                shutil.rmtree(face_dir)
                logging.info(f"Deleted face data directory for {rollno}")
            else:
                logging.warning(f"Face data directory not found for {rollno}")
        except Exception as e:
            logging.error(f"Error deleting face data for {rollno}: {e}")
            raise

    def train_model(self):
        self.load_known_faces()
        logging.info("Face recognition model retrained")