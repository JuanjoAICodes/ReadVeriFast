// Simple test to verify JavaScript is loading
console.log('TEST: JavaScript file loaded successfully');

document.addEventListener('DOMContentLoaded', function() {
    console.log('TEST: DOM loaded');
    
    // Check if speed reader section exists
    const section = document.getElementById('speed-reader-section');
    console.log('TEST: Speed reader section found:', !!section);
    
    if (section) {
        console.log('TEST: Section data attributes:', {
            content: section.dataset.content ? 'Present' : 'Missing',
            userWpm: section.dataset.userWpm,
            articleId: section.dataset.articleId
        });
    }
    
    // Check for start button
    const startBtn = document.getElementById('start-pause-btn');
    console.log('TEST: Start button found:', !!startBtn);
    
    if (startBtn) {
        startBtn.addEventListener('click', function() {
            console.log('TEST: Start button clicked!');
            alert('Button click detected!');
        });
    }
});