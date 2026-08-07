# PostureSense API Inventory

**Version:** 2.0.0 (Phase 1)  

| HTTP Method | Route Endpoint | Blueprint | Auth Required | Functionality |
|---|---|---|---|---|
| GET | `/` | `main` | No | Renders home landing page |
| GET | `/landing` | `main` | No | Renders feature landing page |
| GET | `/favicon.ico` | `main` | No | Serves brand favicon asset |
| GET | `/sitemap.xml` | `main` | No | Serves primary XML sitemap |
| GET | `/sitemap2.xml` | `main` | No | Serves secondary XML sitemap |
| GET | `/robots.txt` | `main` | No | Serves robots crawling rules |
| GET | `/pose_detection` | `main` | Yes | Renders posture analysis UI |
| GET | `/about` | `main` | No | Redirects to home about section |
| GET | `/yoga-poses` | `main` | No | Renders yoga pose library page |
| GET | `/pricing` | `main` | No | Redirects to pricing section |
| GET/POST | `/register` | `auth` | No | User registration form & action |
| GET/POST | `/login` | `auth` | No | User login form & authentication |
| GET | `/logout` | `auth` | Yes | User session termination |
| GET | `/dashboard` | `dashboard` | Yes | User analytics dashboard |
| GET | `/api/dashboard_stats` | `dashboard` | Yes | Returns user session metrics JSON |
| GET/POST | `/contact` | `contact` | No | Contact form handler & email dispatch |
| POST | `/submit` | `contact` | No | Contact form submission API |
| POST | `/subscribe` | `contact` | No | Newsletter subscription API |
| GET | `/status` | `api` | No | Server-Sent Events (SSE) pose status stream |
| GET | `/get_status` | `api` | No | Returns current pose status JSON |
| GET | `/stop_camera` | `api` | No | Stops active camera feed |
| POST | `/save_pose_session` | `api` | Yes | Persists completed pose session to Supabase |
| GET | `/video_feed` | `api` | No | MJPEG video stream feed |
| GET | `/health` | `api` | No | Health check endpoint (`{"status": "ok"}`) |
| GET | `/version` | `api` | No | Version info (`{"version": "2.0.0"}`) |
