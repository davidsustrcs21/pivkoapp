// Simple JavaScript for interactivity
document.addEventListener('DOMContentLoaded', function() {
    // Add count buttons
    const addButtons = document.querySelectorAll('.add-count-btn');
    addButtons.forEach(button => {
        button.addEventListener('click', function() {
            const amount = this.dataset.amount || 1;
            addCount(amount);
        });
    });
    
    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('.delete-btn');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Opravdu chcete smazat tohoto uživatele?')) {
                e.preventDefault();
            }
        });
    });
    
    // Confirm reset actions
    const resetButtons = document.querySelectorAll('.reset-btn');
    resetButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Opravdu chcete resetovat počet tohoto uživatele?')) {
                e.preventDefault();
            }
        });
    });
});

function addCount(amount = 1) {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/add-count';
    
    const amountInput = document.createElement('input');
    amountInput.type = 'hidden';
    amountInput.name = 'amount';
    amountInput.value = amount;
    
    form.appendChild(amountInput);
    document.body.appendChild(form);
    form.submit();
}

// Auto-refresh dashboard every 30 seconds
if (window.location.pathname === '/dashboard') {
    setInterval(() => {
        window.location.reload();
    }, 30000);
}