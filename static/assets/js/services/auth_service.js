/**
 * AuthService
 * Frontend communication layer for authentication endpoints.
 */

export class AuthService {
    static async login(username, password) {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch('/login', {
            method: 'POST',
            body: formData
        });
        return response;
    }

    static async register(username, email, password, confirmPassword) {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('email', email);
        formData.append('password', password);
        formData.append('confirm_password', confirmPassword);

        const response = await fetch('/register', {
            method: 'POST',
            body: formData
        });
        return response;
    }

    static async logout() {
        window.location.href = '/logout';
    }
}
