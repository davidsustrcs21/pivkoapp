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

    // Floating numbers effect - opravený event listener
    document.addEventListener('click', function(e) {
        if (e.target.tagName === 'BUTTON' && e.target.type === 'submit') {
            console.log('Submit button clicked!');
            const form = e.target.closest('form');
            const amountInput = form?.querySelector('input[name="amount"]');
            
            if (amountInput) {
                const amount = parseInt(amountInput.value);
                console.log('Amount found:', amount);
                
                // Najdi správný kontejner
                const card = form.closest('.bg-white') || form.closest('[class*="bg-gray-800"]');
                console.log('Card found:', card);
                
                if (card && amount !== 0) {
                    console.log('Showing floating number:', amount);
                    showFloatingNumber(card, amount);
                }
            }
        }
    });
});

function showFloatingNumber(element, amount) {
    console.log('showFloatingNumber called with:', amount);
    const floatingDiv = document.createElement('div');
    floatingDiv.textContent = amount > 0 ? `+${amount}` : `${amount}`;
    floatingDiv.className = `floating-number ${amount > 0 ? 'positive' : 'negative'}`;
    
    // Pozice relativně k elementu
    const rect = element.getBoundingClientRect();
    floatingDiv.style.left = (rect.left + rect.width / 2) + 'px';
    floatingDiv.style.top = (rect.top + rect.height / 2) + 'px';
    
    document.body.appendChild(floatingDiv);
    console.log('Floating div added to body');
    
    // Animace
    setTimeout(() => {
        floatingDiv.style.transform = 'translateY(-60px)';
        floatingDiv.style.opacity = '0';
        console.log('Animation started');
    }, 50);
    
    // Odstranění po animaci
    setTimeout(() => {
        if (floatingDiv.parentNode) {
            document.body.removeChild(floatingDiv);
            console.log('Floating div removed');
        }
    }, 1000);
}






