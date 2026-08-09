# PostureSense Repository Folder & File Audit

**Version:** 2.0.0  
**Date:** 2026-08-09  
**Auditor:** Lead Release Engineer  

---

## Executive Summary

This repository audit classifies every top-level file and directory in the `Posture-Sense` workspace into four operational categories: **KEEP**, **REMOVE**, **ARCHIVE**, and **DOCUMENT**. All temporary artifacts, duplicate files, and dead scripts have been audited to ensure a clean, production-ready open-source codebase.

---

## Directory & File Classification Matrix

| Path | Category | Purpose / Description | Action Taken |
|---|---|---|---|
| `.github/` | **KEEP / ENHANCE** | CI/CD workflows, issue templates, pull request template. | Added `ci.yml`, bug report template, feature request template, PR template. |
| `.vscode/` | **KEEP** | Workspace editor settings (`settings.json`). | Preserved in repository. |
| `.devcontainer/` | **DOCUMENT** | VS Code development container configuration. | Retained and documented in deployment guides. |
| `.deployment` | **DOCUMENT** | Deployment target metadata. | Retained for deployment tooling reference. |
| `app.py` | **KEEP** | Root application entrypoint serving `backend.app.create_app()` for Gunicorn / Flask CLI. | Maintained as production WSGI entrypoint. |
| `backend/` | **KEEP** | Modular Flask backend application (`app/` blueprints, services, repositories, models, middleware). | Core v2 application logic. |
| `docs/` | **KEEP** | Architecture specifications, engine specs, security, performance benchmarks, demo guide, testing guides. | Expanded with comprehensive v2 documentation suite. |
| `Dockerfile` | **KEEP** | Container build definition for containerized backend deployments. | Updated and verified. |
| `favicon.ico` | **KEEP** | Platform branding favicon asset. | Preserved. |
| `LICENSE` | **KEEP** | MIT Open-Source License document. | Verified standard open-source license. |
| `Procfile` | **KEEP** | Web process declaration for Render / Heroku (`web: gunicorn app:app`). | Preserved. |
| `README.md` | **KEEP / REDESIGN** | Primary project presentation, architecture diagrams, installation, benchmarks. | Redesigned into professional release README. |
| `requirements.txt` | **KEEP / CLEANUP** | Python backend dependencies. | Audited and verified. |
| `robots.txt` | **KEEP** | Search engine crawler rules. | Preserved. |
| `runtime.txt` | **KEEP** | Language runtime version specification (`python-3.12.10`). | Preserved. |
| `shared/` | **KEEP** | Core engine implementation (11 JavaScript/Python modular engines, Event Bus, schemas, YAML configs). | Core v2 engine suite. |
| `sitemap.xml` | **KEEP** | Production site XML sitemap. | Retained. |
| `sitemap2.xml` | **REMOVE** | Duplicate XML sitemap containing secondary domain reference. | **REMOVED**. |
| `startup.sh` | **KEEP** | Production container startup shell script. | Preserved. |
| `static/` | **KEEP** | Web frontend assets (JavaScript engine modules, CSS design system, images). | Core v2 frontend code. |
| `supabase_schema.sql` | **KEEP** | PostgreSQL database schema for Supabase integration. | Preserved. |
| `templates/` | **KEEP** | Modernized HTML Jinja2 templates (landing, dashboard, playground, auth views). | Core v2 UI templates. |
| `test.py` | **REMOVE** | Outdated root-level SMTP email test script. | **REMOVED**. |
| `tests/` | **KEEP** | Automated Pytest test suite (111 unit, integration, and security tests). | 100% passing test suite. |
| `posture_sense_audit.md` | **ARCHIVE** | Legacy Phase 1 audit document. | Archived in `docs/` references. |
| `implementation_plan.md` | **DOCUMENT** | Milestone migration and release implementation plans. | Maintained for technical governance. |
| `mediapipe/` | **REMOVE / GITIGNORE** | Orphaned Python virtualenv directory. | Gitignored & isolated from distribution. |
| `mediapipe_old/` | **REMOVE / GITIGNORE** | Legacy Python virtualenv directory. | Gitignored & isolated from distribution. |
| `venv/`, `.venv/`, `install/` | **REMOVE / GITIGNORE** | Local Python virtual environments. | Gitignored. |
| `.pytest_cache/`, `__pycache__/` | **REMOVE / GITIGNORE** | Python compiler and test execution caches. | Gitignored. |

---

## Verification Audit Checklist

- [x] Zero hardcoded secrets or credentials committed in any directory.
- [x] Zero duplicate sitemaps or outdated test scripts in workspace root.
- [x] All 11 core engines accounted for in `shared/` and `static/assets/js/engine/`.
- [x] All 111 pytest test modules residing under `tests/`.
- [x] Clear isolation between backend API code (`backend/app`), shared engines (`shared/`), and frontend assets (`static/`).
