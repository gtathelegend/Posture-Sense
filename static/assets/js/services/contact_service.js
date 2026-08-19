/**
 * ContactService
 * Handles contact form and newsletter subscription requests with timeout support.
 */

export class ContactService {
    static async submitContact(name, email, message, options = {}) {
        const formData = new FormData();
        formData.append('name', name);
        formData.append('email', email);
        formData.append('message', message);

        const fetchOptions = {
            method: 'POST',
            body: formData,
        };
        if (options.signal) {
            fetchOptions.signal = options.signal;
        }

        const response = await fetch('/contact', fetchOptions);
        const data = await response.json().catch(() => ({}));
        return { ok: response.ok, status: response.status, data };
    }

    static async subscribeNewsletter(email, options = {}) {
        const formData = new FormData();
        formData.append('email', email);

        const fetchOptions = {
            method: 'POST',
            body: formData,
        };
        if (options.signal) {
            fetchOptions.signal = options.signal;
        }

        const response = await fetch('/subscribe', fetchOptions);
        const data = await response.json().catch(() => ({}));
        return { ok: response.ok, status: response.status, data };
    }
}
