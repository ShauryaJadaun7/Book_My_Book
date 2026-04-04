document.addEventListener('DOMContentLoaded', () => {
    
    // 1. Live Image Preview for Uploads
    const coverInput = document.getElementById('cover_image');
    const coverPreview = document.getElementById('cover_preview');
    
    if (coverInput && coverPreview) {
        coverInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    coverPreview.src = e.target.result;
                    coverPreview.classList.remove('d-none'); // Show the image
                    // Hide the placeholder icon if it exists
                    const placeholder = document.getElementById('cover_placeholder');
                    if (placeholder) placeholder.classList.add('d-none');
                }
                reader.readAsDataURL(file);
            }
        });
    }

    // 2. Smooth Form Toggling (Sale, Borrow, Barter) //
    const toggleFields = [
        { checkboxId: 'flexSwitchSale', targetId: 'price_container' },
        { checkboxId: 'flexSwitchBorrow', targetId: 'borrow_fee_container' },
        { checkboxId: 'flexSwitchBarter', targetId: 'barter_prefs_container' },
    ];

    toggleFields.forEach(field => {
        const checkbox = document.getElementById(field.checkboxId);
        const targetContainer = document.getElementById(field.targetId);
        
        if (checkbox && targetContainer) {
            // Initial state based on whether it's checked (e.g., editing existing)
            targetContainer.style.display = checkbox.checked ? 'block' : 'none';
            // Also animate toggle
            checkbox.addEventListener('change', function() {
                if(this.checked) {
                    targetContainer.style.display = 'block';
                    targetContainer.classList.add('fade-in'); // assuming a nice CSS class
                } else {
                    targetContainer.style.display = 'none';
                }
            });
        }
    });

    // 3. Global Toast Notifications Listener (HTMX integration)
    // Listen for custom trigger from cart/routes.py
    document.body.addEventListener("cartUpdated", function(evt) {
        let msg = evt.detail.value;
        let type = evt.detail.type || 'success';
        showToast(msg, type);
    });

    // 4. Cart Dynamic Totals Update
    document.body.addEventListener("cartTotalUpdated", function(evt) {
        let newTotal = evt.detail.total;
        let newCount = evt.detail.count;
        
        let formattedTotal = '₹' + parseFloat(newTotal).toFixed(2);
        
        let totalEl = document.getElementById('cart_total');
        let subtotalEl = document.getElementById('cart_subtotal');
        let countEl = document.getElementById('cart_count');
        
        if (totalEl) totalEl.innerHTML = formattedTotal;
        if (subtotalEl) subtotalEl.innerHTML = formattedTotal;
        if (countEl) countEl.innerHTML = newCount;
        
        // Reload page if cart is emptied to show empty cart state
        if (newCount === 0) {
            window.location.reload();
        }
    });

    function showToast(message, type) {
        const toastEl = document.getElementById('liveToast');
        if (!toastEl) return;
        
        const toastMessage = document.getElementById('toastMessage');
        if (type === 'success') {
            toastEl.className = 'toast align-items-center text-bg-success border-0';
        } else if (type === 'danger') {
             toastEl.className = 'toast align-items-center text-bg-danger border-0';
        } else {
             toastEl.className = `toast align-items-center text-bg-${type} border-0`;
        }
        toastMessage.innerHTML = message;
        // Make sure bootstrap is loaded globally
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
    }
    
    // Make showToast accessible globally if needed
    window.showToast = showToast;

    // 5. Theme Toggle Logic
    const themeToggleBtn = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const htmlElement = document.documentElement;

    function applyTheme(theme) {
        htmlElement.setAttribute('data-bs-theme', theme);
        localStorage.setItem('bmb-theme', theme);
        if(themeIcon) {
            themeIcon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-stars-fill';
        }
    }

    // Initialize Theme
    const savedTheme = localStorage.getItem('bmb-theme');
    if (savedTheme) {
        applyTheme(savedTheme);
    } else {
        // Default to dark if no preference
        applyTheme('dark');
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const currentTheme = htmlElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
        });
    }

    // 6. Auto-dismiss Flash Messages after 6 seconds
    const flashAlerts = document.querySelectorAll('.alert');
    flashAlerts.forEach(alertEl => {
        setTimeout(() => {
            if (typeof bootstrap !== 'undefined') {
                const bsAlert = new bootstrap.Alert(alertEl);
                bsAlert.close();
            } else {
                alertEl.style.transition = 'opacity 0.5s ease';
                alertEl.style.opacity = '0';
                setTimeout(() => alertEl.remove(), 500);
            }
        }, 6000);
    });

});
