# 🪞 Posture Sense - AI-Powered Smart Mirror for Exercise Correction

[![Deployed on Render](https://img.shields.io/badge/Deployed-Render-46E3B7?style=flat-square)](https://posture-sense.onrender.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg?style=flat-square)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-blue.svg?style=flat-square)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

**Posture Sense** is a revolutionary AI-powered smart mirror application that provides real-time exercise feedback and posture correction using computer vision and machine learning. Get instant feedback on your exercises, improve your form, and prevent injuries with intelligent motion tracking powered by MediaPipe and OpenCV.

**Created by:** [Vedaang Sharma](https://github.com/gtathelegend)

---

## 🌟 Features

### Core Functionality
- **🧠 AI-Powered Posture Detection**  
  Uses MediaPipe to detect 33 body landmarks and classify yoga or fitness postures in real-time.

- **🎥 Real-Time Video Feedback**  
  Streams live webcam input with pose estimation overlay and visual feedback.

- **📊 Pose Classification**  
  Detects and analyzes multiple yoga poses:
  - **Warrior II Pose** (Virabhadrasana II) - Strengthens legs, arms & shoulders
  - **T Pose** - Improves posture and shoulder strength
  - **Tree Pose** (Vrikshasana) - Enhances balance and focus
  - **Cobra Pose** (Bhujangasana) - Strengthens spine and opens chest

- **👤 User Authentication**  
  Secure login/registration with bcrypt password hashing and Flask-Login sessions.

- **📈 Dashboard & Progress Tracking**  
  - View workout history and statistics
  - Monitor pose distribution
  - Track accuracy metrics
  - Save pose sessions for analysis

- **📧 Email Integration**  
  Newsletter subscription and contact form with SMTP Gmail integration.

- **📱 Responsive Design**  
  Works seamlessly on desktop, tablet, and mobile devices.

### Technical Features
- **Real-Time Processing** - Sub-100ms pose detection and feedback
- **Database Storage** - SQLite with SQLAlchemy ORM for user data
- **Server-Sent Events** - Live status updates without polling
- **SEO Optimized** - Sitemap, robots.txt, and meta tags included

---

## 🛠️ Tech Stack

### Backend
- **Framework**: Flask (Python web framework)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Flask-Login with Bcrypt
- **Computer Vision**: MediaPipe Pose, OpenCV (cv2)
- **Email**: SMTP Gmail integration

### Frontend
- **HTML5/CSS3/JavaScript** - Responsive design
- **Bootstrap 5** - UI framework and components
- **Vanilla JS** - AOS (Animate on Scroll), Swiper carousels
- **Real-time Updates** - Server-sent events (SSE)

### Deployment
- **Hosting**: Render.com
- **Web Server**: Gunicorn
- **Environment**: Python 3.8+

---

## 📋 Requirements

- Python 3.8 or higher
- pip (Python package manager)
- Modern web browser with camera access
- Webcam or camera device
- Gmail account (for email features)

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/gtathelegend/Posture-Sense.git
cd Posture-Sense
```

### 2. Create Python Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file:

```env
SECRET_KEY=your_secret_key
EMAIL_USER=your_gmail@gmail.com
EMAIL_PASSWORD=your_app_password
ADMIN_EMAIL=admin@example.com
```

### 5. Run the Application

```bash
python app.py
```

Visit `http://localhost:8080`

---

## 📖 Usage

- **Register/Login** - Create account
- **Live Demo** - Use real-time pose detection
- **Yoga Poses** - Learn supported poses
- **Dashboard** - Track your progress

---

## 📁 Project Structure

```
Posture-Sense/
├── app.py              # Flask application
├── requirements.txt    # Dependencies
├── templates/          # HTML pages
├── static/             # CSS, JS, images
└── instance/           # Database
```

---

## 🌐 Deployment

Deploy on Render with:
- Build: `pip install -r requirements.txt`
- Start: `gunicorn app:app`
- Live: `https://posture-sense.onrender.com`

---

## 📄 License

MIT License - See [LICENSE](LICENSE)

---

## 👨‍💻 Creator

**Vedaang Sharma**
- LinkedIN: [Vedaang Sharma](https://www.linkedin.com/in/vedaangsharma2006/)
- GitHub: [@gtathelegend](https://github.com/gtathelegend)
- Email: vedaangsharma2006@gmail.com

---

**Last Updated**: January 26, 2026 | **Version**: 1.7.1

Made with ❤️ by **Vedaang Sharma**