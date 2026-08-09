# PostureSense Free-Tier Deployment Guide

**Version:** 2.0.0  
**Status:** Completed (Milestone 10)  

---

## 1. Deployment Architecture

PostureSense v2 uses a hybrid client-cloud architecture optimized for free-tier hosting platforms:

- **Frontend Platform**: **Vercel** (Static HTML5, CSS3, JavaScript ES Modules, Web Worker, WASM assets).
- **Backend Platform**: **Render** (Flask REST API service, Gunicorn HTTP server).
- **Database Platform**: **Supabase** (PostgreSQL database, authentication, user tables).

---

## 2. Environment Variables Matrix

### Render (Backend Service)
```ini
FLASK_ENV=production
SECRET_KEY=your-32-byte-secure-random-production-key
ALLOWED_ORIGINS=https://posturesense.vercel.app
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_PUBLISHABLE_KEY=your-supabase-publishable-key
SUPABASE_SECRET_KEY=your-supabase-secret-role-key
```

### Vercel (Frontend Hosting)
```ini
VITE_API_URL=https://posturesense-api.onrender.com
```

---

## 3. Free-Tier Limitations & Mitigations

- **Render Cold Starts**: Render free instances sleep after 15 minutes of inactivity. Cold start latency is ~30–50s.
  - *Mitigation*: Client-side perception engine (Camera, MediaPipe, Landmarks, Biomechanics, Pose Rules) runs 100% locally in the browser and remains functional during backend wake-up.
- **Model Asset Delivery**: WASM and `.task` files hosted on CDN (`jsdelivr`) for global caching.
