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

    // Floating numbers effect
    document.addEventListener('submit', function(e) {
        const form = e.target;
        const amountInput = form.querySelector('input[name="amount"]');
        
        if (amountInput) {
            const amount = parseInt(amountInput.value);
            const card = form.closest('.bg-white') || form.closest('.dark\\:bg-gray-800');
            
            if (card && amount !== 0) {
                showFloatingNumber(card, amount);
            }
        }
    });

    // Floating numbers effect pro dashboard tlačítka
    document.addEventListener('click', function(e) {
        // Zachyť kliknutí na tlačítka + a - na dashboardu
        if (e.target.tagName === 'BUTTON' && e.target.closest('form[action="/add-count"]')) {
            const form = e.target.closest('form');
            const amountInput = form.querySelector('input[name="amount"]');
            
            if (amountInput) {
                const amount = parseInt(amountInput.value);
                const card = form.closest('.bg-white') || form.closest('.dark\\:bg-gray-800');
                
                if (card && amount !== 0) {
                    // Spusť efekt před odesláním formuláře
                    showFloatingNumber(card, amount);
                }
            }
        }
    });
});

function showFloatingNumber(element, amount) {
    const floatingDiv = document.createElement('div');
    floatingDiv.textContent = amount > 0 ? `+${amount}` : `${amount}`;
    floatingDiv.className = `floating-number ${amount > 0 ? 'positive' : 'negative'}`;
    
    const rect = element.getBoundingClientRect();
    floatingDiv.style.left = (rect.left + rect.width / 2) + 'px';
    floatingDiv.style.top = (rect.top + rect.height / 2) + 'px';
    
    document.body.appendChild(floatingDiv);
    
    setTimeout(() => {
        floatingDiv.style.transform = 'translateY(-60px)';
        floatingDiv.style.opacity = '0';
    }, 50);
    
    setTimeout(() => {
        if (floatingDiv.parentNode) {
            document.body.removeChild(floatingDiv);
        }
    }, 1000);
}














