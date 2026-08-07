# PostureSense Route Mapping

**Version:** 2.0.0 (Phase 1)  

| Route | View Function | Blueprint Handler | Response Type | Template / Output |
|---|---|---|---|---|
| `/` | `index` | `main.index` | HTML | `templates/index.html` |
| `/landing` | `landing` | `main.landing` | HTML | `templates/landing.html` |
| `/favicon.ico` | `favicon` | `main.favicon` | Image | `favicon.ico` |
| `/sitemap.xml` | `sitemap` | `main.sitemap` | XML | `sitemap.xml` |
| `/sitemap2.xml` | `sitemap2` | `main.sitemap2` | XML | `sitemap2.xml` |
| `/robots.txt` | `robots` | `main.robots` | Plaintext | `robots.txt` |
| `/pose_detection` | `pose_detection` | `main.pose_detection` | HTML | `templates/app.html` |
| `/about` | `about` | `main.about` | Redirect | `/#about` |
| `/yoga-poses` | `yoga_poses` | `main.yoga_poses` | HTML | `templates/yoga-poses.html` |
| `/pricing` | `join_now` | `main.join_now` | Redirect | `/#pricing` |
| `/register` | `register` | `auth.register` | HTML / Redirect | `templates/register.html` |
| `/login` | `login` | `auth.login` | HTML / Redirect | `templates/login.html` |
| `/logout` | `logout` | `auth.logout` | Redirect | `url_for('main.index')` |
| `/dashboard` | `dashboard` | `dashboard.dashboard` | HTML | `templates/dashboard.html` |
| `/api/dashboard_stats` | `dashboard_stats` | `dashboard.dashboard_stats` | JSON | `{ total_sessions, total_duration, ... }` |
| `/contact` | `contact` | `contact.contact` | HTML / JSON | `/#contact` / `{ status: success }` |
| `/submit` | `submit` | `contact.submit` | JSON | `{ status: success }` |
| `/subscribe` | `subscribe` | `contact.subscribe` | JSON | `{ status: success }` |
| `/status` | `pose_status_updates` | `api.pose_status_updates` | Event Stream | SSE `data: <status>` |
| `/get_status` | `get_status` | `api.get_status` | JSON | `{ current_status, last_status }` |
| `/stop_camera` | `stop_camera` | `api.stop_camera` | JSON | `{ status: success }` |
| `/save_pose_session` | `save_pose_session` | `api.save_pose_session` | JSON | `{ status: success }` |
| `/video_feed` | `video_feed` | `api.video_feed` | MJPEG Stream | `multipart/x-mixed-replace` |
| `/health` | `health` | `api.health` | JSON | `{ status: ok }` |
| `/version` | `version` | `api.version` | JSON | `{ version: 2.0.0 }` |
