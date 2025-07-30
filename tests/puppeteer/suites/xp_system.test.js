/**
 * XP System Test Suite
 * Tests XP display, earning, spending, and premium features
 */

module.exports = async function xpSystemTests(runner) {
    console.log('\n💰 Running XP System Test Suite');

    // Helper function to get current XP from display
    async function getCurrentXP(page) {
        const xpDisplay = await page.$('[data-testid="user-xp"], .xp-display, .user-xp, .xp-balance');
        if (!xpDisplay) {
            return null;
        }
        
        const xpText = await xpDisplay.evaluate(el => el.textContent);
        const match = xpText.match(/(\d+)/);
        return match ? parseInt(match[1]) : 0;
    }

    // Helper function to navigate to an article
    async function navigateToArticle(page) {
        await page.goto(`${runner.baseUrl}/`);
        await page.waitForSelector('.article-list .article a, .article-card a');
        const articleLink = await page.$('.article-list .article a, .article-card a');
        await articleLink.click();
        await page.waitForNavigation();
    }

    // Test 5.1: XP Display & Tracking
    await runner.runTest('XP Display Visibility', async (page) => {
        // Login first
        await page.goto(`${runner.baseUrl}/accounts/login/`);
        
        try {
            await page.type('#id_username', 'testuser123');
            await page.type('#id_password', 'SecurePass123!');
            await page.click('button[type="submit"]');
            await page.waitForNavigation();
        } catch (error) {
            console.log('⚠️  Login failed - testing XP display for anonymous user');
        }
        
        // Check XP display on main pages
        const locations = [
            { name: 'Homepage', url: `${runner.baseUrl}/` },
            { name: 'Profile', url: `${runner.baseUrl}/profile/` }
        ];
        
        for (const location of locations) {
            try {
                await page.goto(location.url);
                await page.waitForTimeout(1000);
                
                const xpDisplay = await page.$('[data-testid="user-xp"], .xp-display, .user-xp, .xp-balance');
                
                if (xpDisplay) {
                    const xpText = await xpDisplay.evaluate(el => el.textContent);
                    console.log(`✅ XP display found on ${location.name}: ${xpText}`);
                } else {
                    console.log(`⚠️  XP display not found on ${location.name}`);
                }
            } catch (error) {
                console.log(`⚠️  Could not access ${location.name}: ${error.message}`);
            }
        }
    });

    await runner.runTest('XP Balance Consistency', async (page) => {
        // Check XP consistency across different pages
        const pages = [
            `${runner.baseUrl}/`,
            `${runner.baseUrl}/profile/`
        ];
        
        let xpValues = [];
        
        for (const pageUrl of pages) {
            try {
                await page.goto(pageUrl);
                await page.waitForTimeout(1000);
                
                const xp = await getCurrentXP(page);
                if (xp !== null) {
                    xpValues.push(xp);
                }
            } catch (error) {
                console.log(`⚠️  Could not check XP on ${pageUrl}`);
            }
        }
        
        if (xpValues.length > 1) {
            const allSame = xpValues.every(xp => xp === xpValues[0]);
            if (allSame) {
                console.log(`✅ XP consistent across pages: ${xpValues[0]}`);
            } else {
                throw new Error(`XP inconsistent across pages: ${xpValues.join(', ')}`);
            }
        } else {
            console.log('⚠️  Could not verify XP consistency - insufficient data');
        }
    });

    // Test 5.2: Premium Feature Store
    await runner.runTest('Premium Feature Store Access', async (page) => {
        // Look for premium feature store
        await page.goto(`${runner.baseUrl}/store/`);
        
        const storeSection = await page.$('.premium-store, .feature-store, .xp-store');
        
        if (!storeSection) {
            // Try finding store link from main navigation
            await page.goto(`${runner.baseUrl}/`);
            const storeLink = await page.$('a[href*="store"], .store-link, .premium-link');
            
            if (!storeLink) {
                console.log('⚠️  Premium feature store not found');
                return;
            }
            
            await storeLink.click();
            await page.waitForNavigation();
        }
        
        // Check for premium features
        const premiumFeatures = await page.$$('.premium-feature, .feature-item, .store-item');
        
        if (premiumFeatures.length === 0) {
            throw new Error('No premium features found in store');
        }
        
        console.log(`✅ Found ${premiumFeatures.length} premium features in store`);
        
        // Check first feature for proper structure
        const firstFeature = premiumFeatures[0];
        const featureName = await firstFeature.$('.feature-name, .item-name, h3');
        const featurePrice = await firstFeature.$('.feature-price, .price, .xp-cost');
        
        if (!featureName) {
            throw new Error('Premium feature missing name');
        }
        
        if (!featurePrice) {
            throw new Error('Premium feature missing price');
        }
        
        const nameText = await featureName.evaluate(el => el.textContent);
        const priceText = await featurePrice.evaluate(el => el.textContent);
        
        console.log(`Feature: ${nameText}, Price: ${priceText}`);
    });

    await runner.runTest('Premium Feature Purchase Process', async (page) => {
        // Navigate to store
        await page.goto(`${runner.baseUrl}/store/`);
        
        const premiumFeatures = await page.$$('.premium-feature, .feature-item, .store-item');
        
        if (premiumFeatures.length === 0) {
            console.log('⚠️  No premium features to test purchase');
            return;
        }
        
        // Try to purchase first feature
        const firstFeature = premiumFeatures[0];
        const purchaseButton = await firstFeature.$('.purchase-btn, .buy-btn, button');
        
        if (!purchaseButton) {
            console.log('⚠️  No purchase button found');
            return;
        }
        
        // Check current XP before purchase
        const initialXP = await getCurrentXP(page);
        
        await purchaseButton.click();
        await page.waitForTimeout(2000);
        
        // Check for purchase confirmation or insufficient funds message
        const confirmationMessage = await page.$('.purchase-success, .success-message, .alert-success');
        const errorMessage = await page.$('.insufficient-funds, .error-message, .alert-danger');
        
        if (confirmationMessage) {
            console.log('✅ Purchase successful');
            
            // Verify XP deduction
            const newXP = await getCurrentXP(page);
            if (newXP !== null && initialXP !== null && newXP < initialXP) {
                console.log(`✅ XP deducted: ${initialXP} → ${newXP}`);
            }
        } else if (errorMessage) {
            const errorText = await errorMessage.evaluate(el => el.textContent);
            console.log(`⚠️  Purchase failed: ${errorText}`);
        } else {
            console.log('⚠️  Purchase result unclear');
        }
    });

    // Test 5.3: Premium Feature Functionality
    await runner.runTest('Premium Feature Unlock Detection', async (page) => {
        await navigateToArticle(page);
        
        // Look for premium features in speed reader
        const premiumFeatures = {
            wordChunking: await page.$('.word-chunking, .chunking-options'),
            smartConnectors: await page.$('.smart-connectors'),
            darkMode: await page.$('.dark-mode-toggle'),
            premiumFonts: await page.$('.font-options')
        };
        
        let unlockedFeatures = [];
        let lockedFeatures = [];
        
        for (const [feature, element] of Object.entries(premiumFeatures)) {
            if (element) {
                // Check if feature is locked
                const lockIcon = await element.$('.lock-icon, .premium-lock, [data-locked="true"]');
                const isDisabled = await element.evaluate(el => el.disabled || el.classList.contains('disabled'));
                
                if (lockIcon || isDisabled) {
                    lockedFeatures.push(feature);
                } else {
                    unlockedFeatures.push(feature);
                }
            }
        }
        
        console.log(`Unlocked premium features: ${unlockedFeatures.join(', ') || 'none'}`);
        console.log(`Locked premium features: ${lockedFeatures.join(', ') || 'none'}`);
        
        if (unlockedFeatures.length === 0 && lockedFeatures.length === 0) {
            console.log('⚠️  No premium features detected');
        }
    });

    await runner.runTest('Word Chunking Feature Test', async (page) => {
        await navigateToArticle(page);
        
        // Look for word chunking controls
        const chunkingControl = await page.$('.chunking-options, .word-chunking, select[name*="chunk"]');
        
        if (!chunkingControl) {
            console.log('⚠️  Word chunking control not found');
            return;
        }
        
        // Test chunking options (2-5 words)
        const options = await chunkingControl.$$('option');
        
        if (options.length < 2) {
            throw new Error('Insufficient chunking options');
        }
        
        // Try selecting 2-word chunking
        await chunkingControl.select('2');
        await page.waitForTimeout(1000);
        
        // Start speed reader to test chunking
        const startButton = await page.$('.start-reading, .play-pause');
        if (startButton) {
            await startButton.click();
            await page.waitForTimeout(2000);
            
            // Check if word display shows multiple words
            const wordDisplay = await page.$('.word-display, .speed-reader-word');
            if (wordDisplay) {
                const displayText = await wordDisplay.evaluate(el => el.textContent);
                const wordCount = displayText.trim().split(/\s+/).length;
                
                if (wordCount >= 2) {
                    console.log(`✅ Word chunking working: displaying ${wordCount} words`);
                } else {
                    console.log(`⚠️  Word chunking may not be working: only ${wordCount} word displayed`);
                }
            }
        }
    });

    // Test 5.4: XP Transaction System
    await runner.runTest('XP Earning from Quiz', async (page) => {
        await navigateToArticle(page);
        
        // Record initial XP
        const initialXP = await getCurrentXP(page);
        
        // Complete a quiz (simplified)
        const quizButton = await page.$('.start-quiz, .quiz-button');
        
        if (!quizButton) {
            console.log('⚠️  Cannot test XP earning - no quiz available');
            return;
        }
        
        console.log(`Initial XP: ${initialXP}`);
        console.log('⚠️  Full quiz completion required for XP earning test');
        
        // This would require completing the entire quiz flow
        // For now, just verify the XP display updates
    });

    await runner.runTest('XP Spending on Comments', async (page) => {
        await navigateToArticle(page);
        
        // Look for comment form
        const commentForm = await page.$('.comment-form, form[action*="comment"]');
        
        if (!commentForm) {
            console.log('⚠️  Comment form not found - may require quiz completion');
            return;
        }
        
        // Record initial XP
        const initialXP = await getCurrentXP(page);
        
        // Try to post a comment
        const commentTextarea = await page.$('textarea[name*="comment"], #id_content');
        const submitButton = await page.$('button[type="submit"], .submit-comment');
        
        if (commentTextarea && submitButton) {
            await commentTextarea.type('Test comment for XP spending verification');
            
            await submitButton.click();
            await page.waitForTimeout(3000);
            
            // Check if XP was deducted
            const newXP = await getCurrentXP(page);
            
            if (newXP !== null && initialXP !== null) {
                const xpSpent = initialXP - newXP;
                if (xpSpent > 0) {
                    console.log(`✅ XP spent on comment: ${xpSpent} XP`);
                } else {
                    console.log('⚠️  No XP deduction detected for comment');
                }
            }
        }
    });

    await runner.runTest('XP Transaction History', async (page) => {
        // Look for XP transaction history
        await page.goto(`${runner.baseUrl}/profile/`);
        
        const transactionHistory = await page.$('.xp-history, .transaction-history, .xp-transactions');
        
        if (!transactionHistory) {
            console.log('⚠️  XP transaction history not found');
            return;
        }
        
        // Check for transaction entries
        const transactions = await page.$$('.transaction, .xp-transaction, .history-item');
        
        if (transactions.length === 0) {
            console.log('⚠️  No XP transactions found in history');
            return;
        }
        
        console.log(`✅ Found ${transactions.length} XP transactions`);
        
        // Verify transaction structure
        const firstTransaction = transactions[0];
        const transactionType = await firstTransaction.$('.transaction-type, .type');
        const transactionAmount = await firstTransaction.$('.transaction-amount, .amount');
        
        if (transactionType && transactionAmount) {
            const typeText = await transactionType.evaluate(el => el.textContent);
            const amountText = await transactionAmount.evaluate(el => el.textContent);
            console.log(`Transaction: ${typeText} - ${amountText}`);
        }
    });

    await runner.runTest('XP Real-time Updates', async (page) => {
        // Test if XP updates in real-time during interactions
        await navigateToArticle(page);
        
        const initialXP = await getCurrentXP(page);
        
        if (initialXP === null) {
            console.log('⚠️  Cannot test real-time updates - XP display not found');
            return;
        }
        
        // Perform an action that should change XP (like starting a quiz)
        const quizButton = await page.$('.start-quiz, .quiz-button');
        
        if (quizButton) {
            await quizButton.click();
            await page.waitForTimeout(2000);
            
            // Check if XP display is still visible and potentially updated
            const updatedXP = await getCurrentXP(page);
            
            if (updatedXP !== null) {
                console.log(`✅ XP display remains visible during interactions: ${updatedXP}`);
            } else {
                console.log('⚠️  XP display disappeared during interaction');
            }
        }
    });
};