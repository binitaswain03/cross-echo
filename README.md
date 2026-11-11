# CrossEcho: Cross-Modal Assistive Navigation System for the Visually Impaired

**Final-Year B.Tech Computer Science & Engineering Capstone Project**

Full-Stack AI Web Application, Monocular Spatial Perception & Hands-Free Multilingual Voice Guidance

---

## Project Overview

CrossEcho is an assistive navigation system designed to help visually impaired and blind individuals navigate indoor and outdoor environments more independently.

The system analyzes live video from a webcam and combines computer vision, depth estimation, and audio guidance to describe nearby obstacles and their directions.

### Key Features

- **Object Detection:** YOLOv8 detects objects from the 80-class COCO dataset.
- **Distance Estimation:** MiDaS-based depth estimation with metric priors.
- **Direction Guidance:** Provides angles, clock-face positions, and directional sectors.
- **Multilingual Audio:** Supports English, Hindi, and Odia guidance.
- **Voice Commands:** Allows hands-free navigation controls.
- **Camera Switching:** Supports connected camera devices.
- **Local Processing:** Designed to run AI inference locally.
- **SQLite Logging:** Stores navigation and detection records.

## Technology Stack

- **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Login
- **Computer Vision:** YOLOv8, MiDaS, OpenCV, PyTorch
- **Frontend:** HTML5, CSS3, JavaScript, Canvas API
- **Speech:** Web Speech API and pyttsx3
- **Database:** SQLite

## Project Structure

```text
Cross modal/
├── app.py
├── collect_data.py
├── view_db.py
├── database.py
├── schema.sql
├── requirements.txt
├── yolov8n.pt
├── instance/
├── models/
├── vision/
├── depth/
├── tts/
├── auth/
├── routes/
├── static/
└── templates/
```

## Installation and Setup

### 1. Open the project directory

```powershell
cd "C:\Users\swain\Desktop\Cross modal"
```

### 2. Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Run the application

```powershell
python app.py
```

### 5. Open the application

Visit:

```text
http://127.0.0.1:5000
```

Allow camera and microphone permissions if prompted.

## Data Collection

Run the standalone data collection utility:

```powershell
python collect_data.py
```

Press `q` to stop collection.

## Database Inspection

View stored database records using:

```powershell
python view_db.py
```

## Accessibility Controls

The project documents keyboard shortcuts for navigation, camera switching, voice recognition, language selection, and audio controls. Refer to the application implementation for the exact supported shortcuts and commands.

## Contributors and Purpose

Developed as a Final-Year B.Tech Computer Science and Engineering capstone project to explore assistive computer vision, accessible human-computer interaction, and independent mobility.
