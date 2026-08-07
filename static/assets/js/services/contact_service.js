/**
 * ContactService
 * Handles contact form and newsletter subscription requests.
 */

export class ContactService {
    static async submitContact(name, email, message) {
        const formData = new FormData();
        formData.append('name', name);
        formData.append('email', email);
        formData.append('message', message);

        const response = await fetch('/contact', {
            method: 'POST',
            body: formData
        });
        return await response.json();
    }

    static async subscribeNewsletter(email) {
        const formData = new FormData();
        formData.append('email', email);

        const response = await fetch('/subscribe', {
            method: 'POST',
            body: formData
        });
        return await response.json();
    }
}
