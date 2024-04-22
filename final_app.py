from flask import Flask, render_template, Response, request, redirect, url_for
from flask_socketio import SocketIO, emit
import cv2
import face_recognition
import numpy as np
import csv
from datetime import datetime
import os
import time  # Import required for adding delay

app=Flask(__name__)
socketio = SocketIO(app)
camera=cv2.VideoCapture(0)

# Known face encodings and their names
known_face_encodings = []
known_face_names = []

def load_and_encode_faces():
    os.makedirs(f'faces', exist_ok=True)  # Ensure directory for subject exists
    base_directory = 'faces/'
    for person_name in os.listdir(base_directory):
        person_directory = os.path.join(base_directory, person_name)
        if os.path.isdir(person_directory):
            for image_file in os.listdir(person_directory):
                image_path = os.path.join(person_directory, image_file)
                if os.path.isfile(image_path):
                    print(f"Encoding {image_path}")
                    image = face_recognition.load_image_file(image_path)
                    try:
                        face_encoding = face_recognition.face_encodings(image)[0]
                        known_face_encodings.append(face_encoding)
                        known_face_names.append(person_name)
                    except IndexError:
                        print(f"No face found in {image_path}, skipping.")



def initialize_or_update_csv():
    today_column = datetime.now().strftime("%Y-%m-%d")
    file_path = 'attendance.csv'
    if not os.path.isfile(file_path):
        with open(file_path, 'w', newline='') as file:
            fieldnames = ["Student Name", "Score", today_column]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for name in set(known_face_names):
                writer.writerow({"Student Name": name, "Score": "0/1", today_column: "Absent"})
    else:
        with open(file_path, 'r+', newline='') as file:
            reader = csv.DictReader(file)
            fieldnames = reader.fieldnames
            if today_column not in fieldnames:
                fieldnames.append(today_column)
            total_days = len(fieldnames) - 2  # Excluding 'Student Name' and 'Score'
            data = list(reader)
            file.seek(0)
            file.truncate()
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                if today_column not in row:
                    row[today_column] = "Absent"
                attended_days = sum(1 for day in fieldnames[2:] if row.get(day) == "Present")
                row['Score'] = f"{attended_days}/{total_days}"
                writer.writerow(row)

def update_attendance(name):
    file_path = 'attendance.csv'
    today_column = datetime.now().strftime("%Y-%m-%d")
    with open(file_path, 'r+', newline='') as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
        if today_column not in fieldnames:
            fieldnames.append(today_column)
        existing_data = list(reader)
        total_days = len(fieldnames) - 2  # Excluding 'Student Name' and 'Score'
        file.seek(0)
        file.truncate()
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        found = False
        attended_days = 0  # Initialize attended_days
        for row in existing_data:
            if row['Student Name'] == name:
                row[today_column] = "Present"
                found = True
            attended_days = sum(1 for day in fieldnames if day != 'Student Name' and day != 'Score' and row.get(day) == "Present")
            row['Score'] = f"{attended_days}/{total_days}"
            writer.writerow(row)
        if not found:
            new_row = {"Student Name": name, today_column: "Present", "Score": f"1/{total_days}"}
            writer.writerow(new_row)
        if name != "Unknown":
            score = f"{attended_days}/{total_days}"
            # print(f"Emitting for {name} with score {score}")
            socketio.emit('attendance_update', {'name': name, 'score': score}, namespace='/')

video_capture = cv2.VideoCapture(0)
face_locations = []
face_encodings = []
face_names = []
process_this_frame = True

def generate_frames():
    while True:
            
        ## read the camera frame
        success,frame=camera.read()
        if not success:
            break
        else:
            ret, frame = video_capture.read()
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            # if process_this_frame:
            face_locations = face_recognition.face_locations(small_frame)
            face_encodings = face_recognition.face_encodings(small_frame, face_locations)
            face_names = []
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.4)
                name = "Unknown"
                if True in matches:
                    first_match_index = matches.index(True)
                    name = known_face_names[first_match_index]
                face_names.append(name)
                if name != "Unknown":
                    update_attendance(name)
            # process_this_frame = not process_this_frame

            for (top, right, bottom, left), name in zip(face_locations, face_names):
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.rectangle(frame, (left, bottom - 50), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 2, (255, 255, 255), 1)

            ret,buffer=cv2.imencode('.jpg',frame)
            frame=buffer.tobytes()
            yield(b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
def generate_frames_for_capture():
    while True:
            
        ## read the camera frame
        success,frame=camera.read()
        if not success:
            break
        else:
            ret,buffer=cv2.imencode('.jpg',frame)
            frame=buffer.tobytes()

        yield(b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        subject_name = request.form.get('subject_name')
        if subject_name:
            capture_photos(subject_name)
            message = f"Congratulations, {subject_name}, you are registered."
            print(f"Message set: {message}")
            # return redirect(url_for('index'))
        return render_template('register.html', message=message)
    else:
        return render_template('register.html')


def capture_photos(subject_name, num_photos=1):
    cam = cv2.VideoCapture(0)
    photos_taken = 0
    os.makedirs(f'faces/{subject_name}', exist_ok=True)

    while photos_taken < num_photos:
        ret, frame = cam.read()
        if not ret:
            print("Failed to grab frame")
            break
        img_name = f"faces/{subject_name}/{subject_name}_{photos_taken}.png"
        cv2.imwrite(img_name, frame)
        photos_taken += 1
        # time.sleep(5) 

    # cam.release()
    # update_attendance(subject_name)
    # initialize_or_update_csv()
    load_and_encode_faces()
# load_and_encode_faces()

load_and_encode_faces()

@app.route('/video')
def video():
    return Response(generate_frames(),mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/videoforCapture')
def video_for_capturing_photo():
    return Response(generate_frames_for_capture(),mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__=="__main__":
    initialize_or_update_csv()
    socketio.run(app, debug=True)
    