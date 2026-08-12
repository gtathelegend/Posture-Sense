# PostureSense Security Specification

**Version:** 2.0.0  
**Status:** Completed (Milestone 10)  

---

## 1. Threat Model & Security Controls

PostureSense v2 enforces multi-layer security controls designed for client-side AI perception and cloud-assisted analytics:

| Category | Security Control | Implementation Location |
|---|---|---|
| **Authentication** | Flask-Login session management, password hashing via `Flask-Bcrypt` | `backend/app/services/auth_service.py` |
| **Authorization & User Isolation** | All protected endpoints scope queries strictly to `current_user.id` | `backend/app/blueprints/api/routes.py` |
| **IDOR Protection** | Resource ownership verified via `user_id` repository filters; path tampering rejected | `backend/app/repositories/analytics_repository.py` |
| **Production Secret Validation** | Startup fail-fast guard rejects default `SECRET_KEY` in production (`FLASK_ENV=production`) | `backend/app/config.py` |
| **CORS Policy** | Restricted origin parsing (`ALLOWED_ORIGINS`) with `supports_credentials=True` | `backend/app/__init__.py` |
| **Cookie Hardening** | `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE='Lax'`, `SESSION_COOKIE_SECURE=True` | `backend/app/config.py` |
| **Security Headers** | `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Permissions-Policy: camera=(self)` | `backend/app/middleware/security.py` |
| **Resource Limits** | `MAX_CONTENT_LENGTH = 16MB` payload limit to prevent Denial-of-Service memory exhaustion | `backend/app/config.py` |
| **Report Export Security** | Streamed directly as authenticated inline/attachment downloads; zero public static file writing | `backend/app/services/report_service.py` |

---

## 2. Secrets Management & Secret Audit Findings

- **Secret Audit Result**: **SAFE**. Repo audit confirmed zero committed production credentials. All keys (`SECRET_KEY`, `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `EMAIL_PASSWORD`) are loaded strictly from system environment variables via `python-dotenv`.
- **Environment Template**: [.env.example](file:///d:/Github/Posture-Sense/.env.example) provides safe placeholders for development and deployment reference.
