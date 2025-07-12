# 🪞 PostureSense: AI-Powered Smart Mirror for Real-Time Posture & Exercise Feedback

**PostureSense** is a next-generation AI-powered smart mirror system that provides real-time exercise feedback and posture correction. Built using computer vision and deep learning models (MediaPipe, OpenPose), PostureSense enhances workout efficiency, prevents injuries, and promotes healthy body alignment — ideal for fitness enthusiasts, physiotherapists, and smart home integrations.

---

## 🚀 Features

- 🧠 **AI-Powered Posture Detection**  
  Uses MediaPipe to detect key body landmarks and classify yoga or fitness postures like T-Pose, Warrior II, Tree, and Cobra.

- 🎥 **Real-Time Video Feedback**  
  Streams webcam input and visually overlays feedback on live video frames.

- 📢 **Posture Status Updates**  
  Displays current posture classification and transitions on a web interface.

- 📧 **Newsletter Subscription & Contact Form**  
  Fully functional backend to receive contact messages and newsletter emails using SMTP.

- 📊 **Extensible Pose Classification**  
  Easily integrate more poses or training models in the future for advanced fitness applications.

---

## 🛠️ Technologies Used

| Frontend                  | Backend                     | AI/ML & Vision         |
|---------------------------|-----------------------------|------------------------|
| HTML, CSS, Bootstrap      | Python Flask                | MediaPipe Pose         |
| Vanilla JS (AOS, Swiper)  | Flask routes for API & UI   | OpenCV for video feed  |
| Responsive UI Template    | Email via SMTP (Gmail)      | Pose landmark analysis |




---

## ⚙️ Installation

### 1. Clone the Repo

```bash
git clone https://github.com/gtathelegend/Posture-Sense.git
cd Posture-Sense
```

2. Set up Python Environment
```bash
pip install -r requirements.txt
```
3. Create .env File
```bash
EMAIL_USER=youremail@gmail.com
EMAIL_PASSWORD=yourapppassword
ADMIN_EMAIL=receiveremail@gmail.com
```
4. Run the Flask App
```bash
python app.py
```

Then open http://localhost:5000 or http://localhost:PORT in your browser.

🧪 Sample Poses Detected
T-Pose

Warrior II

Tree Pose

Cobra Pose

Extend easily by tweaking angle thresholds in classifyPose().

📂 Folder Structure
bash
Copy
Edit
posturesense/

│

├── static/               # Assets like CSS, JS, images

├── templates/            # HTML templates

├── .env                  # Environment config

├── app.py                # Main Flask backend

├── README.md             # Project documentation

└── requirements.txt      # Python dependencies

🧑‍💻 Developed By

**Vedaang Sharma**





🌐 Live Demo
🔗 Hosted Version : https://posture-sense.onrender.com

📦 GitHub Repository : https://github.com/gtathelegend/Posture-Sense/

📜 License
This project is licensed under the MIT License. Feel free to use, modify, and distribute.

🙌 Support & Feedback
For issues or feature requests, feel free to open an issue.

For collaborations or feedback, reach us at: vedaangsharma2006@gmail.com

