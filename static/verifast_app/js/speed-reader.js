/**
 * Minimal Immersive Speed Reader - 30 Lines
 * Single-mode full-screen reading with full-width white text strip
 */
document.addEventListener('DOMContentLoaded', function () {
    // Translation function using context processor data
    function _(key) {
        const translations = window.jsTranslations || {};
        return translations[key] || key;
    }

    const section = document.getElementById('speed-reader-section');
    const startBtn = document.getElementById('start-reading-btn');
    const wpmSelector = document.getElementById('wpm-selector');
    const currentWpmDisplay = document.getElementById('current-wpm');
    const overlay = document.getElementById('immersive-overlay');
    const wordDisplay = document.getElementById('immersive-word-display');
    const exitBtn = document.getElementById('exit-reading-btn');

    if (!section || !startBtn || !overlay || !wordDisplay || !exitBtn || !wpmSelector) return;

    let words = section.dataset.content?.replace(/\s+/g, ' ').trim().split(' ').filter(w => w) || [];
    let currentIndex = 0;
    let isRunning = false;
    let intervalId = null;

    function getSelectedWPM() {
        return parseInt(wpmSelector.value) || 250;
    }

    function updateCurrentWPMDisplay() {
        if (currentWpmDisplay) currentWpmDisplay.textContent = getSelectedWPM();
    }

    function updateDisplay() {
        wordDisplay.textContent = words[currentIndex] || _('reading_finished');
    }

    // Update WPM display when selector changes
    wpmSelector.addEventListener('change', updateCurrentWPMDisplay);

    startBtn.addEventListener('click', () => {
        const wpm = getSelectedWPM();
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
        currentIndex = 0;
        updateDisplay();
        intervalId = setInterval(() => {
            if (currentIndex >= words.length) {
                clearInterval(intervalId);
                isRunning = false;
                // HTMX notification for reading completion
                const articleId = section.dataset.articleId;
                if (articleId && typeof htmx !== 'undefined') {
                    htmx.ajax('POST', `/reading/complete/${articleId}/`, {
                        target: '#quiz-container',
                        swap: 'innerHTML'
                    });
                }
                return;
            }
            updateDisplay();
            currentIndex++;
        }, 60000 / wpm);
        isRunning = true;
    });

    exitBtn.addEventListener('click', () => {
        overlay.classList.remove('active');
        document.body.style.overflow = '';
        if (intervalId) clearInterval(intervalId);
        isRunning = false;
    });

    document.addEventListener('keydown', (e) => {
        if (!overlay.classList.contains('active')) return;
        if (e.key === 'Escape') exitBtn.click();
    });

    // Initialize display
    updateCurrentWPMDisplay();
    window.speedReader = { onReadingComplete: null };
});