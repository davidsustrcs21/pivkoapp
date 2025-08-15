// Beer Counter JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('Beer Counter loaded');
    
    // Auto-refresh count display every 30 seconds
    if (window.location.pathname === '/dashboard') {
        setInterval(() => {
            // Could add AJAX refresh here if needed
        }, 30000);
    }
    
    // Confirm dialogs for admin actions
    const resetButtons = document.querySelectorAll('.reset-btn');
    const deleteButtons = document.querySelectorAll('.delete-btn');
    
    resetButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Opravdu chcete resetovat počet piv pro tohoto uživatele?')) {
                e.preventDefault();
            }
        });
    });
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Opravdu chcete smazat tohoto uživatele? Tato akce je nevratná!')) {
                e.preventDefault();
            }
        });
    });
});

