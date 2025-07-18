// Beer Counter JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Add any interactive functionality here
    console.log('Beer Counter loaded');
    
    // Auto-refresh count display every 30 seconds
    if (window.location.pathname === '/dashboard') {
        setInterval(() => {
            // Could add AJAX refresh here if needed
        }, 30000);
    }
});
