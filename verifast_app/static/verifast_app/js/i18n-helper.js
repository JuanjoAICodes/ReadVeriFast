/**
 * JavaScript Internationalization Helper
 * Provides client-side translation support for VeriFast
 */

class I18nHelper {
    constructor() {
        this.currentLanguage = document.documentElement.lang || 'en';
        this.translations = {};
        this.loadTranslations();
    }

    loadTranslations() {
        // Load translations from Django context or API
        const translationsElement = document.getElementById('js-translations');
        if (translationsElement) {
            try {
                this.translations = JSON.parse(translationsElement.textContent);
            } catch (e) {
                console.warn('Failed to load JavaScript translations:', e);
            }
        }
    }

    translate(key, params = {}) {
        let translation = this.translations[key] || key;
        
        // Simple parameter substitution
        Object.keys(params).forEach(param => {
            translation = translation.replace(`{${param}}`, params[param]);
        });
        
        return translation;
    }

    // Alias for shorter usage
    _(key, params = {}) {
        return this.translate(key, params);
    }
}

// Global instance
window.i18n = new I18nHelper();