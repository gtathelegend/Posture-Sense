/**
 * NotificationContext & SettingsContext
 */

export class NotificationContext {
    constructor() {
        this.notifications = [];
    }

    addNotification(message, type = 'info') {
        const notification = { id: Date.now(), message, type };
        this.notifications.push(notification);
        console.log(`[Notification ${type.toUpperCase()}]: ${message}`);
        return notification;
    }
}

export class SettingsContext {
    constructor() {
        this.settings = {
            preferredMode: 'exercise',
            autoStartCamera: false,
            soundFeedback: true
        };
    }

    updateSettings(newSettings) {
        Object.assign(this.settings, newSettings);
    }
}
