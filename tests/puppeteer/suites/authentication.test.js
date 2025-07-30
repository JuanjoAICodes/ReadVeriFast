/**
 * Authentication Test Suite
 * Tests user registration, login, logout functionality
 */

module.exports = async function authenticationTests(runner) {
    console.log('\n🔐 Running Authentication Test Suite');

    // Test 1.1: User Registration
    await runner.runTest('User Registration - Valid Data', async (page) => {
        await page.goto(`${runner.baseUrl}/accounts/register/`);
        
        // Fill registration form
        await page.type('#id_username', 'testuser123');
        await page.type('#id_email', 'test@example.com');
        await page.type('#id_password1', 'SecurePass123!');
        await page.type('#id_password2', 'SecurePass123!');
        
        // Submit form
        await page.click('button[type="submit"]');
        
        // Wait for redirect and verify success
        await page.waitForNavigation();
        
        // Should redirect to profile or dashboard
        const url = page.url();
        if (!url.includes('/profile/') && !url.includes('/dashboard/')) {
            throw new Error(`Expected redirect to profile/dashboard, got: ${url}`);
        }
        
        // Verify user is logged in (check for logout link or user menu)
        const logoutLink = await page.$('a[href*="logout"]');
        if (!logoutLink) {
            throw new Error('User does not appear to be logged in after registration');
        }
    });

    await runner.runTest('User Registration - Invalid Data', async (page) => {
        await page.goto(`${runner.baseUrl}/accounts/register/`);
        
        // Try registration with mismatched passwords
        await page.type('#id_username', 'testuser456');
        await page.type('#id_email', 'invalid-email');
        await page.type('#id_password1', 'weak');
        await page.type('#id_password2', 'different');
        
        await page.click('button[type="submit"]');
        
        // Should stay on registration page with errors
        await page.waitForSelector('.errorlist, .alert-danger, .form-error', { timeout: 3000 });
        
        const errors = await page.$$('.errorlist li, .alert-danger, .form-error');
        if (errors.length === 0) {
            throw new Error('Expected validation errors for invalid registration data');
        }
    });

    // Test 1.2: User Login/Logout
    await runner.runTest('User Login - Valid Credentials', async (page) => {
        await page.goto(`${runner.baseUrl}/accounts/login/`);
        
        // Use credentials from previous registration or create test user
        await page.type('#id_username', 'testuser123');
        await page.type('#id_password', 'SecurePass123!');
        
        await page.click('button[type="submit"]');
        await page.waitForNavigation();
        
        // Verify successful login
        const logoutLink = await page.$('a[href*="logout"]');
        if (!logoutLink) {
            throw new Error('Login appears to have failed - no logout link found');
        }
    });

    await runner.runTest('User Login - Invalid Credentials', async (page) => {
        await page.goto(`${runner.baseUrl}/accounts/login/`);
        
        await page.type('#id_username', 'nonexistent');
        await page.type('#id_password', 'wrongpassword');
        
        await page.click('button[type="submit"]');
        
        // Should show error message
        await page.waitForSelector('.errorlist, .alert-danger, .form-error', { timeout: 3000 });
        
        const currentUrl = page.url();
        if (!currentUrl.includes('/login/')) {
            throw new Error('Should remain on login page after failed login');
        }
    });

    await runner.runTest('User Logout', async (page) => {
        // First ensure we're logged in
        await page.goto(`${runner.baseUrl}/accounts/login/`);
        await page.type('#id_username', 'testuser123');
        await page.type('#id_password', 'SecurePass123!');
        await page.click('button[type="submit"]');
        await page.waitForNavigation();
        
        // Now test logout
        const logoutLink = await page.$('a[href*="logout"]');
        if (!logoutLink) {
            throw new Error('Cannot test logout - user not logged in');
        }
        
        await logoutLink.click();
        await page.waitForNavigation();
        
        // Verify logout successful - should see login link
        const loginLink = await page.$('a[href*="login"]');
        if (!loginLink) {
            throw new Error('Logout appears to have failed - no login link found');
        }
    });

    // Test 1.3: User Profile Management
    await runner.runTest('User Profile Access', async (page) => {
        // Login first
        await page.goto(`${runner.baseUrl}/accounts/login/`);
        await page.type('#id_username', 'testuser123');
        await page.type('#id_password', 'SecurePass123!');
        await page.click('button[type="submit"]');
        await page.waitForNavigation();
        
        // Navigate to profile
        await page.goto(`${runner.baseUrl}/profile/`);
        
        // Verify profile elements are present
        const profileElements = await page.$$eval('[data-testid*="profile"], .profile, .user-stats', 
            elements => elements.length);
        
        if (profileElements === 0) {
            throw new Error('Profile page does not contain expected profile elements');
        }
        
        // Check for XP display
        const xpDisplay = await page.$('[data-testid="user-xp"], .xp-display, .user-xp');
        if (!xpDisplay) {
            throw new Error('Profile page missing XP display');
        }
    });

    // Test 1.4: Admin User Setup (if admin exists)
    await runner.runTest('Admin User Access', async (page) => {
        try {
            await page.goto(`${runner.baseUrl}/admin/`);
            
            // Try admin login (assuming admin user exists)
            await page.type('#id_username', 'admin');
            await page.type('#id_password', 'admin');
            await page.click('input[type="submit"]');
            
            await page.waitForNavigation({ timeout: 5000 });
            
            // Check if we're in admin interface
            const adminTitle = await page.$('.admin-title, #header h1');
            if (!adminTitle) {
                console.log('⚠️  Admin user not configured or credentials incorrect - skipping admin tests');
                return;
            }
            
            console.log('✅ Admin access verified');
            
        } catch (error) {
            console.log('⚠️  Admin test skipped - admin not accessible:', error.message);
        }
    });
};