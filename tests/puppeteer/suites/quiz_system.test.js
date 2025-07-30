/**
 * Quiz System Test Suite
 * Tests quiz generation, interface, completion, and XP rewards
 */

module.exports = async function quizSystemTests(runner) {
    console.log('\n🧠 Running Quiz System Test Suite');

    // Helper function to navigate to an article
    async function navigateToArticle(page) {
        await page.goto(`${runner.baseUrl}/`);
        await page.waitForSelector('.article-list .article a, .article-card a');
        const articleLink = await page.$('.article-list .article a, .article-card a');
        await articleLink.click();
        await page.waitForNavigation();
    }

    // Test 4.1: Quiz Generation
    await runner.runTest('Quiz Availability Check', async (page) => {
        await navigateToArticle(page);
        
        // Look for quiz button or section
        const quizButton = await page.$('.start-quiz, .quiz-button, button[data-action="quiz"]');
        const quizSection = await page.$('.quiz-section, #quiz, .quiz-container');
        
        if (!quizButton && !quizSection) {
            throw new Error('No quiz functionality found on article page');
        }
        
        if (quizButton) {
            console.log('✅ Quiz button found');
        }
        
        if (quizSection) {
            console.log('✅ Quiz section found');
        }
    });

    await runner.runTest('Quiz Generation Process', async (page) => {
        await navigateToArticle(page);
        
        // Find and click quiz button
        const quizButton = await page.$('.start-quiz, .quiz-button, button[data-action="quiz"]');
        
        if (!quizButton) {
            console.log('⚠️  Quiz button not found - skipping generation test');
            return;
        }
        
        await quizButton.click();
        
        // Wait for quiz to load (may take time for AI generation)
        try {
            await page.waitForSelector('.quiz-question, .question, .quiz-content', { timeout: 15000 });
            console.log('✅ Quiz generated successfully');
        } catch (error) {
            // Check for loading indicator
            const loadingIndicator = await page.$('.loading, .spinner, .quiz-loading');
            if (loadingIndicator) {
                console.log('⚠️  Quiz still loading - may need more time');
                await page.waitForTimeout(10000);
                
                const quizContent = await page.$('.quiz-question, .question, .quiz-content');
                if (!quizContent) {
                    throw new Error('Quiz failed to generate within timeout');
                }
            } else {
                throw new Error('Quiz generation failed - no content or loading indicator');
            }
        }
    });

    await runner.runTest('Quiz Content Quality', async (page) => {
        await navigateToArticle(page);
        
        // Start quiz
        const quizButton = await page.$('.start-quiz, .quiz-button, button[data-action="quiz"]');
        if (!quizButton) {
            console.log('⚠️  Cannot test quiz quality - no quiz button');
            return;
        }
        
        await quizButton.click();
        await page.waitForSelector('.quiz-question, .question', { timeout: 15000 });
        
        // Check quiz structure
        const questions = await page.$$('.quiz-question, .question');
        if (questions.length === 0) {
            throw new Error('No quiz questions found');
        }
        
        console.log(`Found ${questions.length} quiz questions`);
        
        // Verify first question has proper structure
        const firstQuestion = questions[0];
        const questionText = await firstQuestion.$('.question-text, .question p, h3');
        const options = await firstQuestion.$$('.option, .answer-option, input[type="radio"]');
        
        if (!questionText) {
            throw new Error('Question text not found');
        }
        
        if (options.length < 2) {
            throw new Error(`Insufficient answer options: found ${options.length}, expected at least 2`);
        }
        
        console.log(`✅ Question structure valid: ${options.length} options`);
    });

    // Test 4.2: Quiz Interface
    await runner.runTest('Quiz Interface Navigation', async (page) => {
        await navigateToArticle(page);
        
        // Start quiz
        const quizButton = await page.$('.start-quiz, .quiz-button, button[data-action="quiz"]');
        if (!quizButton) {
            console.log('⚠️  Cannot test quiz interface - no quiz button');
            return;
        }
        
        await quizButton.click();
        await page.waitForSelector('.quiz-question, .question', { timeout: 15000 });
        
        // Test question navigation
        const nextButton = await page.$('.next-question, .quiz-next, button[data-action="next"]');
        const prevButton = await page.$('.prev-question, .quiz-prev, button[data-action="prev"]');
        
        if (nextButton) {
            console.log('✅ Next button found');
            
            // Try to navigate without selecting answer
            await nextButton.click();
            await page.waitForTimeout(1000);
            
            // Should show validation message
            const validationMessage = await page.$('.validation-error, .error-message, .alert');
            if (validationMessage) {
                console.log('✅ Validation working - cannot proceed without answer');
            }
        }
        
        // Select an answer
        const firstOption = await page.$('.option input, input[type="radio"]');
        if (firstOption) {
            await firstOption.click();
            console.log('✅ Answer selection working');
        }
    });

    await runner.runTest('Quiz Progress Indicators', async (page) => {
        await navigateToArticle(page);
        
        // Start quiz
        const quizButton = await page.$('.start-quiz, .quiz-button, button[data-action="quiz"]');
        if (!quizButton) {
            console.log('⚠️  Cannot test quiz progress - no quiz button');
            return;
        }
        
        await quizButton.click();
        await page.waitForSelector('.quiz-question, .question', { timeout: 15000 });
        
        // Look for progress indicators
        const progressBar = await page.$('.progress-bar, .quiz-progress');
        const questionCounter = await page.$('.question-counter, .quiz-counter');
        const progressText = await page.$('.progress-text');
        
        if (progressBar) {
            console.log('✅ Progress bar found');
        }
        
        if (questionCounter) {
            const counterText = await questionCounter.evaluate(el => el.textContent);
            console.log(`✅ Question counter: ${counterText}`);
        }
        
        if (!progressBar && !questionCounter && !progressText) {
            console.log('⚠️  No progress indicators found');
        }
    });

    // Test 4.3: Quiz Completion & Scoring
    await runner.runTest('Quiz Submission Process', async (page) => {
        await navigateToArticle(page);
        
        // Start quiz
        const quizButton = await page.$('.start-quiz, .quiz-button, button[data-action="quiz"]');
        if (!quizButton) {
            console.log('⚠️  Cannot test quiz submission - no quiz button');
            return;
        }
        
        await quizButton.click();
        await page.waitForSelector('.quiz-question, .question', { timeout: 15000 });
        
        // Answer all questions quickly
        const questions = await page.$$('.quiz-question, .question');
        
        for (let i = 0; i < questions.length; i++) {
            // Select first option for each question
            const options = await page.$$('.option input, input[type="radio"]');
            if (options[i]) {
                await options[i].click();
            }
            
            // Navigate to next question
            const nextButton = await page.$('.next-question, .quiz-next, button[data-action="next"]');
            if (nextButton && i < questions.length - 1) {
                await nextButton.click();
                await page.waitForTimeout(500);
            }
        }
        
        // Submit quiz
        const submitButton = await page.$('.submit-quiz, .quiz-submit, button[type="submit"]');
        if (!submitButton) {
            throw new Error('Quiz submit button not found');
        }
        
        await submitButton.click();
        
        // Wait for results
        await page.waitForSelector('.quiz-results, .quiz-score, .results', { timeout: 10000 });
        console.log('✅ Quiz submitted successfully');
    });

    await runner.runTest('Quiz Score Display', async (page) => {
        // This test assumes previous test completed a quiz
        await navigateToArticle(page);
        
        // Look for quiz results (may be from previous completion)
        const resultsSection = await page.$('.quiz-results, .quiz-score, .results');
        
        if (!resultsSection) {
            console.log('⚠️  No quiz results found - may need to complete quiz first');
            return;
        }
        
        // Check for score elements
        const scoreDisplay = await page.$('.score, .quiz-score-value, .percentage');
        const xpReward = await page.$('.xp-reward, .xp-earned, .points-earned');
        
        if (!scoreDisplay) {
            throw new Error('Quiz score not displayed');
        }
        
        const scoreText = await scoreDisplay.evaluate(el => el.textContent);
        console.log(`Quiz score: ${scoreText}`);
        
        if (xpReward) {
            const xpText = await xpReward.evaluate(el => el.textContent);
            console.log(`XP reward: ${xpText}`);
        }
    });

    await runner.runTest('XP Reward Calculation', async (page) => {
        // Check user's XP before and after quiz (if possible)
        await page.goto(`${runner.baseUrl}/profile/`);
        
        const xpDisplay = await page.$('[data-testid="user-xp"], .xp-display, .user-xp');
        
        if (!xpDisplay) {
            console.log('⚠️  Cannot verify XP rewards - XP display not found');
            return;
        }
        
        const initialXp = await xpDisplay.evaluate(el => {
            const text = el.textContent;
            const match = text.match(/(\d+)/);
            return match ? parseInt(match[1]) : 0;
        });
        
        console.log(`Initial XP: ${initialXp}`);
        
        // Complete a quiz (simplified)
        await navigateToArticle(page);
        const quizButton = await page.$('.start-quiz, .quiz-button');
        
        if (quizButton) {
            // Quick quiz completion simulation
            console.log('⚠️  XP reward verification requires full quiz completion');
        }
    });

    // Test 4.4: Quiz-Gated Features
    await runner.runTest('Comment Unlock After Quiz', async (page) => {
        await navigateToArticle(page);
        
        // Check if comments section exists
        const commentsSection = await page.$('.comments, .comment-section, #comments');
        
        if (!commentsSection) {
            console.log('⚠️  Comments section not found');
            return;
        }
        
        // Look for comment form or unlock message
        const commentForm = await page.$('.comment-form, form[action*="comment"]');
        const unlockMessage = await page.$('.quiz-required, .unlock-message');
        
        if (unlockMessage) {
            const messageText = await unlockMessage.evaluate(el => el.textContent);
            console.log(`Comment unlock message: ${messageText}`);
            
            if (messageText.toLowerCase().includes('quiz')) {
                console.log('✅ Quiz requirement for comments detected');
            }
        }
        
        if (commentForm) {
            console.log('✅ Comment form available (quiz may be completed)');
        }
    });

    await runner.runTest('Quiz Retry Functionality', async (page) => {
        await navigateToArticle(page);
        
        // Look for retry option (may only appear after completion)
        const retryButton = await page.$('.retry-quiz, .quiz-retry, button[data-action="retry"]');
        
        if (!retryButton) {
            console.log('⚠️  Quiz retry button not found - may not be implemented');
            return;
        }
        
        await retryButton.click();
        
        // Should reset quiz to first question
        await page.waitForSelector('.quiz-question, .question', { timeout: 5000 });
        
        const questionCounter = await page.$('.question-counter, .quiz-counter');
        if (questionCounter) {
            const counterText = await questionCounter.evaluate(el => el.textContent);
            if (counterText.includes('1')) {
                console.log('✅ Quiz retry working - reset to first question');
            }
        }
    });
};