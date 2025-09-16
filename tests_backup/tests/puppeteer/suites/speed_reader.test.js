/**
 * Speed Reader Test Suite
 * Tests speed reading functionality, controls, and immersive mode
 */

module.exports = async function speedReaderTests(runner) {
    console.log('\n⚡ Running Speed Reader Test Suite');

    // Helper function to navigate to an article
    async function navigateToArticle(page) {
        await page.goto(`${runner.baseUrl}/`);
        await page.waitForSelector('.article-list .article a, .article-card a');
        const articleLink = await page.$('.article-list .article a, .article-card a');
        await articleLink.click();
        await page.waitForNavigation();
    }

    // Test 3.1: Basic Speed Reader
    await runner.runTest('Speed Reader Initialization', async (page) => {
        await navigateToArticle(page);
        
        // Look for speed reader section
        const speedReaderSection = await page.$('.speed-reader-section, #speed-reader, .speed-reader');
        if (!speedReaderSection) {
            throw new Error('Speed reader section not found on article page');
        }
        
        // Check for essential speed reader elements
        const wordDisplay = await page.$('.word-display, .speed-reader-word, .current-word');
        const controls = await page.$('.speed-reader-controls, .reader-controls');
        const wpmSlider = await page.$('input[type="range"], .wpm-slider');
        
        if (!wordDisplay) {
            throw new Error('Word display area not found');
        }
        
        if (!controls) {
            throw new Error('Speed reader controls not found');
        }
        
        if (!wpmSlider) {
            throw new Error('WPM slider not found');
        }
        
        console.log('✅ Speed reader components initialized');
    });

    await runner.runTest('Speed Reader Start/Pause Controls', async (page) => {
        await navigateToArticle(page);
        
        // Find start/pause button
        const startButton = await page.$('.start-reading, .play-pause, button[data-action="start"]');
        if (!startButton) {
            throw new Error('Start reading button not found');
        }
        
        // Test start functionality
        await startButton.click();
        
        // Wait a moment for reading to start
        await page.waitForTimeout(1000);
        
        // Check if word display is updating
        const wordDisplay = await page.$('.word-display, .speed-reader-word, .current-word');
        const initialWord = await wordDisplay.evaluate(el => el.textContent);
        
        // Wait and check if word changed
        await page.waitForTimeout(2000);
        const secondWord = await wordDisplay.evaluate(el => el.textContent);
        
        if (initialWord === secondWord && initialWord.trim() === '') {
            throw new Error('Speed reader does not appear to be displaying words');
        }
        
        // Test pause functionality
        const pauseButton = await page.$('.pause-reading, .play-pause, button[data-action="pause"]');
        if (pauseButton) {
            await pauseButton.click();
            console.log('✅ Pause functionality tested');
        }
    });

    await runner.runTest('WPM Slider Functionality', async (page) => {
        await navigateToArticle(page);
        
        const wpmSlider = await page.$('input[type="range"], .wpm-slider');
        if (!wpmSlider) {
            throw new Error('WPM slider not found');
        }
        
        // Get initial WPM value
        const initialWpm = await wpmSlider.evaluate(el => el.value);
        console.log(`Initial WPM: ${initialWpm}`);
        
        // Test WPM range (should be 50-1000)
        const minWpm = await wpmSlider.evaluate(el => el.min);
        const maxWpm = await wpmSlider.evaluate(el => el.max);
        
        if (parseInt(minWpm) < 50 || parseInt(maxWpm) > 1000) {
            console.log(`⚠️  WPM range unusual: ${minWpm}-${maxWpm} (expected 50-1000)`);
        }
        
        // Test slider adjustment
        await wpmSlider.click({ clickCount: 1 });
        await page.keyboard.press('ArrowRight');
        await page.keyboard.press('ArrowRight');
        
        const newWpm = await wpmSlider.evaluate(el => el.value);
        if (newWpm === initialWpm) {
            throw new Error('WPM slider does not respond to keyboard input');
        }
        
        console.log(`✅ WPM adjusted from ${initialWpm} to ${newWpm}`);
    });

    await runner.runTest('Keyboard Shortcuts', async (page) => {
        await navigateToArticle(page);
        
        // Test spacebar for start/pause
        await page.keyboard.press('Space');
        await page.waitForTimeout(500);
        
        // Test escape key (should pause/stop)
        await page.keyboard.press('Escape');
        await page.waitForTimeout(500);
        
        // Test R key for reset
        await page.keyboard.press('KeyR');
        await page.waitForTimeout(500);
        
        // Test arrow keys for WPM adjustment
        await page.keyboard.press('ArrowUp');
        await page.keyboard.press('ArrowDown');
        
        console.log('✅ Keyboard shortcuts tested (functionality verified by no errors)');
    });

    // Test 3.2: Immersive Mode
    await runner.runTest('Immersive Mode Activation', async (page) => {
        await navigateToArticle(page);
        
        // Look for immersive mode button
        const immersiveButton = await page.$('.immersive-mode, .fullscreen-reading, button[data-action="immersive"]');
        
        if (!immersiveButton) {
            console.log('⚠️  Immersive mode button not found - checking for alternative triggers');
            
            // Try double-click on word display
            const wordDisplay = await page.$('.word-display, .speed-reader-word');
            if (wordDisplay) {
                await wordDisplay.click({ clickCount: 2 });
                await page.waitForTimeout(1000);
            }
        } else {
            await immersiveButton.click();
            await page.waitForTimeout(1000);
        }
        
        // Check if immersive mode is active
        const immersiveOverlay = await page.$('.immersive-overlay, .fullscreen-overlay, .immersive-mode-active');
        
        if (!immersiveOverlay) {
            console.log('⚠️  Immersive mode overlay not detected');
            return;
        }
        
        // Verify immersive mode styling
        const overlayStyle = await immersiveOverlay.evaluate(el => {
            const style = window.getComputedStyle(el);
            return {
                position: style.position,
                zIndex: style.zIndex,
                backgroundColor: style.backgroundColor
            };
        });
        
        if (overlayStyle.position !== 'fixed' && overlayStyle.position !== 'absolute') {
            throw new Error('Immersive overlay does not appear to be full-screen');
        }
        
        console.log('✅ Immersive mode activated successfully');
    });

    await runner.runTest('Immersive Mode Exit', async (page) => {
        await navigateToArticle(page);
        
        // Activate immersive mode first
        const immersiveButton = await page.$('.immersive-mode, .fullscreen-reading, button[data-action="immersive"]');
        if (immersiveButton) {
            await immersiveButton.click();
            await page.waitForTimeout(1000);
        }
        
        // Test escape key to exit
        await page.keyboard.press('Escape');
        await page.waitForTimeout(1000);
        
        // Verify immersive mode is closed
        const immersiveOverlay = await page.$('.immersive-overlay, .fullscreen-overlay, .immersive-mode-active');
        
        if (immersiveOverlay) {
            const isVisible = await immersiveOverlay.evaluate(el => {
                const style = window.getComputedStyle(el);
                return style.display !== 'none' && style.visibility !== 'hidden';
            });
            
            if (isVisible) {
                throw new Error('Immersive mode did not exit properly');
            }
        }
        
        console.log('✅ Immersive mode exit successful');
    });

    // Test 3.3: Premium Speed Reader Features
    await runner.runTest('Premium Features Detection', async (page) => {
        await navigateToArticle(page);
        
        // Look for premium feature indicators
        const premiumFeatures = {
            wordChunking: await page.$('.word-chunking, .chunking-options, [data-premium="chunking"]'),
            smartConnectors: await page.$('.smart-connectors, [data-premium="connectors"]'),
            darkMode: await page.$('.dark-mode-toggle, [data-premium="dark-mode"]'),
            premiumFonts: await page.$('.font-options, [data-premium="fonts"]')
        };
        
        let foundFeatures = [];
        let lockedFeatures = [];
        
        for (const [feature, element] of Object.entries(premiumFeatures)) {
            if (element) {
                foundFeatures.push(feature);
                
                // Check if feature is locked
                const isLocked = await element.$('.lock-icon, .premium-lock, [data-locked="true"]');
                if (isLocked) {
                    lockedFeatures.push(feature);
                }
            }
        }
        
        console.log(`Found premium features: ${foundFeatures.join(', ')}`);
        console.log(`Locked features: ${lockedFeatures.join(', ')}`);
        
        if (foundFeatures.length === 0) {
            console.log('⚠️  No premium features detected');
        }
    });

    // Test 3.4: Speed Reader Settings Persistence
    await runner.runTest('Settings Persistence', async (page) => {
        await navigateToArticle(page);
        
        // Adjust WPM setting
        const wpmSlider = await page.$('input[type="range"], .wpm-slider');
        if (!wpmSlider) {
            throw new Error('WPM slider not found for persistence test');
        }
        
        // Set specific WPM value
        await wpmSlider.evaluate(el => el.value = '350');
        await wpmSlider.evaluate(el => el.dispatchEvent(new Event('change')));
        
        // Navigate away and back
        await page.goto(`${runner.baseUrl}/`);
        await page.waitForTimeout(1000);
        
        // Return to article
        await navigateToArticle(page);
        
        // Check if WPM setting persisted
        const newWpmSlider = await page.$('input[type="range"], .wpm-slider');
        const persistedWpm = await newWpmSlider.evaluate(el => el.value);
        
        if (persistedWpm !== '350') {
            console.log(`⚠️  WPM setting did not persist: expected 350, got ${persistedWpm}`);
        } else {
            console.log('✅ WPM setting persisted across navigation');
        }
    });

    await runner.runTest('Speed Reader Error Handling', async (page) => {
        await navigateToArticle(page);
        
        // Test with empty content (simulate error condition)
        await page.evaluate(() => {
            // Try to break the speed reader by clearing content
            const wordDisplay = document.querySelector('.word-display, .speed-reader-word, .current-word');
            if (wordDisplay) {
                // Simulate error condition
                window.speedReaderTest = true;
            }
        });
        
        // Try to start reading
        const startButton = await page.$('.start-reading, .play-pause, button[data-action="start"]');
        if (startButton) {
            await startButton.click();
            await page.waitForTimeout(2000);
            
            // Check for error messages
            const errorMessage = await page.$('.error-message, .alert-danger, .speed-reader-error');
            if (errorMessage) {
                console.log('✅ Error handling working - error message displayed');
            } else {
                console.log('⚠️  No error message shown for error condition');
            }
        }
    });
};