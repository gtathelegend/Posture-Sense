/**
 * User Type Definition
 * Represents authenticated user state in the PostureSense frontend.
 */

export class UserType {
    constructor({ id, username, email, created_at, preferred_mode = 'exercise' } = {}) {
        this.id = id || '';
        this.username = username || '';
        this.email = email || '';
        this.created_at = created_at || new Date().toISOString();
        this.preferred_mode = preferred_mode;
    }

    isAuthenticated() {
        return Boolean(this.id);
    }
}
