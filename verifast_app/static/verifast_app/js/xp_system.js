/**
 * XP System JavaScript - Real-time updates and UI interactions
 */

class XPSystemManager {
    constructor() {
        this.currentXP = 0;
        this.totalXP = 0;
        this.currentLevel = 0;
        this.transactionHistory = [];
        this.isHistoryVisible = false;
        
        this.initializeXPSystem();
        this.setupEventListeners();
    }
    
    initializeXPSystem() {
        // Get initial XP values from the page
        const totalXPElement = document.getElementById('total-xp-amount');
        const spendableXPElement = document.getElementById('spendable-xp-amount');
        
        if (totalXPElement) {
            this.totalXP = parseInt(totalXPElement.textContent.replace(/,/g, '')) || 0;
        }
        
        if (spendableXPElement) {
            this.currentXP = parseInt(spendableXPElement.textContent.replace(/,/g, '')) || 0;
        }
        
        this.currentLevel = Math.floor(this.totalXP / 1000);
        
        // Initialize WebSocket connection for real-time updates (if available)
        this.initializeWebSocket();
    }
    
    setupEventListeners() {
        // Listen for XP-related events
        document.addEventListener('xp:earned', (event) => {
            this.handleXPEarned(event.detail);
        });
        
        document.addEventListener('xp:spent', (event) => {
            this.handleXPSpent(event.detail);
        });
        
        document.addEventListener('xp:levelup', (event) => {
            this.handleLevelUp(event.detail);
        });
        
        // Listen for quiz completion events
        document.addEventListener('quiz:completed', (event) => {
            this.handleQuizCompletion(event.detail);
        });
        
        // Listen for social interaction events
        document.addEventListener('social:interaction', (event) => {
            this.handleSocialInteraction(event.detail);
        });
    }
    
    initializeWebSocket() {
        // Initialize WebSocket for real-time XP updates (optional)
        if (typeof WebSocket !== 'undefined' && window.location.protocol === 'https:') {
            try {
                const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${wsProtocol}//${window.location.host}/ws/xp/`;
                
                this.websocket = new WebSocket(wsUrl);
                
                this.websocket.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                };
                
                this.websocket.onerror = (error) => {
                    console.log('WebSocket error:', error);
                };
            } catch (error) {
                console.log('WebSocket not available:', error);
            }
        }
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'xp_update':
                this.updateXPDisplay(data.total_xp, data.current_xp);
                break;
            case 'xp_transaction':
                this.addTransactionToHistory(data.transaction);
                break;
            case 'level_up':
                this.handleLevelUp(data);
                break;
        }
    }
    
    handleXPEarned(data) {
        const { amount, source, description } = data;
        
        // Update XP values
        this.totalXP += amount;
        this.currentXP += amount;
        
        // Update display
        this.updateXPDisplay(this.totalXP, this.currentXP);
        
        // Show notification
        showXPEarned(amount, source, description);
        
        // Check for level up
        const newLevel = Math.floor(this.totalXP / 1000);
        if (newLevel > this.currentLevel) {
            this.currentLevel = newLevel;
            this.handleLevelUp({ level: newLevel, totalXP: this.totalXP, spendableXP: this.currentXP });
        }
        
        // Add to transaction history
        this.addTransactionToHistory({
            type: 'EARN',
            amount: amount,
            source: source,
            description: description,
            timestamp: new Date()
        });
    }
    
    handleXPSpent(data) {
        const { amount, purpose, description } = data;
        
        // Update XP values (only spendable XP decreases)
        this.currentXP -= amount;
        
        // Update display
        this.updateXPDisplay(this.totalXP, this.currentXP);
        
        // Show notification
        showXPSpent(amount, purpose, description);
        
        // Add to transaction history
        this.addTransactionToHistory({
            type: 'SPEND',
            amount: -amount,
            source: purpose,
            description: description,
            timestamp: new Date()
        });
    }
    
    handleLevelUp(data) {
        const { level, totalXP, spendableXP } = data;
        
        // Show level up modal
        showLevelUp(level, totalXP, spendableXP);
        
        // Update level display
        this.updateLevelDisplay(level);
        
        // Show special notification
        xpNotifications.showNotification('levelup', 'Level Up!', `Congratulations! You reached Level ${level}`, 0, 8000);
    }
    
    handleQuizCompletion(data) {
        const { score, xpBreakdown, hasLevelUp } = data;
        
        if (xpBreakdown.total_xp > 0) {
            // Handle main XP earning
            this.handleXPEarned({
                amount: xpBreakdown.base_xp,
                source: 'quiz_completion',
                description: `Quiz completed with ${score}% score`
            });
            
            // Handle bonuses separately
            if (xpBreakdown.perfect_score_bonus > 0) {
                setTimeout(() => {
                    showXPBonus(xpBreakdown.perfect_score_bonus, 'Perfect Score', 'Amazing! Perfect quiz performance!');
                }, 1000);
            }
            
            if (xpBreakdown.wpm_improvement_bonus > 0) {
                setTimeout(() => {
                    showXPBonus(xpBreakdown.wpm_improvement_bonus, 'Speed Record', 'New personal speed record!');
                }, 1500);
            }
            
            if (xpBreakdown.reading_streak_bonus > 0) {
                setTimeout(() => {
                    showXPBonus(xpBreakdown.reading_streak_bonus, 'Reading Streak', 'Keep up the daily reading!');
                }, 2000);
            }
        }
    }
    
    handleSocialInteraction(data) {
        const { type, cost, reward, isAuthor } = data;
        
        if (isAuthor && reward > 0) {
            // User received a reward for their comment
            this.handleXPEarned({
                amount: reward,
                source: 'interaction_reward',
                description: `Received ${type} interaction reward`
            });
        } else if (cost > 0) {
            // User spent XP on interaction
            this.handleXPSpent({
                amount: cost,
                purpose: `interaction_${type.toLowerCase()}`,
                description: `Gave ${type} interaction`
            });
        }
    }
    
    updateXPDisplay(totalXP, currentXP) {
        // Update XP amounts
        const totalXPElement = document.getElementById('total-xp-amount');
        const spendableXPElement = document.getElementById('spendable-xp-amount');
        
        if (totalXPElement) {
            this.animateNumberChange(totalXPElement, totalXP);
        }
        
        if (spendableXPElement) {
            this.animateNumberChange(spendableXPElement, currentXP);
        }
        
        // Update progress bar
        this.updateProgressBar(totalXP);
        
        // Update level display
        const newLevel = Math.floor(totalXP / 1000);
        this.updateLevelDisplay(newLevel);
    }
    
    updateProgressBar(totalXP) {
        const progressFill = document.querySelector('.xp-progress-fill');
        if (progressFill) {
            const progressInLevel = totalXP % 1000;
            const progressPercentage = (progressInLevel / 1000) * 100;
            progressFill.style.width = `${progressPercentage}%`;
        }
        
        // Update progress text
        const progressXP = document.querySelector('.progress-xp');
        if (progressXP) {
            const progressInLevel = totalXP % 1000;
            progressXP.textContent = `${progressInLevel} / 1000 XP`;
        }
    }
    
    updateLevelDisplay(level) {
        const levelElements = document.querySelectorAll('.level-text, .level-number');
        levelElements.forEach(element => {
            if (element.classList.contains('level-text')) {
                element.textContent = `Level ${level}`;
            } else {
                element.textContent = level;
            }
        });
    }
    
    animateNumberChange(element, newValue) {
        const currentValue = parseInt(element.textContent.replace(/,/g, '')) || 0;
        const difference = newValue - currentValue;
        
        if (difference === 0) return;
        
        const duration = 1000; // 1 second animation
        const steps = 30;
        const stepValue = difference / steps;
        const stepDuration = duration / steps;
        
        let currentStep = 0;
        
        const animate = () => {
            currentStep++;
            const value = Math.round(currentValue + (stepValue * currentStep));
            element.textContent = value.toLocaleString();
            
            if (currentStep < steps) {
                setTimeout(animate, stepDuration);
            } else {
                element.textContent = newValue.toLocaleString();
            }
        };
        
        animate();
    }
    
    addTransactionToHistory(transaction) {
        this.transactionHistory.unshift(transaction);
        
        // Update transaction history UI if visible
        if (this.isHistoryVisible) {
            this.refreshTransactionHistory();
        }
    }
    
    refreshTransactionHistory() {
        // This would refresh the transaction history display
        // Implementation depends on how the history is loaded (AJAX, etc.)
        console.log('Refreshing transaction history...');
    }
}

// Transaction History Functions
function showXPHistory() {
    const historyElement = document.getElementById('xp-transaction-history');
    if (historyElement) {
        historyElement.style.display = 'block';
        historyElement.style.position = 'fixed';
        historyElement.style.top = '50%';
        historyElement.style.left = '50%';
        historyElement.style.transform = 'translate(-50%, -50%)';
        historyElement.style.zIndex = '1500';
        historyElement.style.maxHeight = '80vh';
        historyElement.style.overflow = 'auto';
        
        // Add backdrop
        const backdrop = document.createElement('div');
        backdrop.id = 'xp-history-backdrop';
        backdrop.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 1400;
        `;
        backdrop.onclick = hideXPHistory;
        document.body.appendChild(backdrop);
        
        xpSystem.isHistoryVisible = true;
    }
}

function hideXPHistory() {
    const historyElement = document.getElementById('xp-transaction-history');
    const backdrop = document.getElementById('xp-history-backdrop');
    
    if (historyElement) {
        historyElement.style.display = 'none';
    }
    
    if (backdrop) {
        backdrop.remove();
    }
    
    xpSystem.isHistoryVisible = false;
}

function filterTransactions(type) {
    // Update active tab
    document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelector(`[data-filter="${type}"]`).classList.add('active');
    
    // Filter transaction items
    const transactions = document.querySelectorAll('.transaction-item');
    transactions.forEach(transaction => {
        const transactionType = transaction.classList.contains('earn') ? 'earned' : 'spent';
        
        if (type === 'all' || type === transactionType) {
            transaction.style.display = 'flex';
        } else {
            transaction.style.display = 'none';
        }
    });
}

function filterBySource() {
    const sourceFilter = document.getElementById('source-filter');
    const selectedSource = sourceFilter.value;
    
    const transactions = document.querySelectorAll('.transaction-item');
    transactions.forEach(transaction => {
        const transactionSource = transaction.getAttribute('data-source');
        
        if (!selectedSource || transactionSource === selectedSource) {
            transaction.style.display = 'flex';
        } else {
            transaction.style.display = 'none';
        }
    });
}

function filterByTime() {
    const timeFilter = document.getElementById('time-filter');
    const selectedTime = timeFilter.value;
    
    if (!selectedTime) {
        document.querySelectorAll('.transaction-item').forEach(item => {
            item.style.display = 'flex';
        });
        return;
    }
    
    const now = new Date();
    let cutoffDate;
    
    switch (selectedTime) {
        case 'today':
            cutoffDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
            break;
        case 'week':
            cutoffDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
            break;
        case 'month':
            cutoffDate = new Date(now.getFullYear(), now.getMonth(), 1);
            break;
    }
    
    const transactions = document.querySelectorAll('.transaction-item');
    transactions.forEach(transaction => {
        const transactionDate = new Date(transaction.getAttribute('data-date'));
        
        if (transactionDate >= cutoffDate) {
            transaction.style.display = 'flex';
        } else {
            transaction.style.display = 'none';
        }
    });
}

function loadMoreTransactions() {
    // This would load more transactions via AJAX
    console.log('Loading more transactions...');
    
    // Placeholder implementation
    const loadMoreBtn = document.querySelector('.load-more-btn');
    if (loadMoreBtn) {
        loadMoreBtn.textContent = _('loading');
        loadMoreBtn.disabled = true;
        
        // Simulate loading
        setTimeout(() => {
            loadMoreBtn.textContent = _('load_more_transactions');
            loadMoreBtn.disabled = false;
        }, 1000);
    }
}

// Initialize XP System when DOM is loaded
let xpSystem;
document.addEventListener('DOMContentLoaded', () => {
    xpSystem = new XPSystemManager();
});

// Export for global access
window.XPSystem = XPSystemManager;
window.showXPHistory = showXPHistory;
window.hideXPHistory = hideXPHistory;
window.filterTransactions = filterTransactions;
window.filterBySource = filterBySource;
window.filterByTime = filterByTime;
window.loadMoreTransactions = loadMoreTransactions;