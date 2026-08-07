/**
 * ThemeContext
 * Manages theme preferences (dark/light).
 */

export class ThemeContext {
    constructor() {
        this.theme = localStorage.getItem('ps_theme') || 'dark';
        this.applyTheme(this.theme);
    }

    setTheme(newTheme) {
        this.theme = newTheme;
        localStorage.setItem('ps_theme', newTheme);
        this.applyTheme(newTheme);
    }

    toggleTheme() {
        const nextTheme = this.theme === 'dark' ? 'light' : 'dark';
        this.setTheme(nextTheme);
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
    }
}
