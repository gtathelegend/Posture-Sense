# PostureSense Frontend Architecture Specification

**Version:** 2.0.0 (Milestone 3)  
**Status:** Completed  

---

## 1. Overview

The PostureSense v2 frontend architecture establishes a modular, component-driven client architecture to support browser-based computer vision engines (Camera, MediaPipe, EventBus, Analytics, Dashboard) while maintaining 100% visual equivalence and zero breaking changes to existing templates.

---

## 2. Directory Structure

```
static/assets/js/
├── components/               # Modular UI component definitions
│   ├── layout/               # Main, Dashboard, Auth & Error layouts
│   ├── navigation/           # NavBar, Footer
│   ├── cards/                # StatCard, CameraCard, PoseCard
│   ├── forms/                # LoginForm, RegisterForm, ContactForm
│   ├── buttons/              # Action buttons
│   ├── modals/               # Confirm & Info modals
│   ├── charts/               # Analytics chart helpers
│   ├── feedback/             # Alert & Toast indicators
│   ├── dashboard/            # Overview & Recent Sessions widgets
│   └── shared/               # Loading, EmptyState, Offline indicators
├── services/                 # API Communication Layer
│   ├── auth_service.js       # Authentication requests (/login, /register, /logout)
│   ├── dashboard_service.js  # Dashboard metrics (/api/dashboard_stats)
│   ├── analytics_service.js  # Session analytics helpers
│   ├── contact_service.js    # Contact & newsletter submissions (/contact, /subscribe)
│   ├── session_service.js    # Session saving (/save_pose_session)
│   ├── health_service.js     # Health check (/health, /version)
│   ├── camera_service.js     # Camera control placeholder (/stop_camera)
│   └── engine_service.js     # Engine status placeholder (/status, /get_status)
├── types/                    # Shared frontend types & schemas
│   ├── user.js
│   ├── dashboard.js
│   ├── analytics.js
│   ├── session.js
│   ├── api.js
│   ├── settings.js
│   └── notifications.js
├── context/                  # State management providers
│   ├── AuthContext.js
│   ├── ThemeContext.js
│   ├── NotificationContext.js
│   ├── SettingsContext.js
│   └── EngineContext.js      # Future engine state provider
├── adapters/                 # EventBus translation layer
│   └── EngineAdapter.js      # Translates EventBus events -> UI state
└── utils/                    # Frontend helpers & utilities
    └── debug_overlay.js      # System diagnostic panel (toggled via CTRL + SHIFT + D)
```

---

## 3. Key Architectural Layers

### 3.1 Service Layer (`services/`)
- Encapsulates all backend HTTP network requests (`fetch`).
- UI components and context providers do not make direct fetch calls; all communication passes through services (`AuthService`, `DashboardService`, `SessionService`, `ContactService`, `HealthService`).

### 3.2 Context Providers (`context/`)
- `EngineContext`: Holds future engine states (`currentPose`, `fps`, `status`, `isCameraActive`).
- `ThemeContext`: Manages dark/light theme preferences in `localStorage`.
- `NotificationContext`: Manages toast and alert feedback.

### 3.3 Engine Adapter (`adapters/EngineAdapter.js`)
- Decouples UI components from low-level EventBus subscriptions.
- Translates `EventBus` events (e.g. `camera.started`, `pose.recognized`, `camera.error`) directly into `EngineContext` state updates.

### 3.4 Diagnostics & Debug Overlay
- **Developer Playground**: Accessible at `/playground` for monitoring core application versions, configuration schemas, and engine registration status.
- **Debug Overlay**: Global system overlay toggling via `CTRL + SHIFT + D`, rendering live route, event count, memory availability, and backend health status.
