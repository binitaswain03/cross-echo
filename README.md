# CrossEcho: Cross-Modal Assistive Navigation System for the Visually Impaired

### Final-Year B.Tech Computer Science & Engineering Capstone Project
**Full-Stack AI Web Application, Monocular Spatial Perception & Hands-Free Multilingual Voice Guidance**

---

## 1. Project Overview & Abstract

**CrossEcho** is an advanced assistive navigation system engineered to empower visually impaired and blind individuals to navigate both indoor and outdoor environments safely and independently. 

By analyzing live video streams captured from standard wearable or handheld webcams, CrossEcho combines deep-learning computer vision with spatial depth estimation to transform visual scenes into real-time, localized auditory navigation cues.

### Key System Capabilities:
- **Full 80-Class Object Detection (YOLOv8)**: Detects persons, vehicles, obstacles, and everyday household items (including mobile phones, sofas, chairs, tables, laptops, bottles, and remotes) with optimized sensitivity thresholds.
- **Metric Distance Estimation (MiDaS + Metric Priors)**: Fuses MiDaS relative inverse disparity maps with camera pinhole geometry and physical dimensional priors, providing accurate distance measurements from 0.3m to 7.5m.
- **Granular Angle & Clock Direction ("More Left / Right")**: Computes horizontal Field-of-View angles in degrees (e.g., `-32°`), clock-face positions (e.g., *10 o'clock*, *12 o'clock*), and 7 distinct navigational sectors (*Far Left*, *Left*, *Slight Left*, *Straight Ahead*, *Slight Right*, *Right*, *Far Right*).
- **Multilingual Audio Guidance**: Delivers natural spoken alerts in **English**, **Hindi (हिन्दी)**, and **Odia (ଓଡ଼ିଆ)** with native script rendering and phonetic fallbacks.
- **Hands-Free Interactive Voice Commands**: Allows users to control navigation, switch camera devices, switch languages, and request scene status entirely via voice without needing a keyboard or mouse.
- **Hardware Camera Switching**: Seamlessly cycles between laptop webcams, external USB cameras, and virtual cameras on-the-fly via voice command or keypress.
- **100% Offline Capability**: Runs all neural network models and speech processing locally on-device without third-party cloud API dependencies or internet requirements.
- **Persistent SQLite Audit Logging**: Automatically records detection sessions, distances, directions, and obstacle frequencies into an SQLite database with a dedicated command-line inspection tool (`view_db.py`).

---

## 2. Directory Structure

```
Cross modal/
├── app.py                      # Flask main application server & AI pipeline coordinator
├── collect_data.py             # Standalone dataset collection utility for researchers
├── view_db.py                  # CLI database viewer for SQLite tables and detection logs
├── database.py                 # SQLite helper utilities & schema initialization
├── schema.sql                  # Raw SQL table definitions (users, navigation_history, settings)
├── requirements.txt            # Python dependencies (Flask, PyTorch, Ultralytics, OpenCV, etc.)
├── yolov8n.pt                  # Pre-trained YOLOv8 Nano weights (all 80 COCO classes)
├── instance/                   # Flask-SQLAlchemy instance directory
│   └── database.db             # Active SQLite database file
├── models/
│   └── models.py               # SQLAlchemy ORM models (User, NavigationHistory, Settings)
├── vision/
│   ├── yolo_detector.py        # YOLOv8 inference wrapper with 80-class mapping
│   └── direction_analyzer.py   # Granular angle, sector & clock-face orientation engine
├── depth/
│   └── midas_estimator.py      # MiDaS monocular depth model & metric distance fusion
├── tts/
│   ├── priority_engine.py      # Obstacle urgency prioritization & trilingual translations
│   └── audio_guide.py          # Offline PyTTSx3 TTS fallback engine
├── auth/
│   └── auth_routes.py          # User authentication Blueprint (Login, Register, Logout)
├── routes/
│   ├── main_routes.py          # Core navigation web routes (Dashboard, Live HUD)
│   └── api_routes.py           # Real-time computer vision & depth inference API endpoints
├── static/
│   ├── css/
│   │   └── style.css           # Premium accessibility UI styling & high-contrast themes
│   └── js/
│       ├── voice_assistant.js  # Multilingual TTS & continuous Speech Recognition engine
│       ├── webcam.js           # Real-time video frame streaming & canvas HUD renderer
│       └── dashboard.js        # Analytics charts & database metric updates
└── templates/
    ├── base.html               # Accessibility layout with ARIA landmarks & voice bars
    ├── detection.html          # Real-time Navigation HUD with camera & mic controls
    ├── dashboard.html          # Operations dashboard with detection statistics
    ├── login.html              # Operator sign-in portal
    └── register.html           # New operator account registration
```

---

## 3. Core Technical Architecture

### 3.1 Object Detection Pipeline (`vision/yolo_detector.py`)
- Powered by Ultralytics **YOLOv8** (`yolov8n.pt`).
- Detects all **80 COCO classes** with natural everyday aliases:
  - `cell phone` $\rightarrow$ **mobile phone**
  - `couch` $\rightarrow$ **sofa**
  - `dining table` $\rightarrow$ **table**
  - `potted plant` $\rightarrow$ **plant**
- Features a dynamic sensitivity cutoff (`conf=0.20-0.25`) that ensures small, handheld obstacles (phones, cups, remotes) are not filtered out.

### 3.2 Metric Depth Estimation (`depth/midas_estimator.py`)
- Employs Intel ISL **MiDaS Small** (`MiDaS_small`) for real-time monocular relative disparity prediction.
- Fuses relative disparity maps with real-world metric priors (`OBJECT_METRIC_PRIORS`) and optical pinhole camera geometry to calculate accurate metric distances ($0.3\text{m} - 7.5\text{m}$).

### 3.3 Direction & Spatial Angle Engine (`vision/direction_analyzer.py`)
- Measures horizontal displacement relative to the camera optical center ($H_{\text{FOV}} \approx 65^\circ$).
- Outputs:
  1. **Angular Offset**: Real degree values from $-32.5^\circ$ (left) to $+32.5^\circ$ (right).
  2. **Navigational Sector**: *Far Left*, *Left*, *Slight Left*, *Ahead*, *Slight Right*, *Right*, *Far Right*.
  3. **Clock-Face Position**: *9 o'clock*, *10 o'clock*, *11 o'clock*, *12 o'clock*, *1 o'clock*, *2 o'clock*, *3 o'clock*.
  4. **Localized Direction Strings**: Translated into English, Hindi, and Odia.

### 3.4 Multilingual Priority Audio Engine (`tts/priority_engine.py` & `static/js/voice_assistant.js`)
- Prioritizes threats based on spatial proximity, trajectory, and obstacle hazard class (High / Medium / Low).
- Generates speech announcements in three languages:
  - **English**: *"Warning! Mobile phone 0.8 meters ahead at 12 o'clock"*
  - **Hindi (हिन्दी)**: *"चेतावनी! मोबाइल 0.8 मीटर बिल्कुल सामने 12 बजे की दिशा में"*
  - **Odia (ଓଡ଼ିଆ)**: *"ସତର୍କତା! ମୋବାଇଲ୍ 0.8 ମିଟର ସାମ୍ନାରେ 12 ଟା ଦିଗରେ"*
- Incorporates browser speech synthesis with self-echo cancellation to prevent the microphone from picking up the system's own audio output.

---

## 4. Hands-Free Voice Commands & Shortcuts

The system supports continuous voice command recognition using the browser Web Speech API. Users can operate all functions hands-free:

### Spoken Voice Commands

| Function | English Commands | Hindi (हिन्दी) Commands | Odia (ଓଡ଼ିଆ) Commands |
| :--- | :--- | :--- | :--- |
| **Start Camera** | *"Start navigation"*, *"Start camera"* | *"कैमरा शुरू करो"*, *"शुरू करो"* | *"ଆରମ୍ଭ କର"*, *"କ୍ୟାମେରା ଆରମ୍ଭ କର"* |
| **Stop Camera** | *"Stop navigation"*, *"Stop camera"* | *"कैमरा बंद करो"*, *"रोक दो"* | *"ବନ୍ଦ କର"*, *"କ୍ୟାମେରା ବନ୍ଦ କର"* |
| **Switch Camera** | *"Switch camera"*, *"Next camera"* | *"कैमरा बदलो"*, *"दूसरा कैमरा"* | *"କ୍ୟାମେରା ବଦଳାନ୍ତୁ"*, *"ଅନ୍ୟ କ୍ୟାମେରା"* |
| **Switch to Hindi** | *"Hindi"*, *"Change to Hindi"* | *"हिन्दी भाषा"*, *"हिन्दी में बोलो"* | *"ହିନ୍ଦୀ କରନ୍ତୁ"* |
| **Switch to Odia** | *"Odia"*, *"Change to Odia"* | *"उड़िया भाषा"*, *"उड़िया में बोलो"* | *"ଓଡ଼ିଆ"*, *"ଓଡ଼ିଆରେ କୁହ"* |
| **Switch to English** | *"English"*, *"Change to English"* | *"अंग्रेजी भाषा"*, *"इंग्लिश में बोलो"* | *"ଇଂରାଜୀ କରନ୍ତୁ"* |
| **Scene Status** | *"Status"*, *"What do you see?"* | *"क्या दिख रहा है"*, *"स्थिति बताओ"* | *"କଣ ଦେଖାଯାଉଛି"*, *"କଣ ଅଛି"* |
| **Mute / Unmute** | *"Mute voice"*, *"Unmute"* | *"आवाज बंद करो"*, *"चुप रहो"* | *"ଚୁପ୍ ରୁହ"*, *"ଶାନ୍ତ ରୁହ"* |
| **Go to Dashboard** | *"Go to dashboard"*, *"Home page"* | *"डैशबोर्ड खोलो"*, *"होम पेज"* | *"ଡ୍ୟାସବୋର୍ଡ ଖୋଲ"* |

### Accessibility Keyboard Shortcuts

- **`Space`**: Start / Stop live camera stream
- **`V`**: Toggle Voice Command recognition (Microphone ON / OFF)
- **`C`**: Switch to next connected camera device
- **`L`**: Cycle audio guidance language (**English** $\rightarrow$ **हिन्दी** $\rightarrow$ **ଓଡ଼ିଆ**)
- **`M`**: Mute / Unmute audio speech synthesis
- **`S`**: Read aloud live dashboard summary / status
- **`R`**: Repeat the last spoken navigation alert

---

## 5. Database Schema & Inspection

Data is stored persistently in an SQLite database located at `instance/database.db`.

### Tables

1. **`users`**: User authentication accounts
   - `id` (INTEGER, Primary Key)
   - `username` (VARCHAR(80), Unique)
   - `email` (VARCHAR(120), Unique)
   - `password_hash` (VARCHAR(256), Hashed via Werkzeug)
   - `created_at` (DATETIME)

2. **`navigation_history`**: Real-time obstacle detection audit logs
   - `id` (INTEGER, Primary Key)
   - `user_id` (INTEGER, Foreign Key referencing `users.id`)
   - `object_name` (VARCHAR(100), e.g., 'mobile phone', 'sofa', 'person')
   - `confidence` (FLOAT, detection confidence percentage)
   - `distance` (FLOAT, metric distance in meters)
   - `direction` (VARCHAR(20), e.g., 'Left', 'Center', 'Right')
   - `timestamp` (DATETIME)

3. **`settings`**: User-specific accessibility preferences
   - `voice_speed`, `voice_volume`, `alert_distance`, `theme`

### How to View Stored Data

You can inspect all saved records at any time using the built-in database viewer script:

```bash
python view_db.py
```

This displays:
- All registered user accounts
- Total logged detection count
- Latest 15 detections with obstacle name, confidence %, distance (meters), direction, and timestamps
- Top detected obstacles summary

Alternatively, you can open `instance/database.db` directly in [DB Browser for SQLite](https://sqlitebrowser.org/) or via standard SQLite CLI:
```bash
sqlite3 instance/database.db "SELECT * FROM navigation_history ORDER BY id DESC LIMIT 10;"
```

---

## 6. Installation & Setup Guide

### Prerequisites
- **Python 3.8 to 3.12** installed on your system.
- Standard integrated webcam or external USB camera.
- Chromium-based browser (Google Chrome, Microsoft Edge, Brave) for full Web Speech Recognition support.

### Step 1: Clone or Open Directory
```bash
cd "C:\Users\swain\Desktop\Cross modal"
```

### Step 2: Set Up Virtual Environment (Recommended)
```bash
# Create virtual environment
python -m venv venv

# Activate on Windows:
venv\Scripts\activate

# Activate on Linux/macOS:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 7. Running the Application

### Starting the Web Server
Launch the Flask application:
```bash
python app.py
```

When started, the terminal displays:
```text
Starting AI Model initialization pipeline...
Loading YOLOv8 model from yolov8n.pt...
YOLOv8 model loaded successfully with all 80 COCO classes active.
Loading MiDaS model (MiDaS_small)...
 * Running on http://127.0.0.1:5000
```

### Accessing the Web Application
1. Open your browser and navigate to:
   ```text
   http://127.0.0.1:5000
   ```
   *(Important: Accessing via `http://127.0.0.1:5000` or `http://localhost:5000` provides a Secure Context so browsers permit webcam and microphone access without SSL certificates).*

2. Register a new account or log in with existing credentials.
3. Click **"Start Navigation"** to enter the Live Navigation HUD.
4. Allow browser **Camera** and **Microphone** permissions when prompted.
5. Speak *"Start navigation"* or press `Space` to begin receiving spatial audio guidance.

---

## 8. Standalone Researcher Data Collector

For research purposes and collecting training datasets of obstacle distances and spatial angles:
```bash
python collect_data.py
```
- Captures frames directly from your webcam.
- Saves image frames to `dataset/images/`.
- Appends spatial records (Distance, Bounding Box, Angle, Depth Category) to `dataset/records.csv`.
- Press `q` to stop collection safely.

---

## 9. Technology Stack

- **Backend**: Python 3.12, Flask, Flask-SQLAlchemy, Flask-Login, Werkzeug
- **Deep Learning**: PyTorch, TorchVision, Ultralytics YOLOv8 Nano (`yolov8n`), Intel ISL MiDaS Small (`MiDaS_small`), OpenCV (`cv2`)
- **Speech & Audio**: Web Speech API (`SpeechSynthesis`, `SpeechRecognition`), PyTTSx3, Web Audio API (earcons & chimes)
- **Frontend**: HTML5, CSS3 Glassmorphism, JavaScript (ES6+), Canvas API, Lucide Icons
- **Database**: SQLite3 (`instance/database.db`)

---

## 10. Contributors & License

Developed as a Final-Year B.Tech Capstone Project in Computer Science and Engineering.  
Designed to advance assistive computer vision, accessible human-computer interaction, and independent mobility.
