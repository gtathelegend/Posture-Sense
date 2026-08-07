# PostureSense v2 — Migration Plan

**Author:** Lead Architect  
**Date:** 2026-08-06  
**Status:** Awaiting Approval  
**Scope:** Upgrade existing production codebase to v2 engine architecture

---

## Executive Summary

PostureSense v1 is a **monolithic Flask application** where all logic lives in a single 984-line [app.py](file:///d:/Github/Posture-Sense/app.py). Computer vision runs **server-side** (Python MediaPipe + OpenCV), video is streamed as MJPEG over HTTP, and only 4 yoga poses are recognized via hardcoded if-statements.

PostureSense v2 (per [PRD.md](file:///d:/Github/Posture-Sense/docs/prd.md) and [ENGINE_ARCHITECTURE.md](file:///d:/Github/Posture-Sense/docs/ENGINE_ARCHITECTURE.md)) requires:

- **Browser-side** MediaPipe Tasks (privacy-first — no webcam frames leave the device)
- **Event-driven engine architecture** (12 independent engines communicating via an Event Bus)
- **Next.js + React** frontend with modular components
- **Configuration-driven** pose/exercise definitions (no hardcoded angles)
- **4 operational modes** (Exercise, Yoga, Ergonomic, Rehabilitation)
- **Plugin system** for exercises and poses

This plan migrates from v1 → v2 **without rewriting from scratch**, preserving all reusable logic, data, and infrastructure.

---

## 1. Current vs. Target Architecture

### What Exists Today

| Concern | Current Implementation |
|---|---|
| **Backend** | Single `app.py` (Flask) — auth, routes, CV pipeline, email, everything |
| **Frontend** | Jinja2 templates + raw JSX via CDN Babel (no build step) |
| **CV Pipeline** | Server-side Python MediaPipe + OpenCV → MJPEG stream |
| **Pose Detection** | `detectPose()` — MediaPipe landmark extraction (server) |
| **Pose Classification** | `classifyPose()` — 4 poses via hardcoded angle thresholds |
| **Angle Math** | `calculateAngle()` — atan2-based 3-point angle calculation |
| **Database** | Supabase PostgreSQL — 2 tables (`users`, `pose_sessions`) |
| **Auth** | Flask-Login + Flask-Bcrypt + Supabase user table |
| **Dashboard** | Server-rendered Jinja2 with stats cards + Chart.js |
| **Deployment** | Render.com (Gunicorn), Docker, Azure CI (orphaned) |

### What v2 Requires

| Concern | Target Implementation |
|---|---|
| **Backend** | Modular Flask/FastAPI — auth, sessions, analytics APIs only |
| **Frontend** | Next.js + React with component library |
| **CV Pipeline** | Browser-side MediaPipe Tasks → Event Bus → Engine chain |
| **12 Engines** | Camera, MediaPipe, Landmark, Biomechanics, Pose Rule, Movement, Scoring, Feedback, Analytics, Persistence, Notification, Report |
| **Database** | Extended Supabase schema (sessions with joint metrics, goals, etc.) |
| **Configuration** | YAML/JSON files for poses, exercises, thresholds, weights |
| **Plugin System** | Per-exercise plugin directories with config + feedback rules |

---

## 2. Reuse Analysis

### 2.1 — Which files should remain unchanged

| File | Reason |
|---|---|
| [LICENSE](file:///d:/Github/Posture-Sense/LICENSE) | Legal document, no change needed |
| [favicon.ico](file:///d:/Github/Posture-Sense/favicon.ico) | Brand asset |
| [robots.txt](file:///d:/Github/Posture-Sense/robots.txt) | SEO config, update URLs later |
| [static/assets/img/*](file:///d:/Github/Posture-Sense/static/assets/img) | All image assets (hero, details, gallery, team, yoga-poses) |
| [static/assets/img/vgu.png](file:///d:/Github/Posture-Sense/static/assets/img/vgu.png) | Logo asset |

### 2.2 — Which files should be refactored

| File | What to Extract |
|---|---|
| [app.py](file:///d:/Github/Posture-Sense/app.py) | Must be split into 6+ modules (see §2.4) |
| [supabase_schema.sql](file:///d:/Github/Posture-Sense/supabase_schema.sql) | Extend with session metrics, goals, settings tables |
| [templates/base.html](file:///d:/Github/Posture-Sense/templates/base.html) | Design system / nav / footer → React components |
| [templates/dashboard.html](file:///d:/Github/Posture-Sense/templates/dashboard.html) | Stats cards + chart logic → React Dashboard component |
| [templates/login.html](file:///d:/Github/Posture-Sense/templates/login.html) | Form structure → React auth component |
| [templates/register.html](file:///d:/Github/Posture-Sense/templates/register.html) | Form structure → React auth component |
| [static/assets/design-system.css](file:///d:/Github/Posture-Sense/static/assets/design-system.css) | Migrate tokens to CSS custom properties in new design system |
| [static/assets/pages.css](file:///d:/Github/Posture-Sense/static/assets/pages.css) | Extract reusable component styles |
| [.gitignore](file:///d:/Github/Posture-Sense/.gitignore) | Add `node_modules/`, `.next/`, `out/` |
| [requirements.txt](file:///d:/Github/Posture-Sense/requirements.txt) | Remove `mediapipe`, `opencv-contrib-python`, `numpy`, `protobuf` (CV moves to browser) |

### 2.3 — Which files should be deleted

| File | Reason |
|---|---|
| `mediapipe/` | Python virtualenv committed by accident — NOT a code module |
| `mediapipe_old/` | Second orphaned virtualenv |
| `venv/` | Third orphaned virtualenv |
| `.venv/` | Fourth orphaned virtualenv |
| `install/` | Fifth orphaned virtualenv |
| `instance/posture_sense.db` | Orphaned SQLite database — app uses Supabase |
| [test.py](file:///d:/Github/Posture-Sense/test.py) | One-off email test script, not a test suite |
| [index.html](file:///d:/Github/Posture-Sense/index.html) (root) | Standalone static landing page — superseded by `templates/index.html` and then by React landing |
| [static/forms/contact.php](file:///d:/Github/Posture-Sense/static/forms/contact.php) | PHP file — app is Python/Flask, this is dead code |
| [static/forms/newsletter.php](file:///d:/Github/Posture-Sense/static/forms/newsletter.php) | PHP file — dead code |
| [static/forms/Readme.txt](file:///d:/Github/Posture-Sense/static/forms/Readme.txt) | Belongs to PHP forms — dead |
| [static/extras/.DS_Store](file:///d:/Github/Posture-Sense/static/extras/.DS_Store) | macOS metadata file |
| [static/assets/.DS_Store](file:///d:/Github/Posture-Sense/static/assets/.DS_Store) | macOS metadata file |
| [.codex](file:///d:/Github/Posture-Sense/.codex) | Empty file, no purpose |
| [sitemap2.xml](file:///d:/Github/Posture-Sense/sitemap2.xml) | Duplicate sitemap — consolidate into one |
| [posture_sense_audit.md](file:///d:/Github/Posture-Sense/posture_sense_audit.md) | Historical audit doc — move to `docs/` if preserving |

### 2.4 — Which files should be split

#### [app.py](file:///d:/Github/Posture-Sense/app.py) → 6 modules

| Lines | Concern | Target Module |
|---|---|---|
| 1–50 | App factory, Supabase client, config | `backend/app/__init__.py` + `backend/app/core/config.py` |
| 52–168 | User model, PoseSession model, DB helpers | `backend/app/models/` + `backend/app/repositories/` |
| 173–576 | `detectPose()`, `calculateAngle()`, `classifyPose()`, `gen_frames()`, camera globals | **DELETE from backend** — CV logic moves to browser engines. `calculateAngle()` algorithm preserved as reference in `frontend/src/engines/biomechanics/` |
| 579–710 | Auth routes (`/register`, `/login`, `/logout`, `/dashboard`, `/api/dashboard_stats`) | `backend/app/api/auth.py` + `backend/app/api/dashboard.py` |
| 712–940 | Status SSE, `/video_feed`, `/get_status`, `/stop_camera`, `/save_pose_session` | `/video_feed` and `/stop_camera` **DELETE** (no server camera). `/save_pose_session` → `backend/app/api/sessions.py`. SSE → frontend WebSocket or polling |
| 942–984 | Email routes (`/contact`, `/submit`, `/subscribe`), app entrypoint | `backend/app/api/contact.py` + `backend/app/main.py` |

### 2.5 — Which files should become engines

These are **new frontend modules** that extract and evolve logic from the current codebase:

| Engine | Source from v1 | What it becomes |
|---|---|---|
| **Camera Engine** | `gen_frames()`, `open_camera()`, `find_working_camera()` in [app.py:209-329](file:///d:/Github/Posture-Sense/app.py#L209-L329) | `frontend/src/engines/camera/` — browser `getUserMedia()` wrapper |
| **MediaPipe Engine** | `detectPose()` in [app.py:390-423](file:///d:/Github/Posture-Sense/app.py#L390-L423) | `frontend/src/engines/mediapipe/` — MediaPipe Tasks Vision (browser WASM) |
| **Landmark Engine** | Implicit in `detectPose()` output processing | `frontend/src/engines/landmark/` — validation, smoothing, One Euro Filter |
| **Biomechanics Engine** | `calculateAngle()` in [app.py:425-451](file:///d:/Github/Posture-Sense/app.py#L425-L451) | `frontend/src/engines/biomechanics/` — joint angles, symmetry, balance, ROM |
| **Pose Rule Engine** | `classifyPose()` in [app.py:453-576](file:///d:/Github/Posture-Sense/app.py#L453-L576) | `frontend/src/engines/pose-rules/` — config-driven YAML rules, no hardcoded if-statements |
| **Movement Engine** | Does not exist in v1 | `frontend/src/engines/movement/` — state machine for rep counting |
| **Scoring Engine** | Does not exist (v1 has no scoring) | `frontend/src/engines/scoring/` — weighted component scores |
| **Feedback Engine** | Does not exist (v1 only shows pose label) | `frontend/src/engines/feedback/` — explainable corrections |
| **Analytics Engine** | Dashboard stats in [app.py:653-708](file:///d:/Github/Posture-Sense/app.py#L653-L708) | `frontend/src/engines/analytics/` + `backend/app/api/analytics.py` |
| **Persistence Engine** | Supabase helpers in [app.py:115-168](file:///d:/Github/Posture-Sense/app.py#L115-L168) | `backend/app/services/persistence.py` |
| **Notification Engine** | Does not exist in v1 | `frontend/src/engines/notification/` |
| **Report Engine** | Does not exist in v1 | `backend/app/services/reports.py` |

### 2.6 — Which frontend components can be reused

| Existing Asset | Reuse Strategy |
|---|---|
| **Nav bar** ([base.html:38-68](file:///d:/Github/Posture-Sense/templates/base.html#L38-L68)) | Extract markup + styling → React `<NavBar>` component. Class names and design tokens transfer directly. |
| **Aurora background** ([base.html:29-35](file:///d:/Github/Posture-Sense/templates/base.html#L29-L35)) | Copy CSS animation → `styles/aurora.css` |
| **Stats cards** ([dashboard.html:35-50](file:///d:/Github/Posture-Sense/templates/dashboard.html#L35-L50)) | Extract → React `<StatCard>` component |
| **Camera card** ([app.html:24-37](file:///d:/Github/Posture-Sense/templates/app.html#L24-L37)) | Refactor for browser MediaPipe → `<CameraCard>` |
| **Status panel** ([app.html:40-49](file:///d:/Github/Posture-Sense/templates/app.html#L40-L49)) | Extract → `<StatusPanel>` with engine event bindings |
| **Login form** ([login.html](file:///d:/Github/Posture-Sense/templates/login.html)) | Form structure + validation → React `<LoginForm>` |
| **Register form** ([register.html](file:///d:/Github/Posture-Sense/templates/register.html)) | Form structure + validation → React `<RegisterForm>` |
| **Yoga pose cards** ([yoga-poses.html](file:///d:/Github/Posture-Sense/templates/yoga-poses.html)) | Card layout → React `<PoseCard>` component |
| **Design system tokens** ([design-system.css](file:///d:/Github/Posture-Sense/static/assets/design-system.css)) | CSS custom properties transfer to new design system |
| **Image assets** ([static/assets/img/](file:///d:/Github/Posture-Sense/static/assets/img)) | All images carry forward unchanged |
| **Google Fonts** (Space Grotesk, JetBrains Mono) | Keep font selection |

### 2.7 — Which backend endpoints can be reused

| Endpoint | Verdict | Justification |
|---|---|---|
| `POST /register` | **REFACTOR** | Auth logic is sound; extract to blueprint, add input sanitization |
| `POST /login` | **REFACTOR** | Same — extract, add rate limiting |
| `GET /logout` | **KEEP** | Minimal, works correctly |
| `GET /dashboard` | **REFACTOR** | Stats calculation logic reused; serve JSON to React instead of Jinja2 |
| `GET /api/dashboard_stats` | **KEEP** | Already returns JSON — perfect for React frontend |
| `POST /save_pose_session` | **REFACTOR** | Extend payload for v2 session schema (joint metrics, scores, etc.) |
| `GET /status` (SSE) | **DELETE** | Server-side pose status SSE is obsolete — CV runs in browser |
| `GET /video_feed` | **DELETE** | MJPEG stream obsolete — camera is browser-only |
| `GET /get_status` | **DELETE** | Server-side status polling obsolete |
| `GET /stop_camera` | **DELETE** | Server camera control obsolete |
| `POST /contact` | **REFACTOR** | Extract to separate blueprint; remove duplicate code |
| `POST /submit` | **DELETE** | Duplicate of `/contact` |
| `POST /subscribe` | **REFACTOR** | Extract to separate blueprint |
| `GET /` (index) | **REPLACE** | Next.js will serve the landing page |
| `GET /landing` | **REPLACE** | Next.js will serve this |
| `GET /pose_detection` | **REPLACE** | Next.js will serve the analysis page |
| `GET /yoga-poses` | **REPLACE** | Next.js will serve this |
| `GET /pricing` | **DELETE** | Empty stub (`pass`), no implementation |

### 2.8 — Which database schema can remain

| Table | Verdict | Notes |
|---|---|---|
| `public.users` | **KEEP** | Schema is correct: `id uuid`, `username`, `email`, `password_hash`, `created_at`. No changes needed. |
| `public.pose_sessions` | **REFACTOR** | Current schema stores only `pose_label`, `duration`, `accuracy`. v2 needs: `exercise_type`, `mode`, `avg_score`, `best_score`, `worst_score`, `rep_count`, `joint_metrics JSONB`, `mistakes JSONB`, `corrections JSONB`, `confidence`. Add these as new columns with defaults. |
| `public.user_settings` | **NEW** | User preferences: theme, notification settings, goals |
| `public.goals` | **NEW** | Weekly/monthly targets |
| `public.session_snapshots` | **NEW** | Per-frame analytics samples (optional, for detailed replay) |

> [!IMPORTANT]
> The existing `users` table and `pose_sessions` table with their indexes are preserved. Migration adds columns — it does NOT drop or recreate tables.

### 2.9 — Which deployment configuration should remain

| File | Verdict | Notes |
|---|---|---|
| [Procfile](file:///d:/Github/Posture-Sense/Procfile) | **REFACTOR** | Update to `web: gunicorn backend.app.main:app` |
| [Dockerfile](file:///d:/Github/Posture-Sense/Dockerfile) | **REFACTOR** | Remove OpenCV/MediaPipe system deps; update Python to 3.11; add WORKDIR |
| [runtime.txt](file:///d:/Github/Posture-Sense/runtime.txt) | **KEEP** | Already `python-3.11.9` |
| [startup.sh](file:///d:/Github/Posture-Sense/startup.sh) | **REFACTOR** | Update module path |
| [.deployment](file:///d:/Github/Posture-Sense/.deployment) | **KEEP** | Azure SCM build flag is harmless |
| [.devcontainer/devcontainer.json](file:///d:/Github/Posture-Sense/.devcontainer/devcontainer.json) | **REFACTOR** | Remove Streamlit references; add Node.js; fix ports |
| [.github/workflows/main_vedaangsharma2006.yml](file:///d:/Github/Posture-Sense/.github/workflows/main_vedaangsharma2006.yml) | **REFACTOR** | Update for new folder structure; add frontend build step |

### 2.10 — Which documentation can remain

| File | Verdict | Notes |
|---|---|---|
| [docs/PRD.md](file:///d:/Github/Posture-Sense/docs/prd.md) | **KEEP** | Authoritative product spec for v2 |
| [docs/ENGINE_ARCHITECTURE.md](file:///d:/Github/Posture-Sense/docs/ENGINE_ARCHITECTURE.md) | **KEEP** | Authoritative engine design for v2 |
| [README.md](file:///d:/Github/Posture-Sense/README.md) | **REFACTOR** | Update to reflect v2 architecture, new setup instructions |
| [sitemap.xml](file:///d:/Github/Posture-Sense/sitemap.xml) | **REFACTOR** | Update URLs for new routing |

---

## 3. Complete File Classification

### Root Directory

| File | Classification | Justification |
|---|---|---|
| [app.py](file:///d:/Github/Posture-Sense/app.py) | **SPLIT** → 6 modules | 984-line monolith violates every principle in ENGINE_ARCHITECTURE. Auth, models, repos, API routes extracted to `backend/`. CV code extracted as algorithm reference for browser engines. |
| [requirements.txt](file:///d:/Github/Posture-Sense/requirements.txt) | **REFACTOR** | Remove CV deps (mediapipe, opencv, numpy, protobuf). Add FastAPI or keep Flask-only. Move to `backend/requirements.txt`. |
| [supabase_schema.sql](file:///d:/Github/Posture-Sense/supabase_schema.sql) | **REFACTOR** | Extend `pose_sessions` with v2 columns. Add new tables. Move to `database/schema.sql`. |
| [index.html](file:///d:/Github/Posture-Sense/index.html) (root) | **DELETE** | Orphaned standalone landing page. Superseded by `templates/index.html`, which itself will become a React page. |
| [test.py](file:///d:/Github/Posture-Sense/test.py) | **DELETE** | Ad-hoc email test script — not a test suite. Replace with proper `tests/` directory. |
| [posture_sense_audit.md](file:///d:/Github/Posture-Sense/posture_sense_audit.md) | **MOVE** | Historical audit. Move to `docs/archive/v1_audit.md`. |
| [favicon.ico](file:///d:/Github/Posture-Sense/favicon.ico) | **MOVE** | Move to `frontend/public/favicon.ico`. |
| [robots.txt](file:///d:/Github/Posture-Sense/robots.txt) | **MOVE** | Move to `frontend/public/robots.txt`. Update URLs. |
| [sitemap.xml](file:///d:/Github/Posture-Sense/sitemap.xml) | **MOVE** | Move to `frontend/public/sitemap.xml`. Update URLs. |
| [sitemap2.xml](file:///d:/Github/Posture-Sense/sitemap2.xml) | **DELETE** | Duplicate sitemap. |
| [LICENSE](file:///d:/Github/Posture-Sense/LICENSE) | **KEEP** | No change. |
| [README.md](file:///d:/Github/Posture-Sense/README.md) | **REFACTOR** | Rewrite for v2 architecture. |
| [.codex](file:///d:/Github/Posture-Sense/.codex) | **DELETE** | Empty file. |
| [.env](file:///d:/Github/Posture-Sense/.env) | **REFACTOR** | Remove email creds from repo. Create `.env.example` template. **Rotate all exposed secrets immediately.** |
| [.gitignore](file:///d:/Github/Posture-Sense/.gitignore) | **REFACTOR** | Add `node_modules/`, `.next/`, `out/`, `__pycache__/`, `*.pyc`, `.env`. |
| [.gitattributes](file:///d:/Github/Posture-Sense/.gitattributes) | **KEEP** | Standard git config. |

### Deployment Files

| File | Classification | Justification |
|---|---|---|
| [Dockerfile](file:///d:/Github/Posture-Sense/Dockerfile) | **REFACTOR** | Remove `libgl1`, `libglib2.0-0` (OpenCV deps). Add `WORKDIR`. Update CMD path. |
| [Procfile](file:///d:/Github/Posture-Sense/Procfile) | **REFACTOR** | Update module path to `backend.app.main:app`. |
| [runtime.txt](file:///d:/Github/Posture-Sense/runtime.txt) | **KEEP** | Already correct (`python-3.11.9`). |
| [startup.sh](file:///d:/Github/Posture-Sense/startup.sh) | **REFACTOR** | Update `gunicorn` target path. |
| [.deployment](file:///d:/Github/Posture-Sense/.deployment) | **KEEP** | Harmless Azure setting. |

### Templates

| File | Classification | Justification |
|---|---|---|
| [templates/base.html](file:///d:/Github/Posture-Sense/templates/base.html) | **REPLACE** | Nav, footer, aurora BG, design tokens → React layout components. CSS tokens preserved. |
| [templates/index.html](file:///d:/Github/Posture-Sense/templates/index.html) | **REPLACE** | Landing page → Next.js page. Content and section structure reused. |
| [templates/landing.html](file:///d:/Github/Posture-Sense/templates/landing.html) | **DELETE** | Thin wrapper for CDN React — superseded by proper Next.js. |
| [templates/app.html](file:///d:/Github/Posture-Sense/templates/app.html) | **REPLACE** | Pose detection UI → React `<AnalysisPage>`. Camera card + status panel markup reused. |
| [templates/dashboard.html](file:///d:/Github/Posture-Sense/templates/dashboard.html) | **REPLACE** | Dashboard → React `<DashboardPage>`. Stats card structure + Chart.js logic reused. |
| [templates/login.html](file:///d:/Github/Posture-Sense/templates/login.html) | **REPLACE** | Login → React `<LoginPage>`. Form fields and validation rules reused. |
| [templates/register.html](file:///d:/Github/Posture-Sense/templates/register.html) | **REPLACE** | Register → React `<RegisterPage>`. Form fields and validation rules reused. |
| [templates/yoga-poses.html](file:///d:/Github/Posture-Sense/templates/yoga-poses.html) | **REPLACE** | Yoga library → React `<PoseLibraryPage>`. Card content reused. |

### Static Assets

| File | Classification | Justification |
|---|---|---|
| [static/assets/design-system.css](file:///d:/Github/Posture-Sense/static/assets/design-system.css) | **REFACTOR** | CSS custom properties → `frontend/src/styles/design-system.css` |
| [static/assets/pages.css](file:///d:/Github/Posture-Sense/static/assets/pages.css) | **REFACTOR** | Extract component styles → per-component CSS modules |
| [static/assets/landing.css](file:///d:/Github/Posture-Sense/static/assets/landing.css) | **MOVE** | → `frontend/src/styles/landing.css` |
| [static/assets/landing-light.css](file:///d:/Github/Posture-Sense/static/assets/landing-light.css) | **MOVE** | → `frontend/src/styles/landing-light.css` |
| [static/assets/landing-tweaks.jsx](file:///d:/Github/Posture-Sense/static/assets/landing-tweaks.jsx) | **REPLACE** | CDN Babel JSX → proper Next.js React component |
| [static/assets/shared.jsx](file:///d:/Github/Posture-Sense/static/assets/shared.jsx) | **REPLACE** | CDN Babel JSX → proper React components |
| [static/assets/tweaks-panel.jsx](file:///d:/Github/Posture-Sense/static/assets/tweaks-panel.jsx) | **REPLACE** | Design tool JSX → dev-only React component |
| [static/assets/css/main.css](file:///d:/Github/Posture-Sense/static/assets/css/main.css) | **MOVE** | Landing page CSS → `frontend/src/styles/` |
| [static/assets/js/main.js](file:///d:/Github/Posture-Sense/static/assets/js/main.js) | **REPLACE** | Vendor init scripts → Next.js component imports |
| [static/assets/img/*](file:///d:/Github/Posture-Sense/static/assets/img) | **MOVE** | All images → `frontend/public/img/` |
| [static/assets/scss/Readme.txt](file:///d:/Github/Posture-Sense/static/assets/scss/Readme.txt) | **DELETE** | Empty SCSS readme — no SCSS files exist |
| [static/assets/vendor/*](file:///d:/Github/Posture-Sense/static/assets/vendor) | **REPLACE** | Bootstrap, AOS, Swiper, etc. → npm packages in `frontend/package.json` |
| [static/forms/*](file:///d:/Github/Posture-Sense/static/forms) | **DELETE** | PHP files — dead code in a Python project |
| [static/extras/*.txt](file:///d:/Github/Posture-Sense/static/extras) | **MOVE** | Marketing copy → `docs/content/` for reference |
| [static/extras/Screenshots/](file:///d:/Github/Posture-Sense/static/extras/Screenshots) | **MOVE** | Screenshots → `docs/screenshots/` |

### Directories to Delete Entirely

| Directory | Reason |
|---|---|
| `mediapipe/` | Committed virtualenv (contains `Include/`, `Lib/`, `Scripts/`, `pyvenv.cfg`) |
| `mediapipe_old/` | Second committed virtualenv |
| `venv/` | Third committed virtualenv |
| `.venv/` | Fourth committed virtualenv |
| `install/` | Fifth committed virtualenv |
| `instance/` | Contains orphaned `posture_sense.db` (SQLite) — app uses Supabase |

### Config/Tooling

| File | Classification | Justification |
|---|---|---|
| [.devcontainer/devcontainer.json](file:///d:/Github/Posture-Sense/.devcontainer/devcontainer.json) | **REFACTOR** | Remove Streamlit reference; add Node.js feature; change port from 8501 to 3000+8080 |
| [.github/workflows/main_vedaangsharma2006.yml](file:///d:/Github/Posture-Sense/.github/workflows/main_vedaangsharma2006.yml) | **REFACTOR** | Update for monorepo structure; add frontend build; fix Python version to 3.11 |
| [.vscode/settings.json](file:///d:/Github/Posture-Sense/.vscode/settings.json) | **REFACTOR** | Add frontend workspace settings |
| [.claude/settings.local.json](file:///d:/Github/Posture-Sense/.claude/settings.local.json) | **KEEP** | Tool config |

### Documentation

| File | Classification | Justification |
|---|---|---|
| [docs/PRD.md](file:///d:/Github/Posture-Sense/docs/prd.md) | **KEEP** | v2 spec — authoritative |
| [docs/ENGINE_ARCHITECTURE.md](file:///d:/Github/Posture-Sense/docs/ENGINE_ARCHITECTURE.md) | **KEEP** | v2 engine design — authoritative |

---

## 4. Migration Phases

### Phase 1 — Cleanup & Foundation (Week 1)

**Goal:** Remove dead weight, establish project structure, secure credentials.

> [!CAUTION]
> The `.env` file is committed with real Supabase keys and Gmail app passwords. **Rotate all secrets before any other work.**

| # | Task | Files Affected |
|---|---|---|
| 1.1 | **Rotate all exposed credentials** (Supabase keys, Gmail app password, SECRET_KEY) | `.env`, Supabase dashboard, Gmail |
| 1.2 | **Delete orphaned virtualenvs** (`mediapipe/`, `mediapipe_old/`, `venv/`, `.venv/`, `install/`) | 5 directories (~100MB+) |
| 1.3 | **Delete orphaned files** (`instance/posture_sense.db`, root `index.html`, `test.py`, `.codex`, `sitemap2.xml`, `static/forms/*`, `.DS_Store` files, `static/assets/scss/Readme.txt`) | ~15 files |
| 1.4 | **Create `.env.example`** with placeholder values | New file |
| 1.5 | **Update `.gitignore`** — add `node_modules/`, `.next/`, `out/`, `__pycache__/`, `*.pyc`, `.env`, `.env.*`, `!.env.example`, virtualenv patterns | `.gitignore` |
| 1.6 | **Create target directory skeleton** (see §5 Target Folder Structure) | New directories |
| 1.7 | **Move `posture_sense_audit.md`** → `docs/archive/v1_audit.md` | Move |
| 1.8 | **Move `static/extras/`** content → `docs/content/` and `docs/screenshots/` | Move |

**Deliverable:** Clean repository with zero dead files, all secrets rotated, directory skeleton created.

---

### Phase 2 — Backend Modularization (Week 2-3)

**Goal:** Split the monolithic `app.py` into a proper modular Flask application without changing any business logic.

| # | Task | Source | Target |
|---|---|---|---|
| 2.1 | **Extract config** — Supabase client factory, env loading, app factory | `app.py:1-50` | `backend/app/__init__.py`, `backend/app/core/config.py` |
| 2.2 | **Extract models** — `User`, `PoseSession` classes | `app.py:65-112` | `backend/app/models/user.py`, `backend/app/models/session.py` |
| 2.3 | **Extract repositories** — `fetch_user_by_*`, `create_user`, `fetch_pose_sessions`, `create_pose_session` | `app.py:115-168` | `backend/app/repositories/user_repo.py`, `backend/app/repositories/session_repo.py` |
| 2.4 | **Extract auth routes** — `/register`, `/login`, `/logout` | `app.py:581-651` | `backend/app/api/auth.py` (Flask Blueprint) |
| 2.5 | **Extract dashboard routes** — `/dashboard`, `/api/dashboard_stats` | `app.py:653-708` | `backend/app/api/dashboard.py` (Flask Blueprint) |
| 2.6 | **Extract session routes** — `/save_pose_session` | `app.py:922-934` | `backend/app/api/sessions.py` (Flask Blueprint) |
| 2.7 | **Extract contact routes** — `/contact`, `/subscribe` (deduplicate `/submit`) | `app.py:762-978` | `backend/app/api/contact.py` (Flask Blueprint) |
| 2.8 | **Delete server-side CV code** — `gen_frames()`, `detectPose()`, `classifyPose()`, `calculateAngle()`, camera globals, `/video_feed`, `/get_status`, `/stop_camera`, `/status` SSE | `app.py:173-576, 712-940` | **Archive** `calculateAngle()` in `docs/reference/v1_angle_algorithm.py` for porting to JS |
| 2.9 | **Create entrypoint** | — | `backend/app/main.py` |
| 2.10 | **Update `requirements.txt`** — remove `mediapipe`, `opencv-contrib-python`, `numpy<2`, `protobuf<5` | `requirements.txt` | `backend/requirements.txt` |
| 2.11 | **Extend database schema** — add v2 columns to `pose_sessions`, create `user_settings`, `goals` tables | `supabase_schema.sql` | `database/migrations/001_v2_schema.sql` |

**Deliverable:** Backend runs identically to v1 but from a modular structure. All existing auth, dashboard, and session endpoints work unchanged. No CV code remains on the server.

---

### Phase 3 — Frontend Foundation (Week 3-5)

**Goal:** Initialize Next.js project, establish design system, port existing UI components to React.

| # | Task | Source | Target |
|---|---|---|---|
| 3.1 | **Initialize Next.js** — `npx create-next-app frontend/` with TypeScript | — | `frontend/` |
| 3.2 | **Port design system** — CSS custom properties, color tokens, typography | `static/assets/design-system.css`, `static/assets/landing-light.css` | `frontend/src/styles/design-system.css`, `frontend/src/styles/globals.css` |
| 3.3 | **Port layout components** — nav bar, footer, aurora background | `templates/base.html` | `frontend/src/components/layout/NavBar.tsx`, `Footer.tsx`, `Aurora.tsx` |
| 3.4 | **Port auth pages** — login, register forms | `templates/login.html`, `templates/register.html` | `frontend/src/app/login/page.tsx`, `frontend/src/app/register/page.tsx` |
| 3.5 | **Port dashboard** — stats cards, chart, session table | `templates/dashboard.html` | `frontend/src/app/dashboard/page.tsx`, `frontend/src/components/dashboard/` |
| 3.6 | **Port pose library** — yoga pose cards | `templates/yoga-poses.html` | `frontend/src/app/poses/page.tsx` |
| 3.7 | **Port landing page** — hero, features, about, contact sections | `templates/index.html` | `frontend/src/app/page.tsx` |
| 3.8 | **Move static assets** — images, favicon, robots.txt, sitemap | `static/assets/img/*`, `favicon.ico`, `robots.txt`, `sitemap.xml` | `frontend/public/` |
| 3.9 | **Install npm packages** — replace vendor directory with npm deps (Bootstrap Icons, AOS, Swiper, Chart.js) | `static/assets/vendor/*` | `frontend/package.json` |
| 3.10 | **Connect to backend** — API client, auth hooks, session hooks | — | `frontend/src/lib/api.ts`, `frontend/src/hooks/useAuth.ts` |

**Deliverable:** Fully functional Next.js frontend that replicates all existing pages. Backend serves API only. No more Jinja2 templates.

---

### Phase 4 — Engine Architecture (Week 5-8)

**Goal:** Implement the 12-engine event-driven architecture in the browser, per ENGINE_ARCHITECTURE.md.

| # | Task | Engine | Key Deliverables |
|---|---|---|---|
| 4.1 | **Event Bus** | Core | `frontend/src/engines/core/event-bus.ts` — pub/sub system with typed events |
| 4.2 | **Camera Engine** | Camera | `frontend/src/engines/camera/` — `getUserMedia()`, device selection, frame scheduling |
| 4.3 | **MediaPipe Engine** | MediaPipe | `frontend/src/engines/mediapipe/` — MediaPipe Tasks Vision (WASM), 33 landmarks, confidence |
| 4.4 | **Landmark Engine** | Landmark | `frontend/src/engines/landmark/` — validation, One Euro Filter, interpolation, normalization |
| 4.5 | **Biomechanics Engine** | Biomechanics | `frontend/src/engines/biomechanics/` — port `calculateAngle()` to TS, add symmetry, balance, ROM, center of mass |
| 4.6 | **Pose Rule Engine** | Pose Rules | `frontend/src/engines/pose-rules/` — YAML/JSON config loader, rule matcher, score calculator |
| 4.7 | **Movement Engine** | Movement | `frontend/src/engines/movement/` — state machine, rep counter, phase detection |
| 4.8 | **Scoring Engine** | Scoring | `frontend/src/engines/scoring/` — weighted component scores (40% alignment, 20% balance, 15% symmetry, 15% ROM, 10% confidence) |
| 4.9 | **Feedback Engine** | Feedback | `frontend/src/engines/feedback/` — rule evaluation, priority ranking, correction messages |
| 4.10 | **Analytics Engine** | Analytics | `frontend/src/engines/analytics/` — session aggregation, trend detection |
| 4.11 | **Persistence Engine** | Persistence | `backend/app/services/persistence.py` + `frontend/src/engines/persistence/` — Supabase abstraction |
| 4.12 | **Configuration System** | Config | `shared/config/poses/`, `shared/config/exercises/`, `shared/config/feedback/` — YAML definitions |
| 4.13 | **Analysis Page** | UI | `frontend/src/app/analysis/page.tsx` — wire all engines together with live canvas overlay |
| 4.14 | **4 Modes** | UI | Mode selector + per-mode config: Exercise, Yoga, Ergonomic, Rehabilitation |

**Deliverable:** Full browser-side AI pipeline with event-driven engines. Camera video never leaves the browser. Real-time skeleton overlay, angle calculations, pose recognition, scoring, and feedback — all in-browser.

---

### Phase 5 — Polish, Testing & Deployment (Week 8-10)

**Goal:** Production readiness — testing, performance, deployment, documentation.

| # | Task | Deliverable |
|---|---|---|
| 5.1 | **Unit tests** — each engine tested independently with mock data | `frontend/src/engines/*/tests/`, `backend/tests/` |
| 5.2 | **Integration tests** — event flow, engine communication | `frontend/src/engines/__tests__/` |
| 5.3 | **E2E tests** — login → camera → detection → feedback → save → dashboard | Playwright / Cypress test suite |
| 5.4 | **Performance benchmarks** — FPS ≥30, inference ≤50ms, CPU <40% | `docs/benchmarks.md` |
| 5.5 | **Notification Engine** | `frontend/src/engines/notification/` — posture reminders, achievements |
| 5.6 | **Report Engine** | `backend/app/services/reports.py` — PDF/CSV export |
| 5.7 | **Update Dockerfile** — multi-stage build (Node for frontend, Python for backend) | `Dockerfile` |
| 5.8 | **Update CI/CD** — build frontend, deploy backend, update Render config | `.github/workflows/` |
| 5.9 | **Update devcontainer** — Node.js + Python, correct ports | `.devcontainer/devcontainer.json` |
| 5.10 | **Update README** — v2 architecture, setup guide, screenshots | `README.md` |
| 5.11 | **Delete old templates** — all `templates/*.html` files after React port verified | `templates/` directory |
| 5.12 | **Delete old static** — all `static/` after assets moved to `frontend/public/` | `static/` directory |
| 5.13 | **Plugin system** — exercise plugin directories with `config.yaml`, `feedback.yaml` | `shared/plugins/exercise/`, `shared/plugins/yoga/` |

**Deliverable:** Production-ready PostureSense v2 with full test coverage, optimized performance, clean deployment pipeline, and comprehensive documentation.

---

## 5. Target Folder Structure

```
Posture-Sense/
├── frontend/                          # Next.js + React application
│   ├── public/
│   │   ├── img/                       # ← moved from static/assets/img/
│   │   ├── favicon.ico                # ← moved from root
│   │   ├── robots.txt                 # ← moved from root
│   │   └── sitemap.xml                # ← moved from root
│   ├── src/
│   │   ├── app/                       # Next.js App Router pages
│   │   │   ├── page.tsx               # Landing (← from templates/index.html)
│   │   │   ├── login/page.tsx         # ← from templates/login.html
│   │   │   ├── register/page.tsx      # ← from templates/register.html
│   │   │   ├── dashboard/page.tsx     # ← from templates/dashboard.html
│   │   │   ├── analysis/page.tsx      # ← from templates/app.html (v2 engine UI)
│   │   │   ├── poses/page.tsx         # ← from templates/yoga-poses.html
│   │   │   └── layout.tsx             # ← from templates/base.html
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── NavBar.tsx         # ← from base.html nav
│   │   │   │   ├── Footer.tsx         # ← from base.html footer
│   │   │   │   └── Aurora.tsx         # ← from base.html aurora BG
│   │   │   ├── dashboard/
│   │   │   │   ├── StatCard.tsx       # ← from dashboard.html stat cards
│   │   │   │   ├── SessionTable.tsx   # ← from dashboard.html session list
│   │   │   │   └── PoseChart.tsx      # ← from dashboard.html Chart.js
│   │   │   ├── analysis/
│   │   │   │   ├── CameraCard.tsx     # ← from app.html camera card
│   │   │   │   ├── StatusPanel.tsx    # ← from app.html status panel
│   │   │   │   ├── SkeletonOverlay.tsx # NEW — canvas skeleton renderer
│   │   │   │   ├── FeedbackPanel.tsx  # NEW — real-time corrections
│   │   │   │   ├── ScoreDisplay.tsx   # NEW — live scoring UI
│   │   │   │   └── ModeSelector.tsx   # NEW — Exercise/Yoga/Ergo/Rehab
│   │   │   ├── auth/
│   │   │   │   ├── LoginForm.tsx      # ← from login.html
│   │   │   │   └── RegisterForm.tsx   # ← from register.html
│   │   │   └── poses/
│   │   │       └── PoseCard.tsx       # ← from yoga-poses.html
│   │   ├── engines/                   # Browser-side AI engines
│   │   │   ├── core/
│   │   │   │   ├── event-bus.ts       # Central pub/sub
│   │   │   │   ├── types.ts           # Shared data contracts
│   │   │   │   └── engine-base.ts     # Abstract engine interface
│   │   │   ├── camera/
│   │   │   │   ├── camera-engine.ts
│   │   │   │   └── camera-engine.test.ts
│   │   │   ├── mediapipe/
│   │   │   │   ├── mediapipe-engine.ts
│   │   │   │   └── mediapipe-engine.test.ts
│   │   │   ├── landmark/
│   │   │   │   ├── landmark-engine.ts
│   │   │   │   ├── one-euro-filter.ts
│   │   │   │   └── landmark-engine.test.ts
│   │   │   ├── biomechanics/
│   │   │   │   ├── biomechanics-engine.ts  # ← calculateAngle() ported to TS
│   │   │   │   ├── angle-calculator.ts
│   │   │   │   ├── symmetry-calculator.ts
│   │   │   │   ├── balance-calculator.ts
│   │   │   │   └── biomechanics-engine.test.ts
│   │   │   ├── pose-rules/
│   │   │   │   ├── pose-rule-engine.ts
│   │   │   │   ├── rule-matcher.ts
│   │   │   │   └── pose-rule-engine.test.ts
│   │   │   ├── movement/
│   │   │   │   ├── movement-engine.ts
│   │   │   │   ├── state-machine.ts
│   │   │   │   ├── rep-counter.ts
│   │   │   │   └── movement-engine.test.ts
│   │   │   ├── scoring/
│   │   │   │   ├── scoring-engine.ts
│   │   │   │   └── scoring-engine.test.ts
│   │   │   ├── feedback/
│   │   │   │   ├── feedback-engine.ts
│   │   │   │   └── feedback-engine.test.ts
│   │   │   ├── analytics/
│   │   │   │   ├── analytics-engine.ts
│   │   │   │   └── analytics-engine.test.ts
│   │   │   ├── persistence/
│   │   │   │   └── persistence-engine.ts
│   │   │   └── notification/
│   │   │       └── notification-engine.ts
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   ├── useEngine.ts
│   │   │   └── useSession.ts
│   │   ├── lib/
│   │   │   ├── api.ts                 # Backend API client
│   │   │   └── supabase.ts            # Direct Supabase client (optional)
│   │   ├── styles/
│   │   │   ├── design-system.css      # ← from static/assets/design-system.css
│   │   │   ├── globals.css            # ← from landing-light.css + pages.css
│   │   │   └── aurora.css             # ← from base.html aurora styles
│   │   ├── types/
│   │   │   └── index.ts               # Global TypeScript types
│   │   └── workers/
│   │       └── mediapipe-worker.ts    # Web Worker for CV offloading
│   ├── package.json
│   ├── tsconfig.json
│   └── next.config.js
│
├── backend/                           # Flask/FastAPI API server
│   ├── app/
│   │   ├── __init__.py                # App factory
│   │   ├── main.py                    # Entrypoint
│   │   ├── core/
│   │   │   ├── config.py              # ← from app.py env loading
│   │   │   └── security.py            # ← from app.py bcrypt setup
│   │   ├── api/
│   │   │   ├── auth.py                # ← from app.py auth routes
│   │   │   ├── dashboard.py           # ← from app.py dashboard routes
│   │   │   ├── sessions.py            # ← from app.py save_pose_session
│   │   │   ├── analytics.py           # NEW — v2 analytics API
│   │   │   └── contact.py             # ← from app.py contact/subscribe
│   │   ├── models/
│   │   │   ├── user.py                # ← from app.py User class
│   │   │   └── session.py             # ← from app.py PoseSession class
│   │   ├── repositories/
│   │   │   ├── user_repo.py           # ← from app.py fetch_user_by_*
│   │   │   └── session_repo.py        # ← from app.py fetch/create pose_sessions
│   │   ├── services/
│   │   │   ├── persistence.py         # Supabase abstraction layer
│   │   │   ├── email.py               # ← from app.py SMTP logic (deduplicated)
│   │   │   └── reports.py             # NEW — PDF/CSV export
│   │   ├── middleware/
│   │   │   └── rate_limit.py          # NEW — rate limiting
│   │   └── schemas/
│   │       └── session_schema.py      # NEW — request/response validation
│   ├── tests/
│   │   ├── test_auth.py
│   │   ├── test_sessions.py
│   │   └── test_dashboard.py
│   └── requirements.txt               # ← from root requirements.txt (CV deps removed)
│
├── database/
│   ├── schema.sql                     # ← from supabase_schema.sql (extended)
│   └── migrations/
│       └── 001_v2_schema.sql          # V2 column additions + new tables
│
├── shared/
│   ├── config/
│   │   ├── poses/
│   │   │   ├── warrior_ii.yaml
│   │   │   ├── tree.yaml
│   │   │   ├── cobra.yaml
│   │   │   ├── t_pose.yaml
│   │   │   ├── mountain.yaml          # NEW for v2
│   │   │   ├── chair.yaml
│   │   │   ├── triangle.yaml
│   │   │   ├── downward_dog.yaml
│   │   │   ├── bridge.yaml
│   │   │   └── child.yaml
│   │   ├── exercises/
│   │   │   ├── squat.yaml
│   │   │   ├── pushup.yaml
│   │   │   ├── lunge.yaml
│   │   │   ├── plank.yaml
│   │   │   └── jumping_jack.yaml
│   │   ├── feedback/
│   │   │   ├── alignment.yaml
│   │   │   ├── balance.yaml
│   │   │   ├── stability.yaml
│   │   │   └── ergonomics.yaml
│   │   ├── thresholds/
│   │   │   └── default.yaml
│   │   └── weights/
│   │       └── scoring.yaml
│   └── plugins/                       # Plugin system (future)
│       ├── exercise/
│       └── yoga/
│
├── docs/
│   ├── PRD.md                         # ← KEEP (authoritative)
│   ├── ENGINE_ARCHITECTURE.md         # ← KEEP (authoritative)
│   ├── archive/
│   │   └── v1_audit.md                # ← moved from posture_sense_audit.md
│   ├── content/                       # ← moved from static/extras/*.txt
│   ├── screenshots/                   # ← moved from static/extras/Screenshots/
│   └── reference/
│       └── v1_angle_algorithm.py      # calculateAngle() preserved for porting
│
├── .devcontainer/devcontainer.json    # ← REFACTORED
├── .github/workflows/deploy.yml       # ← REFACTORED from main_vedaangsharma2006.yml
├── .gitignore                         # ← REFACTORED
├── .env.example                       # NEW — template with placeholder values
├── Dockerfile                         # ← REFACTORED (multi-stage)
├── Procfile                           # ← REFACTORED
├── startup.sh                         # ← REFACTORED
├── runtime.txt                        # ← KEEP
├── LICENSE                            # ← KEEP
└── README.md                          # ← REFACTORED for v2
```

---

## 6. Risk Assessment

> [!WARNING]
> ### Critical: Credential Exposure
> The [.env](file:///d:/Github/Posture-Sense/.env) file is committed to the repository with real Supabase keys (`sb_secret_...`), Gmail app passwords, and the Flask secret key. **All credentials must be rotated in Phase 1 before any other work begins.**

> [!WARNING]
> ### High: Server-to-Browser CV Migration
> The biggest architectural change is moving computer vision from Python (server) to JavaScript/TypeScript (browser). The `calculateAngle()` algorithm is mathematically portable, but the entire `classifyPose()` function with its hardcoded if-statements must be replaced with the configuration-driven Pose Rule Engine. This is the highest-effort task.

> [!IMPORTANT]
> ### Medium: Flask → API-Only Transition
> The backend currently serves HTML pages. During migration (Phases 2-3), both Flask templates and the new React frontend must coexist. The backend should serve API endpoints at `/api/*` while Next.js serves pages. Full template deletion happens only in Phase 5 after the React port is verified.

> [!NOTE]
> ### Low: Database Migration
> Adding columns to `pose_sessions` with `DEFAULT` values is non-breaking. The existing `users` table requires zero changes. Old sessions will simply have `NULL` for new columns.

---

## 7. Success Criteria

| Metric | Current (v1) | Target (v2) |
|---|---|---|
| Pose inference location | Server (Python) | Browser (WASM) |
| Recognized poses | 4 (hardcoded) | 10+ (config-driven) |
| Supported exercises | 0 | 5+ (config-driven) |
| Operational modes | 1 (Yoga only) | 4 (Exercise, Yoga, Ergo, Rehab) |
| Feedback quality | Pose label only | Explainable corrections with angle data |
| Scoring | None | Weighted 0-100 with component breakdown |
| Architecture | Monolithic (1 file) | 12 engines + Event Bus |
| Frontend | Jinja2 + CDN Babel | Next.js + TypeScript |
| FPS | ~15 (server-limited) | ≥30 (browser-native) |
| Privacy | Video streams to server | Video never leaves browser |
| Backend files | 1 (`app.py`) | ~15 modular files |
| Test coverage | 0% | ≥80% |

---

## Open Questions

> [!IMPORTANT]
> ### Q1: Flask or FastAPI for v2 backend?
> The PRD data flow diagram mentions "FastAPI Backend" at line 1616, but the existing codebase is Flask with Flask-Login and Flask-Bcrypt. Options:
> - **A)** Keep Flask — lower migration effort, all auth logic stays intact
> - **B)** Migrate to FastAPI — better async, auto-docs, but requires rewriting auth middleware
>
> **Recommendation:** Keep Flask for Phase 2 (zero-risk extraction), evaluate FastAPI for Phase 5.

> [!IMPORTANT]
> ### Q2: Direct Supabase from frontend or via backend?
> The v2 React frontend could talk to Supabase directly (using `supabase-js`) for session saves, or continue routing through the Flask backend. Direct access is faster but reduces backend control.
>
> **Recommendation:** Route through backend API for auth-related data. Allow direct Supabase for read-heavy analytics queries.

> [!IMPORTANT]
> ### Q3: Monorepo or separate repos?
> The target structure uses a monorepo (`frontend/` + `backend/` in one repo). Alternative: separate repos with git submodules.
>
> **Recommendation:** Monorepo — simpler CI/CD, shared config, easier development.

---

## Summary

| Phase | Duration | Key Outcome |
|---|---|---|
| **Phase 1** | Week 1 | Clean repo, rotated secrets, directory skeleton |
| **Phase 2** | Week 2-3 | Modular Flask backend, no more monolith |
| **Phase 3** | Week 3-5 | Next.js frontend replicating all existing pages |
| **Phase 4** | Week 5-8 | 12-engine browser AI pipeline, 4 operational modes |
| **Phase 5** | Week 8-10 | Tests, performance, deployment, documentation |

**Total estimated effort: 8-10 weeks.**

Zero existing functionality is lost. Every reusable piece of logic, design, and data is preserved and evolved. The migration is additive — never destructive.
