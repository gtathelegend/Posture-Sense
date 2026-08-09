/**
 * EventBus
 * Production-grade, lightweight in-memory event bus for PostureSense v2 browser engine pipeline.
 */

export class EventBus {
    constructor() {
        this.listeners = new Map();
        this.wildcardListeners = new Set();
    }

    /**
     * Subscribe to an event topic or all events ('*')
     * @param {string} eventName
     * @param {function} handler
     * @returns {function} Unsubscribe function
     */
    subscribe(eventName, handler) {
        if (typeof handler !== 'function') {
            console.error('[EventBus] Handler must be a function', handler);
            return () => {};
        }

        if (eventName === '*') {
            this.wildcardListeners.add(handler);
            return () => this.unsubscribe('*', handler);
        }

        if (!this.listeners.has(eventName)) {
            this.listeners.set(eventName, new Set());
        }
        this.listeners.get(eventName).add(handler);

        return () => this.unsubscribe(eventName, handler);
    }

    /**
     * Unsubscribe a handler from an event topic
     * @param {string} eventName
     * @param {function} handler
     */
    unsubscribe(eventName, handler) {
        if (eventName === '*') {
            this.wildcardListeners.delete(handler);
            return;
        }

        if (this.listeners.has(eventName)) {
            this.listeners.get(eventName).delete(handler);
            if (this.listeners.get(eventName).size === 0) {
                this.listeners.delete(eventName);
            }
        }
    }

    /**
     * Publish an event to subscribers
     * @param {string} eventName
     * @param {*} data
     */
    publish(eventName, data) {
        const eventObject = {
            name: eventName,
            data: data,
            timestamp: Date.now()
        };

        // Notify specific subscribers
        if (this.listeners.has(eventName)) {
            for (const handler of Array.from(this.listeners.get(eventName))) {
                try {
                    handler(eventObject);
                } catch (err) {
                    console.error(`[EventBus] Error executing subscriber for '${eventName}':`, err);
                }
            }
        }

        // Notify wildcard subscribers
        for (const handler of Array.from(this.wildcardListeners)) {
            try {
                handler(eventObject);
            } catch (err) {
                console.error(`[EventBus] Error executing wildcard subscriber for '${eventName}':`, err);
            }
        }
    }

    /**
     * Clear all subscribers
     */
    clear() {
        this.listeners.clear();
        this.wildcardListeners.clear();
    }
}
