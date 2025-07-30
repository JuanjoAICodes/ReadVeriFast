/**
 * VeriFast Speed Reader - Enhanced Implementation
 * Provides immersive speed reading with premium features
 */

(function() {
    'use strict';
    
    function initSpeedReader() {
        console.log('Speed Reader: Initializing...');

        // Get essential elements
        const speedReaderSection = document.getElementById('speed-reader-section');
        const wordDisplay = document.getElementById('word-display');
        const startPauseBtn = document.getElementById('start-pause-btn');
        const resetBtn = document.getElementById('reset-btn');
        const speedDecreaseBtn = document.getElementById('speed-decrease');
        const speedIncreaseBtn = document.getElementById('speed-increase');
        const currentSpeedDisplay = document.getElementById('current-speed');
        const progressBar = document.getElementById('progress-bar');

        // Check if all essential elements exist
        if (!speedReaderSection || !wordDisplay || !startPauseBtn || !resetBtn || !speedDecreaseBtn || !speedIncreaseBtn || !currentSpeedDisplay || !progressBar) {
            console.error('Speed Reader: Essential elements missing');
            return;
        }

        // Get article content
        const articleContent = speedReaderSection.dataset.content;
        if (!articleContent) {
            console.error('Speed Reader: No article content found');
            return;
        }

        // Clean and split content into words
        function cleanAndSplitWords(content) {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = content;
            const cleanContent = (tempDiv.textContent || tempDiv.innerText || '').replace(/\s+/g, ' ').trim();
            return cleanContent.split(/\s+/).filter(word => word.length > 0);
        }

        const words = cleanAndSplitWords(articleContent);
        console.log(`Speed Reader: Found ${words.length} words`);

        // Get immersive overlay elements
        const immersiveOverlay = document.getElementById('immersive-overlay');
        const immersiveWordDisplay = document.getElementById('immersive-word-display');
        const immersiveProgressBar = document.getElementById('immersive-progress-bar');
        const immersiveStopBtn = document.getElementById('immersive-stop-btn');

        // Speed Reader state
        let currentIndex = 0;
        let intervalId = null;
        let isRunning = false;
        let isImmersiveMode = false;
        let wpm = parseInt(currentSpeedDisplay.textContent) || 250;
        let currentChunks = words; // Start with single words

        // Core functions
        function showWord() {
            if (currentIndex < currentChunks.length) {
                const currentWord = currentChunks[currentIndex];
                wordDisplay.textContent = currentWord;
                progressBar.value = (currentIndex + 1) / currentChunks.length * 100;
                
                // Update immersive display if active
                if (isImmersiveMode && immersiveWordDisplay) {
                    immersiveWordDisplay.textContent = currentWord;
                    
                    // Ensure word fits on one line by adjusting font size if needed
                    adjustFontSizeForWord(immersiveWordDisplay, currentWord);
                    
                    if (immersiveProgressBar) {
                        immersiveProgressBar.style.width = progressBar.value + '%';
                    }
                }
                
                currentIndex++;
            } else {
                // Finished reading
                wordDisplay.textContent = window.i18n ? window.i18n._('finished') : 'Reading finished!';
                if (isImmersiveMode && immersiveWordDisplay) {
                    immersiveWordDisplay.textContent = window.i18n ? window.i18n._('finished') : 'Reading finished!';
                    immersiveWordDisplay.style.fontSize = '4rem'; // Reset font size
                    hideImmersiveOverlay();
                }
                pauseReading();
            }
        }

        function adjustFontSizeForWord(element, word) {
            // Reset to default size first
            element.style.fontSize = '4rem';
            
            // Force a single line display
            element.style.whiteSpace = 'nowrap';
            element.style.overflow = 'hidden';
            
            // Check if word is too wide and reduce font size if needed
            const maxWidth = window.innerWidth * 0.9; // 90% of viewport width
            
            // Create a temporary element to measure text width
            const tempElement = document.createElement('div');
            tempElement.style.position = 'absolute';
            tempElement.style.visibility = 'hidden';
            tempElement.style.whiteSpace = 'nowrap';
            tempElement.style.fontSize = '4rem';
            tempElement.style.fontWeight = '300';
            tempElement.style.letterSpacing = '0.05em';
            tempElement.textContent = word;
            document.body.appendChild(tempElement);
            
            let fontSize = 4;
            while (tempElement.offsetWidth > maxWidth && fontSize > 1.5) {
                fontSize -= 0.2;
                tempElement.style.fontSize = fontSize + 'rem';
                element.style.fontSize = fontSize + 'rem';
            }
            
            document.body.removeChild(tempElement);
        }

        function startReading() {
            if (intervalId) clearInterval(intervalId);
            const interval = 60000 / wpm; // Convert WPM to milliseconds
            intervalId = setInterval(showWord, interval);
            startPauseBtn.textContent = window.i18n ? window.i18n._('pause') : 'Pause';
            isRunning = true;
        }

        function pauseReading() {
            if (intervalId) {
                clearInterval(intervalId);
                intervalId = null;
            }
            startPauseBtn.textContent = window.i18n ? window.i18n._('start') : 'Start Reading';
            isRunning = false;
        }

        function resetReading() {
            pauseReading();
            currentIndex = 0;
            progressBar.value = 0;
            wordDisplay.textContent = window.i18n ? window.i18n._('click_start') : 'Click Start to begin reading';
            if (isImmersiveMode) {
                hideImmersiveOverlay();
            }
        }

        function updateWpm(newWpm) {
            wpm = Math.max(50, Math.min(1000, newWpm)); // Clamp between 50-1000
            currentSpeedDisplay.textContent = wpm;
            // Restart reading with new speed if currently running
            if (isRunning) {
                pauseReading();
                startReading();
            }
        }

        function increaseSpeed() {
            updateWpm(wpm + 5);
        }

        function decreaseSpeed() {
            updateWpm(wpm - 5);
        }

        // Immersive mode functions
        function showImmersiveOverlay() {
            if (!immersiveOverlay || !immersiveWordDisplay) {
                console.log('Speed Reader: Immersive mode not available');
                return false;
            }

            isImmersiveMode = true;
            immersiveOverlay.classList.add('active');
            immersiveOverlay.setAttribute('aria-hidden', 'false');
            document.body.style.overflow = 'hidden';
            
            // Sync with current word
            const displayText = currentIndex < currentChunks.length ? currentChunks[currentIndex] : "Ready to Read";
            immersiveWordDisplay.textContent = displayText;
            
            if (immersiveProgressBar) {
                immersiveProgressBar.style.width = progressBar.value + '%';
            }
            
            console.log('Speed Reader: Immersive mode activated');
            return true;
        }

        function hideImmersiveOverlay() {
            if (!immersiveOverlay) return;
            
            isImmersiveMode = false;
            immersiveOverlay.classList.remove('active');
            immersiveOverlay.setAttribute('aria-hidden', 'true');
            document.body.style.overflow = '';
            console.log('Speed Reader: Immersive mode deactivated');
        }

        // Event listeners
        startPauseBtn.addEventListener('click', () => {
            console.log('Speed Reader: Start/Pause clicked');
            
            if (!words || words.length === 0) {
                wordDisplay.textContent = window.i18n ? window.i18n._('no_content') : 'No content available';
                return;
            }

            if (isRunning) {
                pauseReading();
                if (isImmersiveMode) {
                    hideImmersiveOverlay();
                }
            } else {
                // Reset if finished
                if (currentIndex >= currentChunks.length) {
                    resetReading();
                }
                
                // Show immersive overlay and start reading
                showImmersiveOverlay();
                startReading();
            }
        });

        resetBtn.addEventListener('click', resetReading);
        speedDecreaseBtn.addEventListener('click', decreaseSpeed);
        speedIncreaseBtn.addEventListener('click', increaseSpeed);

        // Immersive stop button
        if (immersiveStopBtn) {
            immersiveStopBtn.addEventListener('click', () => {
                pauseReading();
                hideImmersiveOverlay();
            });
        }

        // Original article show/hide functionality
        const showOriginalBtn = document.getElementById('show-original-article');
        const hideOriginalBtn = document.getElementById('hide-original-article');
        const fullArticleContent = document.getElementById('full-article-content');

        if (showOriginalBtn && hideOriginalBtn && fullArticleContent) {
            showOriginalBtn.addEventListener('click', () => {
                fullArticleContent.style.display = 'block';
                showOriginalBtn.parentElement.style.display = 'none';
            });

            hideOriginalBtn.addEventListener('click', () => {
                fullArticleContent.style.display = 'none';
                showOriginalBtn.parentElement.style.display = 'block';
            });
        }

        // Connector words for smart grouping
        const connectorWords = new Set([
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'el', 'la', 'los', 'las', 'un', 'una', 'y', 'o', 'pero', 'en', 'con', 'por', 'para', 'de'
        ]);

        // Advanced chunking function with connector grouping
        function createAdvancedChunks(wordArray, chunkSize, groupConnectors) {
            if (chunkSize === 1 && !groupConnectors) {
                return wordArray;
            }
            
            const chunks = [];
            let i = 0;
            
            while (i < wordArray.length) {
                let chunk = [];
                
                // If grouping connectors, check if current word is a connector
                if (groupConnectors && i < wordArray.length - 1) {
                    const currentWord = wordArray[i].toLowerCase();
                    const nextWord = wordArray[i + 1] ? wordArray[i + 1].toLowerCase() : '';
                    
                    // If current word is a connector, group it with the next word
                    if (connectorWords.has(currentWord) && !connectorWords.has(nextWord)) {
                        chunk.push(wordArray[i], wordArray[i + 1]);
                        i += 2;
                    }
                }
                
                // Add remaining words to reach chunk size
                while (chunk.length < chunkSize && i < wordArray.length) {
                    chunk.push(wordArray[i]);
                    i++;
                }
                
                if (chunk.length > 0) {
                    chunks.push(chunk.join(' '));
                }
            }
            
            return chunks;
        }
        
        // Note: Advanced features (chunking, fonts, smart features) will be loaded from user profile settings
        // For now, using simple single-word display

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            
            switch (e.key) {
                case ' ':
                    e.preventDefault();
                    startPauseBtn.click();
                    break;
                case 'Escape':
                    if (isImmersiveMode) {
                        hideImmersiveOverlay();
                        pauseReading();
                    }
                    break;
                case 'r':
                case 'R':
                    resetBtn.click();
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    increaseSpeed();
                    break;
                case 'ArrowDown':
                    e.preventDefault();
                    decreaseSpeed();
                    break;
            }
        });

        console.log('Speed Reader: Initialization complete');
    }

    // Initialize speed reader when DOM is loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSpeedReader);
    } else {
        initSpeedReader();
    }
})();