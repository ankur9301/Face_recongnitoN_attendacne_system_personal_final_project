# Automated Facial Recognition-based Attendance System

## Overview
This project implements an automated facial recognition-based attendance system to streamline the process of marking attendance. The system leverages modern facial recognition technology to automate attendance marking, enhancing accuracy and efficiency.

## Technology Stack
- **Flask**: Web framework for serving HTML pages and handling HTTP requests.
- **Flask-SocketIO**: Enables real-time communication for dynamic updates.
- **OpenCV**: Captures and processes real-time video streams from a webcam.
- **face_recognition**: Performs facial detection and recognition tasks.
- **CSV**: Manages attendance records in a CSV file.
- **os**: Handles directory creation and file management.
- **datetime**: Manages date-based operations for attendance tracking.
- **numpy**: Supports numerical operations for image processing.

## Features
- Real-time facial recognition to automatically mark attendance.
- Web-based interface for viewing live attendance updates.
- Robust handling of multiple faces in different lighting conditions.
- CSV-based storage for attendance records, allowing for easy export and analysis.

## Installation
1. Clone this repository to your local machine.
2. Install the required dependencies 
3. Ensure you have a webcam connected to your system.

## Usage
1. Start the Flask server by running `final_app.py`.
2. Open a web browser and navigate to `http://localhost:5000`.
3. Register new faces by entering a name and capturing a photo.
4. Use the `/video` endpoint to stream real-time video and mark attendance based on recognized faces.
5. Check the attendance CSV file for recorded data.

## Future Improvements
- Integration with advanced machine learning models for improved accuracy.
- Enhanced scalability for larger datasets.
- More extensive handling of varied lighting conditions.




