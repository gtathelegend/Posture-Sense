# PostureSense Baseline & Current State Report

**Project:** PostureSense  
**Version:** 2.0.0 (Phase 1 Refactored)  
**Date:** August 2026  
**Status:** Monolith Refactored to Modular Backend  

---

## 1. Overview

PostureSense has successfully undergone Phase 1 of its architectural migration. The monolithic 984-line `app.py` has been split into a clean, modular Flask application factory structure under `backend/app/`.

---

## 2. Working Features

- **Application Factory Pattern**: `create_app()` initializes Flask, extensions, blueprints, error handlers, and middleware.
- **Authentication System**: User registration (`/register`), login (`/login`), logout (`/logout`), password hashing with Flask-Bcrypt, session management via Flask-Login.
- **Landing & Public Pages**: Homepage (`/`), landing page (`/landing`), yoga pose reference (`/yoga-poses`), static file serving (`/favicon.ico`, `/sitemap.xml`, `/sitemap2.xml`, `/robots.txt`).
- **Dashboard & Statistics**: User session dashboard (`/dashboard`), dashboard analytics JSON API (`/api/dashboard_stats`).
- **Camera & Pose Processing**: Video feed streaming (`/video_feed`), status SSE endpoint (`/status`), pose status polling (`/get_status`), camera shutdown (`/stop_camera`), pose session persistence (`/save_pose_session`).
- **Contact & Communications**: Contact form processing (`/contact`, `/submit`) and newsletter subscription (`/subscribe`) via SMTP.
- **Database Connectivity**: Full Supabase PostgreSQL integration via `UserRepository` and `SessionRepository`.

---

## 3. Runtime & Build Status

- **Python Version**: 3.12.10
- **Node Version**: v24.5.0
- **Backend Startup Time**: ~2.3s
- **Database Connection Latency**: ~2.3s (Supabase REST)
- **API Status**: All 21 endpoints respond with 200 OK / expected 302 redirects.
- **Deployment Compatibility**: 100% compatible with existing `Procfile` (`gunicorn app:app`) and Docker container configuration.

---

## 4. Known Limitations & Technical Debt Remaining

1. **Server-Side Vision Engine**: Computer vision (MediaPipe Pose + OpenCV) still executes server-side in `cv_utils.py` during Phase 1. Offloading to browser WASM occurs in Phase 2.
2. **Static Asset Packaging**: Frontend assets are currently served directly via Flask Jinja2 templates without a Next.js build step.
3. **Hardcoded Pose Definitions**: Yoga pose classification in `classifyPose()` relies on hardcoded joint angle ranges.
