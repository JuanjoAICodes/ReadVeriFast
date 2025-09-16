/**
 * Article Reading Test Suite
 * Tests article listing, detail view, and content display
 */

module.exports = async function articleReadingTests(runner) {
    console.log('\n📚 Running Article Reading Test Suite');

    // Test 2.1: Article List View
    await runner.runTest('Article List Display', async (page) => {
        await page.goto(`${runner.baseUrl}/`);
        
        // Wait for articles to load
        await page.waitForSelector('.article-list, .article-card, article', { timeout: 10000 });
        
        // Check for article elements
        const articles = await page.$$('.article-list .article, .article-card, article');
        if (articles.length === 0) {
            throw new Error('No articles found on homepage');
        }
        
        console.log(`Found ${articles.length} articles on homepage`);
        
        // Verify article metadata is displayed
        const firstArticle = articles[0];
        const title = await firstArticle.$('.article-title, h2, h3');
        const metadata = await firstArticle.$('.article-meta, .metadata, .article-info');
        
        if (!title) {
            throw new Error('Article title not found');
        }
        
        if (!metadata) {
            console.log('⚠️  Article metadata not clearly visible');
        }
    });

    await runner.runTest('Article List Pagination', async (page) => {
        await page.goto(`${runner.baseUrl}/`);
        
        // Look for pagination controls
        const pagination = await page.$('.pagination, .page-navigation, .pager');
        
        if (!pagination) {
            console.log('⚠️  No pagination found - may not be needed if few articles');
            return;
        }
        
        // Test pagination functionality
        const nextButton = await page.$('.pagination .next, .page-next');
        if (nextButton) {
            await nextButton.click();
            await page.waitForNavigation();
            
            // Verify we're on page 2
            const currentPage = await page.$('.pagination .current, .active');
            if (!currentPage) {
                throw new Error('Pagination navigation failed');
            }
        }
    });

    // Test 2.2: Article Detail View
    await runner.runTest('Article Detail View Access', async (page) => {
        await page.goto(`${runner.baseUrl}/`);
        
        // Find and click first article
        await page.waitForSelector('.article-list .article a, .article-card a, article a');
        const articleLink = await page.$('.article-list .article a, .article-card a, article a');
        
        if (!articleLink) {
            throw new Error('No article links found');
        }
        
        await articleLink.click();
        await page.waitForNavigation();
        
        // Verify we're on article detail page
        const articleContent = await page.$('.article-content, .content, main article');
        if (!articleContent) {
            throw new Error('Article detail page does not contain article content');
        }
        
        // Check for essential elements
        const title = await page.$('h1, .article-title');
        const content = await page.$('.article-content, .content p');
        
        if (!title) {
            throw new Error('Article title missing on detail page');
        }
        
        if (!content) {
            throw new Error('Article content missing on detail page');
        }
    });

    await runner.runTest('Article Metadata Display', async (page) => {
        // Navigate to first article
        await page.goto(`${runner.baseUrl}/`);
        await page.waitForSelector('.article-list .article a, .article-card a');
        const articleLink = await page.$('.article-list .article a, .article-card a');
        await articleLink.click();
        await page.waitForNavigation();
        
        // Check for metadata elements
        const metadata = {
            wordCount: await page.$('[data-testid="word-count"], .word-count'),
            readingLevel: await page.$('[data-testid="reading-level"], .reading-level'),
            tags: await page.$('[data-testid="tags"], .tags, .article-tags'),
            timestamp: await page.$('[data-testid="timestamp"], .timestamp, .date')
        };
        
        let missingElements = [];
        Object.entries(metadata).forEach(([key, element]) => {
            if (!element) {
                missingElements.push(key);
            }
        });
        
        if (missingElements.length > 0) {
            console.log(`⚠️  Missing metadata elements: ${missingElements.join(', ')}`);
        }
        
        // At least some metadata should be present
        const hasAnyMetadata = Object.values(metadata).some(el => el !== null);
        if (!hasAnyMetadata) {
            throw new Error('No article metadata found on detail page');
        }
    });

    await runner.runTest('Article Tags Display', async (page) => {
        // Navigate to article detail
        await page.goto(`${runner.baseUrl}/`);
        await page.waitForSelector('.article-list .article a, .article-card a');
        const articleLink = await page.$('.article-list .article a, .article-card a');
        await articleLink.click();
        await page.waitForNavigation();
        
        // Look for tags
        const tagsContainer = await page.$('.tags, .article-tags, [data-testid="tags"]');
        
        if (!tagsContainer) {
            console.log('⚠️  No tags container found');
            return;
        }
        
        const tags = await page.$$('.tag, .article-tag, .badge');
        console.log(`Found ${tags.length} tags on article`);
        
        // Verify tags are clickable/interactive
        if (tags.length > 0) {
            const firstTag = tags[0];
            const tagText = await firstTag.evaluate(el => el.textContent);
            console.log(`First tag: "${tagText}"`);
            
            // Test tag click (should navigate to tag page or filter)
            try {
                await firstTag.click();
                await page.waitForNavigation({ timeout: 3000 });
                console.log('✅ Tag navigation working');
            } catch (error) {
                console.log('⚠️  Tag click did not navigate (may be expected)');
            }
        }
    });

    // Test 2.3: Article Submission/Scraping
    await runner.runTest('Article Submission Form', async (page) => {
        // Look for article submission form
        await page.goto(`${runner.baseUrl}/submit/`);
        
        const submitForm = await page.$('form[action*="submit"], .submit-form, #article-submit-form');
        
        if (!submitForm) {
            console.log('⚠️  Article submission form not found at /submit/');
            
            // Try to find submission link elsewhere
            await page.goto(`${runner.baseUrl}/`);
            const submitLink = await page.$('a[href*="submit"], .submit-article');
            
            if (!submitLink) {
                console.log('⚠️  No article submission functionality found - skipping test');
                return;
            }
            
            await submitLink.click();
            await page.waitForNavigation();
        }
        
        // Test form elements
        const urlInput = await page.$('input[name*="url"], #id_url, input[type="url"]');
        if (!urlInput) {
            throw new Error('URL input field not found in submission form');
        }
        
        // Test form submission with invalid URL
        await page.type('input[name*="url"], #id_url, input[type="url"]', 'not-a-valid-url');
        
        const submitButton = await page.$('button[type="submit"], input[type="submit"]');
        if (submitButton) {
            await submitButton.click();
            
            // Should show validation error
            await page.waitForSelector('.error, .alert-danger, .form-error', { timeout: 3000 });
        }
    });

    await runner.runTest('Responsive Design Check', async (page) => {
        // Test mobile viewport
        await page.setViewport({ width: 375, height: 667 }); // iPhone SE
        
        await page.goto(`${runner.baseUrl}/`);
        await page.waitForSelector('.article-list, .article-card');
        
        // Check if layout adapts to mobile
        const articles = await page.$$('.article-list .article, .article-card');
        if (articles.length === 0) {
            throw new Error('Articles not visible on mobile viewport');
        }
        
        // Navigate to article detail on mobile
        const articleLink = await page.$('.article-list .article a, .article-card a');
        await articleLink.click();
        await page.waitForNavigation();
        
        // Verify content is readable on mobile
        const content = await page.$('.article-content, .content');
        if (!content) {
            throw new Error('Article content not accessible on mobile');
        }
        
        // Reset viewport
        await page.setViewport({ width: 1280, height: 720 });
    });
};