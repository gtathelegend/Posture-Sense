/**
 * Settings & Notification Types
 */

export class SettingsType {
    constructor({ theme = 'dark', mode = 'exercise', sound_effects = true, debug_overlay = false } = {}) {
        this.theme = theme;
        this.mode = mode;
        this.sound_effects = sound_effects;
        this.debug_overlay = debug_overlay;
    }
}

export class NotificationType {
    constructor({ id, type = 'info', message = '', timestamp = new Date().toISOString() } = {}) {
        this.id = id || Math.random().toString(36).substr(2, 9);
        this.type = type; // info, success, warning, error
        this.message = message;
        this.timestamp = timestamp;
    }
}
