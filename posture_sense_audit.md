# Posture-Sense — Comprehensive Technical Audit Report

> **Audited:** 2026-08-06  
> **Repository:** `d:\Github\Posture-Sense` · `gtathelegend/Posture-Sense`  
> **Live URL:** https://posture-sense.onrender.com  
> **Auditor:** Antigravity (Senior Software Architect / AI Engineer)

---

## 1. Repository Overview

### Overall Architecture

The project is a **monolithic Flask web application** — no microservices, no separate frontend build pipeline. Everything runs from a single `app.py` file. The backend handles HTML rendering via Jinja2 templates, REST API endpoints, server-sent events (SSE), and OpenCV/MediaPipe video streaming simultaneously.

### Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.11.9 |
| **Web Framework** | Flask 2.x |
| **Auth** | Flask-Login + Flask-Bcrypt |
| **Database** | Supabase (PostgreSQL) via `supabase-py` |
| **Computer Vision** | MediaPipe 0.10.14 + OpenCV (`opencv-contrib-python`) |
| **CORS** | Flask-CORS |
| **Email** | smtplib / SMTP Gmail |
| **Deployment** | Render.com (Gunicorn), Docker available |
| **Templating** | Jinja2 (server-side rendered HTML) |
| **CSS** | Custom design system (vanilla CSS) |
| **JS** | Vanilla JS + React 18 (CDN, Babel transpiled at runtime) |
| **UI Libraries** | Bootstrap 5 (vendor), AOS, Swiper, GLightbox, PureCounter |

### Folder Structure

```
Posture-Sense/
├── app.py                    # ENTIRE application (984 lines)
├── requirements.txt          # 12 Python packages
├── supabase_schema.sql       # DB schema (2 tables)
├── Procfile                  # gunicorn app:app
├── Dockerfile                # Python 3.9 container
├── runtime.txt               # python-3.11.9 (conflicts with Dockerfile)
├── startup.sh                # gunicorn with --timeout 600 --workers 1
├── templates/
│   ├── base.html             # Nav, footer, shared layout
│   ├── index.html            # Main landing page (678 lines)
│   ├── landing.html          # Alternative React landing (33 lines)
│   ├── app.html              # Pose detection UI (260 lines)
│   ├── dashboard.html        # User dashboard (198 lines)
│   ├── login.html            # Auth - Login
│   ├── register.html         # Auth - Register
│   └── yoga-poses.html       # Pose library (static content)
├── static/assets/
│   ├── design-system.css     # CSS design tokens
│   ├── pages.css             # Inner-page styles (1397 lines)
│   ├── landing.css           # Landing-specific styles
│   ├── landing-light.css     # Light-theme landing styles
│   ├── js/main.js            # Bootstrap + vendor JS (185 lines)
│   ├── landing-tweaks.jsx    # React landing component (501 lines)
│   ├── shared.jsx            # Shared React nav/footer (127 lines)
│   ├── tweaks-panel.jsx      # Design customization panel
│   └── vendor/               # Bootstrap, AOS, Swiper, etc.
├── instance/posture_sense.db # Orphaned SQLite file (unused)
├── mediapipe/                # Python virtualenv (NOT a module)
├── mediapipe_old/            # Python virtualenv (NOT a module)
└── static/extras/            # Marketing copywriting .txt files
```

### Major Modules

- **Pose Pipeline** (`app.py` lines 173–576): MediaPipe initialization, `gen_frames()` stream generator, `detectPose()`, `calculateAngle()`, `classifyPose()`
- **Authentication** (`app.py` lines 579–710): `/register`, `/login`, `/logout`, `/dashboard`
- **API Endpoints** (`app.py` lines 712–984): `/video_feed`, `/get_status`, `/stop_camera`, `/save_pose_session`, `/status` (SSE)
- **Email** (`app.py` lines 762–978): `/contact`, `/submit`, `/subscribe`

### Frontend Architecture

- **Primary pages** (`/`, `/login`, `/register`, `/yoga-poses`, `/dashboard`, `/pose_detection`): Server-side Jinja2 HTML templates extending `base.html`
- **Landing alternative** (`/landing`): A fully React 18 SPA rendered via in-browser Babel transpilation from CDN. **No build step.** Raw JSX served and compiled at runtime.
- **No module bundler** (no Webpack, Vite, or Parcel)
- **No TypeScript**
- **State** is managed via Flask sessions (`flask-login`) on the backend and minimal vanilla JS on the frontend

### Backend Architecture

- Single-file Flask app (`app.py`, 984 lines)
- No separation of concerns: models, routes, services, and business logic all in one file
- No Blueprints, no application factory pattern
- Supabase client initialized at module level (fails silently if env vars missing)
- Global mutable state for camera: `camera_active`, `current_status`, `last_status`, `camera` — all module-level globals (not thread-safe)

### Database

- **Supabase (PostgreSQL)** with 2 tables:
  - `users` (id UUID, username, email, password_hash, created_at)
  - `pose_sessions` (id bigint, user_id UUID FK, pose_label, timestamp, duration, accuracy)
- All DB interactions via Supabase Python client (REST-based)
- No ORM (no SQLAlchemy)
- **An orphaned `instance/posture_sense.db` SQLite file exists** — this is never referenced in any code; it is a leftover from a previous Flask-SQLAlchemy prototype

### APIs

| Endpoint | Method | Auth Required | Purpose |
|---|---|---|---|
| `/video_feed` | GET | No | MJPEG stream from server camera |
| `/get_status` | GET | No | JSON: current/last pose status |
| `/stop_camera` | GET | No | Signal camera shutdown |
| `/save_pose_session` | POST | Yes | Save session to Supabase |
| `/api/dashboard_stats` | GET | Yes | JSON dashboard stats |
| `/status` | GET | No | SSE stream of pose_status |
| `/subscribe` | POST | No | Newsletter subscription via email |
| `/contact` | POST | No | Contact form via email |
| `/submit` | POST | No | Duplicate of `/contact` |

### Authentication

- Session-based via `Flask-Login` + server-side sessions
- Passwords hashed with bcrypt (`Flask-Bcrypt`)
- No OAuth, no JWT, no 2FA
- No password reset functionality
- No email verification on registration
- Sessions expire on browser close (default Flask session behavior)

### State Management

- Server-side: Flask session cookie
- Client-side: `localStorage` (only in React landing for `ps_user` — **disconnected from Flask auth**)
- The React-based nav in `shared.jsx` reads `localStorage` for auth state, while the Jinja2 templates use `current_user` from Flask-Login — **these two systems are completely separate and inconsistent**

### Deployment Configuration

- **Render.com**: `Procfile` → `gunicorn app:app` (no worker config, no bind, no timeout)
- **`startup.sh`**: `gunicorn --bind=0.0.0.0 --timeout 600 --workers 1 app:app` (1 worker is correct given camera global state)
- **Dockerfile**: Uses Python 3.9, installs libgl1/libglib2.0-0, but **no `WORKDIR` is set**, code is copied to container root
- **`runtime.txt`**: `python-3.11.9` (conflicts with Dockerfile's `python:3.9`)
- **`.deployment`**: Azure-style SCM build flag — `SCM_DO_BUILD_DURING_DEPLOYMENT=true`
- **`.env` committed to repository** with real credentials (CRITICAL SECURITY ISSUE)

---

## 2. Existing Features

### ✅ Fully Implemented

| Feature | Evidence |
|---|---|
| **Landing page (main)** | `templates/index.html` (678 lines), renders correctly at `/` |
| **User Registration** | `app.py:581-623`, `/register` route, bcrypt hashing, Supabase insert |
| **User Login** | `app.py:625-644`, session-based with Flask-Login |
| **User Logout** | `app.py:646-651` |
| **Dashboard (data)** | `app.py:653-708`, reads real Supabase sessions, computes stats |
| **Pose session saving** | `app.py:922-934`, `/save_pose_session` → Supabase insert |
| **Session history table** | `templates/dashboard.html:76-106`, real data from DB |
| **Yoga poses page** | `templates/yoga-poses.html`, 4 static poses with images/descriptions |
| **MediaPipe landmark detection** | `app.py:390-423`, `detectPose()` with 33 landmarks |
| **Joint angle calculation** | `app.py:425-451`, `calculateAngle()` (atan2 method) |
| **Pose classification (4 poses)** | `app.py:453-576`, `classifyPose()` for Warrior II, T Pose, Tree Pose, Cobra Pose |
| **Server camera streaming** | `app.py:250-329`, `gen_frames()`, MJPEG via `/video_feed` |
| **Pose status API** | `app.py:905-911`, `/get_status` returns JSON |
| **Skeleton overlay** | `app.py:411-412`, `mp_drawing.draw_landmarks()` on each frame |
| **Camera controls (Start/Pause/Close)** | `templates/app.html:119-175`, JS camera control |
| **Dashboard live updates** | `templates/dashboard.html:115-192`, polls `/api/dashboard_stats` every 3 sec |
| **Newsletter subscription** | `app.py:942-978`, email via Gmail SMTP |
| **Responsive design** | CSS design system with wrap container and mobile nav |
| **SEO assets** | `sitemap.xml`, `sitemap2.xml`, `robots.txt`, Google Tag Manager |
| **DB schema** | `supabase_schema.sql` with proper indices |

### 🟡 Partially Implemented

| Feature | Status | Evidence |
|---|---|---|
| **Contact form** | Routes exist (`/contact`, `/submit`), email logic coded, but `contact.html` template is **missing** → 500 error | `app.py:762-843`, no `templates/contact.html` |
| **Accuracy scoring** | Saved to DB and displayed on dashboard, but the score is **fake random** (`85 + Math.random() * 15`) | `app.html:196` |
| **SSE status stream** | `/status` endpoint exists but generates an **infinite loop with no sleep** (CPU-melting busy loop) | `app.py:714-720` |
| **Alternative React landing** | Renders at `/landing`, has animated skeleton canvas, but "Launch live demo" links to `/app.html` (404) | `landing.html`, `landing-tweaks.jsx` |
| **Email integration** | Gmail SMTP configured, works locally if credentials valid; on Render with gunicorn the credentials are loaded from env | `app.py:772-833` |
| **Voice feedback (TTS)** | Code present but entirely commented out (`pyttsx3`) | `app.py:17,198-206` |
| **Camera reliability** | Has reconnect logic but uses `cv2.CAP_DSHOW` (Windows-only) — will silently fail on Linux/Render | `app.py:234` |

### ❌ Missing / Broken

| Feature | Status | Evidence |
|---|---|---|
| **`/about` page** | **500 Server Error** — `render_template('#about')` is not a valid call | `app.py:760` |
| **`/contact` page** | **500 Server Error** — `contact.html` does not exist | `app.py:843` |
| **`/pricing` page** | **500 Server Error** — `join_now()` returns `None` | `app.py:850-851` |
| **Password reset** | Not implemented | No route exists |
| **Email verification** | Not implemented | No route exists |
| **User profile settings** | Not implemented | No route exists |
| **Reports / PDF export** | Not implemented | No route exists |
| **Exercise repetition counting** | Not implemented | No code |
| **Exercise recognition** | Not implemented | No code |
| **Posture correction feedback (specific)** | Only 4 hardcoded string responses | `app.html:229-238` |
| **Progress charts / visualizations** | Not implemented (dashboard is table-only) | No charting library |
| **Webcam calibration** | Not implemented | No code |
| **Offline inference** | Not implemented (requires server) | Architecture doesn't allow it |

---

## 3. Pose Detection Audit

### Libraries Present

| Library | Present | Usage |
|---|---|---|
| **MediaPipe** | ✅ Yes | `mediapipe==0.10.14` in requirements.txt; `import mediapipe as mp` in app.py; `mp.solutions.pose` initialized at line 175 |
| **OpenCV** | ✅ Yes | `opencv-contrib-python` in requirements.txt; used for camera capture, frame flip, resize, encode, color conversion |
| **TensorFlow** | ❌ No | Not in requirements.txt, not imported anywhere |
| **PyTorch** | ❌ No | Not referenced anywhere |
| **BlazePose** | 🟡 Implicit | MediaPipe Pose is built on BlazePose internally, but no direct BlazePose API is used |
| **PoseNet** | ❌ No | Not present |
| **MoveNet** | ❌ No | Not present |
| **ONNX** | ❌ No | Not present |
| **WebAssembly inference** | ❌ No | No client-side inference; all processing on server |

### Webcam Feed

- **Implemented**: ✅ `gen_frames()` opens `cv2.VideoCapture`, reads frames, encodes to JPEG, yields as MJPEG multipart stream
- **Deployment reality**: ❌ **Completely non-functional on Render** — Render's container has no physical camera. `/video_feed` returns an empty byte stream. The `<img id="video_feed">` element will simply show a broken image.
- **On local machine**: ✅ Works if a webcam is available

### Landmark Detection

- **Implemented**: ✅ `detectPose()` at `app.py:390-423` calls `pose.process(imageRGB)` and collects all 33 landmarks into a list of `(x, y, z)` pixel-coordinate tuples
- **33 Keypoints**: ✅ MediaPipe Pose produces 33 landmarks; all are collected via `for landmark in results.pose_landmarks.landmark`
- **Confidence scores**: 🟡 MediaPipe provides per-landmark `visibility` (confidence) scores, but the code does **not extract or use them** — landmarks are added to the list unconditionally
- **Smoothing**: ❌ No temporal smoothing (no EMA, no Kalman filter). `pose = mp_pose.Pose(static_image_mode=False, ...)` enables MediaPipe's internal tracking, which provides some implicit smoothing

### Skeleton Rendering

- **Implemented**: ✅ `mp_drawing.draw_landmarks()` draws the full skeleton overlay (joints + connections) on each frame before encoding

### Pose Classification Logic

- **Method**: Rule-based angle thresholds (NOT ML classification)
- **Angles calculated**: 8 joint angles (left/right: elbow, shoulder, knee, hip-knee-ankle, hip-shoulder)
- **Poses supported**: Warrior II, T Pose, Tree Pose, Cobra Pose — **only 4 total**
- **Confidence scores**: ❌ No per-prediction confidence; it's a hard boolean threshold match
- **Unknown pose handling**: Defaults to "Scanning..." label with red text; the check `if label != 'Unknown Pose'` is logically incorrect — the initial label is `'Scanning ...'`, not `'Unknown Pose'`, so the condition is always true, and `pose_status` gets updated even for the scanning state

---

## 4. AI / ML Audit

### What the project claims
The README and landing page claim: "AI-powered", "machine learning", "computer vision", "MediaPipe · 33 LANDMARKS", "POSTURE CLASSIFICATION", "BIOMETRIC FEEDBACK LOOP", "97.3% accuracy" (hardcoded in footer).

### What is actually implemented

| Claim | Reality |
|---|---|
| **Pose estimation** | ✅ Real — MediaPipe BlazePose runs server-side via Python |
| **Posture classification** | 🟡 Partial — Rule-based angle thresholds, not ML. Hard-coded `if` conditions. 4 poses only. |
| **Exercise recognition** | ❌ Missing — no exercise type detection |
| **Joint angle calculation** | ✅ Real — `calculateAngle()` using atan2 math |
| **Repetition counting** | ❌ Missing — no counter, no state machine for reps |
| **Posture scoring** | ❌ Fake — accuracy is `85 + Math.random() * 15` (random float 85–100%) |
| **AI feedback generation** | ❌ Hardcoded strings — 4 canned messages matching 4 pose names |
| **Model inference** | 🟡 MediaPipe's internal BlazePose model does real inference; the classification layer on top is just `if/elif` rules |
| **"97.3% accuracy"** | ❌ Fabricated — hardcoded string in `shared.jsx:110` footer |
| **"18ms latency"** | ❌ Fabricated — hardcoded string in `shared.jsx:109` footer |

### Verdict

This is a **rule-based heuristic system dressed up with AI marketing language**. The underlying MediaPipe model performs genuine pose estimation, but the "classification" layer is a series of hard-coded angle ranges — not a trained ML classifier. There is no model training, no dataset, no inference pipeline, no probability output. A production AI system would use a trained neural classifier (e.g., SVM, MLP, or fine-tuned CNN) operating on landmark coordinates.

---

## 5. Backend Audit

### Routes Inventory

| Route | Status | Notes |
|---|---|---|
| `GET /` | ✅ Working | Renders `index.html` |
| `GET /landing` | ✅ Working | Renders React landing page |
| `GET /login` | ✅ Working | Login form |
| `POST /login` | ✅ Working | Auth against Supabase |
| `GET /register` | ✅ Working | Register form |
| `POST /register` | ✅ Working | Creates user in Supabase |
| `GET /logout` | ✅ Working | Clears session |
| `GET /dashboard` | ✅ Working | Protected; shows session data |
| `GET /api/dashboard_stats` | ✅ Working | JSON stats |
| `GET /pose_detection` | ✅ Working | Protected; renders camera UI |
| `GET /video_feed` | ✅ Local only / ❌ Deployed | MJPEG stream; no camera on Render |
| `GET /get_status` | ✅ Working | JSON with current/last pose |
| `GET /stop_camera` | ✅ Working | Sets `camera_active = False` |
| `POST /save_pose_session` | ✅ Working | Inserts to Supabase |
| `GET /status` | ⚠️ Broken | Infinite busy-loop SSE — no `time.sleep()` |
| `GET /yoga-poses` | ✅ Working | Static page |
| `GET /about` | ❌ 500 Error | `render_template('#about')` — invalid template name |
| `GET/POST /contact` | ❌ 500 Error | `contact.html` missing |
| `GET/POST /submit` | ❌ 500 Error | `contact.html` missing |
| `GET /pricing` | ❌ 500 Error | Returns `None` |
| `POST /subscribe` | ✅ Conditionally works | Depends on Gmail SMTP env vars |
| `GET /favicon.ico` | ✅ Working | |
| `GET /sitemap.xml` | ✅ Working | |
| `GET /robots.txt` | ✅ Working | |

### Dead / Broken Code

1. **`/about`** (`app.py:758-760`): `render_template('#about')` — `#about` is a CSS anchor, not a template file. Throws `TemplateNotFound` in production.
2. **`/pricing`** (`app.py:849-851`): `join_now()` body is just `pass` — returns `None`, causing Flask to throw `TypeError`.
3. **`/submit`** (`app.py:854-903`): Duplicate of `/contact` with identical code and the same missing `contact.html` dependency.
4. **`/status` SSE** (`app.py:714-720`): Infinite generator with no sleep/delay — it will consume 100% CPU on one core as soon as a client connects.
5. **`cv2.CAP_DSHOW`** (`app.py:234`): Windows DirectShow backend — non-functional on Linux containers.
6. **`posture_sense.db`** (`instance/`): Orphaned SQLite file from a previous prototype. Never referenced in code.
7. **`mediapipe/`** and **`mediapipe_old/`** directories: Both are Python virtual environments (`pyvenv.cfg` inside), not project modules. Misleadingly named. Should not be in the repository.
8. **`static/forms/contact.php`** and **`newsletter.php`**: PHP files in a Python/Flask project. Never executed. Leftover template files.
9. **Commented-out TTS engine** (`app.py:17,198-206`): 8 lines of commented-out `pyttsx3` code.
10. **Old `gen_frames` commented out** (`app.py:348-388`): Large block of dead code for IP camera URL.
11. **`test.py`**: Developer debug script committed to repository.
12. **`poseAccuracyScore = 85 + Math.random() * 15`** (`app.html:196`): Fake accuracy metric.

### TODOs and Placeholder Code

- No formal `# TODO` comments found in the codebase
- Several empty route bodies (`pass` in `/pricing`)
- Duplicate email-sending code blocks (copy-pasted verbatim between `/contact` and `/submit`)
- `static/extras/*.txt` files: Marketing copy placeholder text files (faq, gallery, price, stat, testimonial) — never consumed by the app

---

## 6. Frontend Audit

### Pages Status

| Page | Status | Notes |
|---|---|---|
| **`/` (Home/Index)** | ✅ Fully functional | 678-line marketing page; real CTAs, animations. Works correctly. |
| **`/landing`** | 🟡 Partially functional | React SPA with animated skeleton canvas; works visually but "Launch live demo" links to `/app.html` (404 on Render) |
| **`/login`** | ✅ Fully functional | Form submits, Flash messages work, redirects on success |
| **`/register`** | ✅ Fully functional | Form submits with client + server validation |
| **`/yoga-poses`** | ✅ Fully functional | Static content with 4 pose cards and images |
| **`/pose_detection`** | 🟡 Partially functional | UI is complete; camera streaming works **locally only**; fake accuracy; no landmark confidence display |
| **`/dashboard`** | ✅ Functionally complete | Reads real DB data; pose distribution bars; session table; live polling |
| **`/about`** | ❌ Broken (500) | Template missing |
| **`/contact`** | ❌ Broken (500) | Template missing |
| **`/pricing`** | ❌ Broken (500) | Route returns None |

### Components That Never Receive Real Data

1. **Accuracy badge** on dashboard: Shows values from `accuracy` column in DB — seeded by `Math.random()` on client
2. **"97.3% accuracy"** in footer (`shared.jsx:110`): Hardcoded string
3. **"18ms latency"** in footer (`shared.jsx:109`): Hardcoded string
4. **"6+ Pose Models"** in hero (`index.html:52`): Only 4 poses exist in code
5. **"Sub-100ms pose detection"** in README: No benchmark; claim unverified
6. **Pose feedback messages** in `app.html:229-238`: 4 hardcoded switch-case strings; no dynamic AI-generated feedback

### `main.js` Mismatch

`static/assets/js/main.js` (185 lines) is the generic **BootstrapMade Bootslander template JS**. It references `.mobile-nav-toggle`, `#navmenu`, `#header`, `#preloader`, `.scroll-top`, `.glightbox` — but the actual Jinja2 templates use different class names from the custom design system (`ps-nav`, `ps-navmenu`, `mobileToggle`). This file is effectively dead code on inner pages; it may only activate on `templates/index.html` which does include the old Bootstrap vendor structure.

---

## 7. Deployment Audit

### Configuration Issues

| Issue | Severity | Detail |
|---|---|---|
| **`.env` committed to repo** | 🔴 Critical | Contains Gmail App Password, Supabase Secret Key, and Flask Secret Key in plaintext |
| **Werkzeug Debugger exposed in production** | 🔴 Critical | `app.run(debug=True)` — but gunicorn ignores this. However, `/about`, `/contact`, `/pricing` still return Werkzeug debug pages on live Render deployment (the interactive debugger is enabled) |
| **Webcam unavailable on Render** | 🔴 Critical | `/video_feed` streams empty bytes; pose detection is 100% non-functional in deployed environment |
| **`cv2.CAP_DSHOW` on Linux** | 🔴 Critical | Windows-only capture backend; will fail silently on Render Linux container |
| **`runtime.txt` vs Dockerfile version conflict** | 🟡 Medium | `runtime.txt` specifies Python 3.11.9; Dockerfile uses `python:3.9` |
| **No `WORKDIR` in Dockerfile** | 🟡 Medium | Files copied to container root `/`; considered bad practice |
| **Gunicorn with no workers config in Procfile** | 🟡 Medium | `web: gunicorn app:app` — defaults to 1 worker (correct for camera global state, but no timeout) |
| **`/status` SSE busy loop** | 🟡 Medium | Will spike CPU on Render if any client connects |
| **React landing uses in-browser Babel** | 🟡 Medium | `babel.min.js` is loaded from CDN at runtime; not suitable for production; slows page load |
| **Supabase keys in .env** | 🔴 Critical | Secret key should be in Render environment variables, not a committed file |

### What Works on Deployment (Render)

- ✅ Homepage (`/`)
- ✅ Login / Register pages render and form submission likely works (if Supabase env vars are set)
- ✅ `/yoga-poses`
- ✅ `/get_status` returns JSON
- ✅ Dashboard (if logged in via Supabase)
- ✅ `/favicon.ico`, `/sitemap.xml`, `/robots.txt`

### What Does NOT Work on Deployment

- ❌ `/video_feed` — empty; no camera on server
- ❌ `/pose_detection` — camera UI renders but no feed
- ❌ `/about` — 500 TemplateNotFound
- ❌ `/contact` — 500 TemplateNotFound
- ❌ `/pricing` — 500 TypeError
- ❌ `/landing` "Launch live demo" button — navigates to `/app.html` (404)
- ❌ `/status` SSE — busy loop; CPU risk

---

## 8. Runtime Issues

### Broken Imports / Runtime Errors

1. **`render_template('#about')`** (`app.py:760`): Crashes at runtime with `TemplateNotFound`
2. **`join_now()` returns `None`** (`app.py:849-851`): Flask raises `TypeError` on every request to `/pricing`
3. **`contact.html` missing** (`app.py:843,903`): Both `/contact` and `/submit` crash

### Dead / Unused Files

| File | Issue |
|---|---|
| `static/assets/js/main.js` | Bootslander template JS; mostly unused on inner pages |
| `static/forms/contact.php` | PHP in a Python project; never executed |
| `static/forms/newsletter.php` | Same |
| `static/forms/Readme.txt` | Template placeholder readme |
| `static/extras/faq.txt`, etc. | Marketing copy placeholder files |
| `instance/posture_sense.db` | Orphaned SQLite; never referenced |
| `mediapipe/` directory | Python venv named misleadingly |
| `mediapipe_old/` directory | Another Python venv |
| `test.py` | Developer debug script; should not be in production repo |
| `static/assets/tweaks-panel.jsx` | Design customization dev panel (18KB); included in production |
| `index.html` (root) | 25KB file in root; separate from `templates/index.html`; Flask never serves it |
| `.claude`, `.codex`, `.vscode` | IDE config directories committed |

### Duplicate Code

- `/contact` and `/submit` routes contain **verbatim identical email-sending code** (70+ lines duplicated)
- Jinja2 nav/footer in `base.html` is duplicated by `shared.jsx` React nav/footer — two completely separate implementations of the same UI

### Console Errors (Observed on Deployed Site)

- Babel in-browser transpiler warning on `/landing`
- Any click of "Launch live demo" on `/landing` → navigation to `/app.html` → 404
- `main.js` may fail to find `.mobile-nav-toggle` on pages that don't include it

---

## 9. Missing Core Features

Compared to a production-quality AI posture analysis application:

| Missing Feature | Importance |
|---|---|
| **Real-time pose estimation in browser** | 🔴 Critical — Current server streaming doesn't work on deployment. Browser-based MediaPipe (JS) or TensorFlow.js MoveNet would make deployment viable. |
| **Landmark visualization overlay on client** | 🔴 Critical — The skeleton overlay is burned into the MJPEG; no interactive keypoint display |
| **Repetition counter** | 🔴 High — Core fitness feature; requires state machine tracking joint angles over time |
| **Exercise recognition** | 🔴 High — Currently only yoga poses; no exercise type detection (squat, push-up, etc.) |
| **Real posture scoring** | 🔴 High — Accuracy is random; a real score would compare joint angles against reference ranges |
| **Specific posture correction feedback** | 🔴 High — "Great job!" is not feedback; real feedback identifies the specific deviation (e.g., "Lower your right arm 10°") |
| **User profile / settings** | 🟡 Medium — No profile editing, no height/weight, no goals |
| **Progress analytics / charts** | 🟡 Medium — Dashboard shows raw table data; no trend lines, charts, or weekly progress views |
| **PDF / session reports** | 🟡 Medium — Export functionality entirely absent |
| **Password reset** | 🟡 Medium — Basic security requirement |
| **Email verification** | 🟡 Medium — Accounts can be created with arbitrary emails |
| **Webcam calibration** | 🟡 Medium — No distance/angle calibration; detection quality varies by setup |
| **Multiple exercise templates** | 🟡 Medium — 4 yoga poses only; no strength, cardio, or mobility exercises |
| **Offline / local inference** | 🟡 Medium — Server dependency means no offline use; browser WASM inference would solve this |
| **Performance optimization** | 🟡 Medium — No frame skipping, no model quantization, no WebWorker for inference |
| **Accessibility** | 🟡 Medium — No ARIA labels on interactive elements, no keyboard navigation tested |
| **Mobile camera support** | 🟡 Medium — Architecture requires server camera; mobile browser camera not usable |
| **Session timer / goal setting** | 🟡 Medium — No in-session timer or target duration |
| **Notification system** | 🟡 Medium — No push notifications, no in-app alerts for goals met |

---

## 10. Production Readiness Scores

| Area | Score | Rationale |
|---|---|---|
| **Architecture** | 3/10 | Single-file monolith, global mutable state, no separation of concerns, two conflicting frontend frameworks |
| **Frontend** | 4/10 | Visually polished UI; but 3 broken routes, fake data, two disconnected auth systems, no charting |
| **Backend** | 3/10 | Working auth + DB; 3 broken routes with 500s, SSE busy loop, duplicate code, no input sanitization |
| **Code Quality** | 3/10 | No tests, no type hints beyond Optional, duplicate code, dead files, committed secrets, no linting |
| **AI Implementation** | 2/10 | MediaPipe landmark detection is real; classification is rule-based; accuracy is fabricated; no deployed inference |
| **UX** | 5/10 | Design is attractive and modern; but core feature (camera) doesn't work on deployment; 3 broken pages |
| **Deployment** | 2/10 | Deployed but core feature is non-functional; 3 routes return 500; secrets committed; Werkzeug debug exposed |
| **Documentation** | 5/10 | README is well-structured and accurate for local setup; no API docs, no contribution guide |
| **Testing** | 0/10 | No unit tests, no integration tests, no CI/CD pipeline; only `test.py` (email debug script) |
| **Maintainability** | 2/10 | Everything in one 984-line file; no modules, no interfaces, no comments on business logic |
| **Overall Readiness** | **3/10** | A functional local prototype with a polished UI skin; not production-ready in any meaningful sense |

---

## 11. Prioritized Roadmap

### Phase 1 — Critical Fixes (Week 1–2)
*Without these, the deployed app is broken and insecure.*

| Task | Complexity | Dependencies |
|---|---|---|
| Remove `.env` from Git, rotate all secrets | Low | None |
| Fix `/about` — create proper template or redirect | Low | None |
| Fix `/pricing` — return a valid response | Low | None |
| Create `templates/contact.html` or redirect `/contact` → landing | Low | None |
| Fix `/status` SSE — add `time.sleep(0.5)` to prevent busy loop | Low | None |
| Disable Werkzeug debug (`debug=False` or rely on Gunicorn) | Low | None |
| Remove `cv2.CAP_DSHOW` (use default backend for Linux compat) | Low | None |
| Fix `/landing` "Launch live demo" button → `/pose_detection` | Low | None |

### Phase 2 — Core AI (Week 3–6)
*Switch to browser-based inference to make the core feature deployable.*

| Task | Complexity | Dependencies |
|---|---|---|
| Integrate MediaPipe JS (or TensorFlow.js MoveNet) for browser-side inference | High | JS/WASM knowledge |
| Render skeleton overlay on canvas in browser | Medium | MediaPipe JS |
| Extract per-landmark visibility/confidence scores | Low | MediaPipe JS |
| Implement real posture scoring vs reference angles | Medium | MediaPipe JS, angle library |
| Implement repetition counter (state machine on joint angle time series) | Medium | Browser inference |
| Add temporal smoothing (EMA over landmark positions) | Low | Browser inference |
| Expand pose library to 10+ poses with proper angle ranges | Medium | Domain knowledge |
| Replace random accuracy with real per-frame deviation score | Medium | Angle calculation |

### Phase 3 — Analytics & Features (Week 7–10)

| Task | Complexity | Dependencies |
|---|---|---|
| Add Chart.js or Recharts for dashboard visualizations | Low | Phase 1 fixes |
| Implement weekly/monthly progress views | Medium | Chart.js |
| Add specific posture correction feedback (per joint, per pose) | Medium | Phase 2 |
| Implement password reset via email | Medium | Email integration |
| Add email verification on registration | Medium | Email integration |
| User profile page (goals, stats, settings) | Medium | Auth system |
| Session timer with goal alerts | Low | Phase 2 |

### Phase 4 — Polish (Week 11–14)

| Task | Complexity | Dependencies |
|---|---|---|
| PDF report generation (ReportLab or WeasyPrint) | Medium | Phase 3 |
| Unify auth system (remove `localStorage` dual system) | Medium | React refactor |
| Refactor `app.py` into Flask Blueprints | Medium | All phases |
| Add unit tests (pytest) and CI/CD (GitHub Actions) | High | Phase 1 |
| Add ARIA labels and keyboard navigation | Low | Phase 1 |
| Webcam calibration flow | Medium | Phase 2 |
| Offline inference with model caching | High | Phase 2, WASM |
| Pre-compile React JSX (Vite or webpack) | Medium | Phase 2 |

---

## 12. Final Summary

### Current Completion Percentage

**~25% complete** as a production AI posture analysis application.
**~60% complete** as a local proof-of-concept demo.

### Features That Genuinely Work

- User registration and login (via Supabase, bcrypt-hashed passwords)
- Session history storage and retrieval from Supabase
- Dashboard showing real session data (total sessions, duration, pose distribution)
- MediaPipe landmark detection + skeleton overlay (locally, with camera)
- Pose classification for 4 yoga poses via angle thresholds (locally)
- Joint angle calculation (`calculateAngle()` function is correct math)
- Attractive, responsive UI design
- SEO assets (sitemap, robots.txt, meta tags)
- Newsletter/contact email SMTP integration (locally, with valid credentials)

### Features That Appear Implemented But Are Actually Mock/Placeholder

- **"Accuracy score"**: Random float between 85–100% generated in browser — not a real measurement
- **"97.3% accuracy" in footer**: Hardcoded marketing string
- **"18ms latency" in footer**: Hardcoded marketing string
- **"6+ Pose Models"**: Only 4 poses exist
- **"AI-powered feedback"**: 4 hardcoded strings like "Great job! You're in the Warrior II pose."
- **"Real-time posture correction"**: No correction guidance; only pose name displayed
- **"BIOMETRIC FEEDBACK LOOP"** (marquee): Marketing text with no technical backing

### Features That Are Completely Missing

- **Browser-based inference** (entire core feature fails on deployment)
- Password reset
- Email verification
- Repetition counting
- Exercise recognition (anything beyond 4 yoga poses)
- Progress charts/visualizations
- PDF/session reports
- User profile settings
- Posture correction feedback (specific, actionable)
- Any form of model training or ML classification
- Tests of any kind

### Biggest Technical Risks

1. **Core feature non-functional in production**: The entire value proposition (webcam pose detection) is inoperable on Render. A visitor cannot experience the product without cloning and running locally.
2. **Committed secrets**: `.env` contains Gmail App Password, Supabase Secret Key, and Flask Secret Key — all potentially compromised.
3. **3 broken routes returning 500**: `/about`, `/contact`, `/pricing` expose Werkzeug debugger in production — a security vulnerability.
4. **Global mutable camera state**: Not thread-safe; concurrent requests to `/video_feed` will corrupt `camera_active` and `camera` globals.
5. **SSE busy loop**: `/status` will spike CPU to 100% for every connected client.

### Biggest Strengths

1. **Genuinely uses MediaPipe**: The landmark detection pipeline is real, correctly implemented, and locally functional.
2. **Clean UI design**: The design system is modern, cohesive, and visually impressive — better than most student projects.
3. **Supabase integration works**: Auth + session storage is correctly implemented with proper bcrypt hashing.
4. **Database schema is correct**: The 2-table Supabase schema with proper foreign keys and indices is well-designed.
5. **Solid deployment configuration awareness**: Procfile, Dockerfile, runtime.txt, startup.sh all exist — shows deployment intent.
