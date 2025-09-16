# Puppeteer MCP Server - Usage Guide & Troubleshooting

*Created: July 17, 2025 | Updated: July 17, 2025*

## 🎯 **Purpose**
This document serves as a reference to avoid repeating common mistakes when using the Puppeteer MCP server for browser automation and testing.

## 🚨 **CRITICAL SETUP REQUIREMENTS**

### **1. Package Installation**
The Puppeteer MCP server must be installed globally:
```bash
npm install -g @modelcontextprotocol/server-puppeteer
```

### **2. Configuration Issues to Avoid**

**❌ COMMON MISTAKES:**
- Using `npx -y @modelcontextprotocol/server-puppeteer` (slow, causes timeouts)
- Having conflicting user-level and workspace-level MCP configs
- Invalid JSON with comments in configuration files
- Using `xvfb-run` unnecessarily (can cause connection issues)

**✅ CORRECT CONFIGURATION:**
```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "mcp-server-puppeteer",
      "args": [],
      "env": {
        "PUPPETEER_LAUNCH_OPTIONS": "{\"headless\": true, \"args\": [\"--no-sandbox\", \"--disable-setuid-sandbox\", \"--disable-dev-shm-usage\", \"--disable-gpu\", \"--no-first-run\", \"--no-zygote\", \"--single-process\"]}"
      },
      "disabled": false,
      "autoApprove": [
        "puppeteer_navigate",
        "puppeteer_screenshot",
        "puppeteer_evaluate",
        "puppeteer_click"
      ]
    }
  }
}
```

### **3. Troubleshooting Connection Timeouts**

**If you see: "MCP server connection + listTools timed out after 60 seconds"**

**Step 1:** Check for conflicting configurations
```bash
# Check user-level config (should be empty or not conflict)
cat ~/.kiro/settings/mcp.json

# Check workspace-level config
cat .kiro/settings/mcp.json
```

**Step 2:** Verify package installation
```bash
# Check if installed globally
npm list -g @modelcontextprotocol/server-puppeteer

# If not installed or having issues, reinstall
npm install -g @modelcontextprotocol/server-puppeteer --force
```

**Step 3:** Use direct command instead of npx
- Change `"command": "npx"` to `"command": "mcp-server-puppeteer"`
- Remove npx args: `"args": []`

## ⚠️ **CRITICAL REQUIREMENT: allowDangerous Parameter**

**ALWAYS** include `allowDangerous: true` in ALL Puppeteer MCP tool calls due to security restrictions in the server configuration.

### **❌ WRONG (Will Fail):**
```javascript
mcp_puppeteer_puppeteer_navigate({
    url: "http://127.0.0.1:8000"
})
```

### **✅ CORRECT (Will Work):**
```javascript
mcp_puppeteer_puppeteer_navigate({
    url: "http://127.0.0.1:8000",
    allowDangerous: true
})
```
```

## 📋 **Correct Usage Examples**

### **Navigation:**
```javascript
mcp_puppeteer_puppeteer_navigate({
    url: "http://127.0.0.1:8000/articles/1/",
    allowDangerous: true
})
```

### **Screenshots:**
```javascript
mcp_puppeteer_puppeteer_screenshot({
    name: "homepage",
    allowDangerous: true,
    height: 800,
    width: 1000
})
```

### **Element Interaction:**
```javascript
mcp_puppeteer_puppeteer_click({
    selector: "button#start-btn",
    allowDangerous: true
})
```

### **Form Filling:**
```javascript
mcp_puppeteer_puppeteer_fill({
    selector: "input#username",
    value: "testuser",
    allowDangerous: true
})
```

### **JavaScript Evaluation:**
```javascript
mcp_puppeteer_puppeteer_evaluate({
    script: "console.log('Testing functionality'); return document.title;",
    allowDangerous: true
})
```

## 🚨 **Common Error Messages**

### **Error 1: Missing allowDangerous Parameter**
```
Error: MCP error -32603: Dangerous browser arguments detected: --no-sandbox, --disable-setuid-sandbox, --single-process. Found from environment variable and tool call argument. Set allowDangerous: true in the tool call arguments to override.
```

**Solution:** Add `allowDangerous: true` to the tool call.

### **Error 2: X Server Issues**
```
Error: Missing X server or $DISPLAY
```

**Solution:** The `xvfb-run` command in the configuration should handle this, but if it persists:
1. Check if `xvfb` is installed: `sudo apt-get install xvfb`
2. Verify the MCP server configuration
3. Restart the MCP server

## 🧪 **Testing Workflow**

### **1. Start Django Development Server:**
```bash
python manage.py runserver 127.0.0.1:8000 &
```

### **2. Navigate to Application:**
```javascript
mcp_puppeteer_puppeteer_navigate({
    url: "http://127.0.0.1:8000",
    allowDangerous: true
})
```

### **3. Take Screenshot for Verification:**
```javascript
mcp_puppeteer_puppeteer_screenshot({
    name: "current_page",
    allowDangerous: true,
    height: 800
})
```

### **4. Test Specific Functionality:**
```javascript
mcp_puppeteer_puppeteer_evaluate({
    script: `
        // Test speed reader functionality
        const speedReaderSection = document.getElementById('speed-reader-section');
        const articleContent = speedReaderSection?.dataset.content;
        
        return {
            hasSpeedReader: !!speedReaderSection,
            contentLength: articleContent?.length || 0,
            pageTitle: document.title
        };
    `,
    allowDangerous: true
})
```

## 🔍 **Debugging Tips**

### **1. Always Check Element Existence:**
```javascript
mcp_puppeteer_puppeteer_evaluate({
    script: `
        const element = document.getElementById('target-element');
        return {
            exists: !!element,
            visible: element ? window.getComputedStyle(element).display !== 'none' : false,
            content: element ? element.textContent : null
        };
    `,
    allowDangerous: true
})
```

### **2. Console Log Debugging:**
```javascript
mcp_puppeteer_puppeteer_evaluate({
    script: `
        console.log('=== DEBUG INFO ===');
        console.log('Current URL:', window.location.href);
        console.log('Page Title:', document.title);
        console.log('Elements found:', document.querySelectorAll('button').length);
        return 'Debug info logged to console';
    `,
    allowDangerous: true
})
```

### **3. Wait for Elements:**
```javascript
mcp_puppeteer_puppeteer_evaluate({
    script: `
        // Wait for element to appear
        function waitForElement(selector, timeout = 5000) {
            return new Promise((resolve, reject) => {
                const element = document.querySelector(selector);
                if (element) {
                    resolve(element);
                    return;
                }
                
                const observer = new MutationObserver(() => {
                    const element = document.querySelector(selector);
                    if (element) {
                        observer.disconnect();
                        resolve(element);
                    }
                });
                
                observer.observe(document.body, {
                    childList: true,
                    subtree: true
                });
                
                setTimeout(() => {
                    observer.disconnect();
                    reject(new Error('Element not found within timeout'));
                }, timeout);
            });
        }
        
        // Usage
        return waitForElement('#speed-reader-section')
            .then(element => ({ found: true, id: element.id }))
            .catch(error => ({ found: false, error: error.message }));
    `,
    allowDangerous: true
})
```

## 📝 **Best Practices**

### **1. Always Include allowDangerous: true**
- This is the #1 rule - never forget this parameter
- All Puppeteer MCP calls require it due to security configuration

### **2. Use Descriptive Screenshot Names**
- `homepage`, `article_detail`, `speed_reader_interface`
- Include timestamps if taking multiple shots: `speed_reader_2025_07_17`

### **3. Test in Stages**
1. Navigate to page
2. Take screenshot to verify page loaded
3. Test specific functionality
4. Take final screenshot to verify results

### **4. Handle Errors Gracefully**
- Always wrap complex JavaScript in try-catch blocks
- Return meaningful error information
- Use console.log for debugging

### **5. Clean Up After Testing**
```bash
# Stop Django server if running in background
pkill -f "python manage.py runserver"
```

## 🎯 **Common Use Cases for VeriFast Testing**

### **1. Speed Reader Testing:**
```javascript
// Navigate to article
mcp_puppeteer_puppeteer_navigate({
    url: "http://127.0.0.1:8000/articles/1/",
    allowDangerous: true
})

// Test word splitting functionality
mcp_puppeteer_puppeteer_evaluate({
    script: `
        const speedReaderSection = document.getElementById('speed-reader-section');
        const articleContent = speedReaderSection.dataset.content;
        
        function cleanAndSplitWords(content) {
            if (!content) return [];
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = content;
            let cleanContent = tempDiv.textContent || tempDiv.innerText || '';
            cleanContent = cleanContent.replace(/\\s+/g, ' ').trim();
            return cleanContent.split(/\\s+/).filter(word => word.length > 0);
        }
        
        const words = cleanAndSplitWords(articleContent);
        return {
            contentLength: articleContent.length,
            wordCount: words.length,
            firstWords: words.slice(0, 10),
            hasChoppedWords: words.some(word => word.includes('-') && word.length < 5)
        };
    `,
    allowDangerous: true
})
```

### **2. UI Element Testing:**
```javascript
// Test if all speed reader controls are present
mcp_puppeteer_puppeteer_evaluate({
    script: `
        const controls = {
            startButton: !!document.getElementById('start-pause-btn'),
            resetButton: !!document.getElementById('reset-btn'),
            wpmSlider: !!document.getElementById('wmp-slider'),
            chunkSize: !!document.getElementById('chunk-size'),
            groupConnectors: !!document.getElementById('group-connectors'),
            removeSymbols: !!document.getElementById('remove-symbols'),
            readingFont: !!document.getElementById('reading-font'),
            darkMode: !!document.getElementById('dark-mode')
        };
        
        return {
            allControlsPresent: Object.values(controls).every(Boolean),
            controls: controls
        };
    `,
    allowDangerous: true
})
```

## 🔄 **Remember for Next Time**

1. **ALWAYS** add `allowDangerous: true` to every Puppeteer MCP call
2. Start Django server before testing: `python manage.py runserver 127.0.0.1:8000 &`
3. Take screenshots to verify page state before testing functionality
4. Use meaningful names for screenshots and test results
5. Clean up background processes when done testing

---

*This guide should prevent repeating the same Puppeteer MCP mistakes in future sessions.*