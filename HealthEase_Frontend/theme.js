(function() {
    // 1. Immediate Theme Application (Prevents flashing)
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
        document.documentElement.classList.add('dark-theme');
        
        // Apply class to body as soon as body element is parsed
        const observer = new MutationObserver((mutations, obs) => {
            if (document.body) {
                document.body.classList.add('dark-theme');
                obs.disconnect();
            }
        });
        observer.observe(document.documentElement, { childList: true });
    }
})();

document.addEventListener('DOMContentLoaded', () => {
    // Inject Theme Toggle Button (Self-healing implementation)
    function injectToggle() {
        // Target priority containers where the button makes visual sense
        const targetContainers = [
            document.getElementById('authBtnContainer'),
            document.querySelector('.auth-buttons'),
            document.querySelector('.user-info'),
            document.querySelector('.admin-profile'),
            document.querySelector('.header-container')
        ];
        
        for (const container of targetContainers) {
            if (container) {
                // If button already exists, do nothing
                if (container.querySelector('#themeToggleBtn')) {
                    return;
                }
                
                const isDark = document.body.classList.contains('dark-theme');
                const toggleBtn = document.createElement('button');
                toggleBtn.id = 'themeToggleBtn';
                toggleBtn.className = 'theme-toggle-btn';
                toggleBtn.setAttribute('aria-label', 'Toggle Theme');
                toggleBtn.innerHTML = isDark ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
                toggleBtn.style.marginRight = '10px';
                
                // Insert as the first element inside the container
                container.insertBefore(toggleBtn, container.firstChild);
                
                // Click Handler
                toggleBtn.addEventListener('click', () => {
                    const wasDark = document.body.classList.contains('dark-theme');
                    if (wasDark) {
                        document.body.classList.remove('dark-theme');
                        document.documentElement.classList.remove('dark-theme');
                        localStorage.setItem('theme', 'light');
                        document.querySelectorAll('#themeToggleBtn').forEach(btn => {
                            btn.innerHTML = '<i class="fas fa-moon"></i>';
                        });
                    } else {
                        document.body.classList.add('dark-theme');
                        document.documentElement.classList.add('dark-theme');
                        localStorage.setItem('theme', 'dark');
                        document.querySelectorAll('#themeToggleBtn').forEach(btn => {
                            btn.innerHTML = '<i class="fas fa-sun"></i>';
                        });
                    }
                });
                
                return; // Stop after successful injection
            }
        }
    }
    
    // Initial run
    injectToggle();
    
    // Set up MutationObserver to re-inject toggle if parent innerHTML is wiped by page auth scripts
    const observer = new MutationObserver(() => {
        injectToggle();
    });
    
    // Observe body for changes to child elements (like header updates)
    observer.observe(document.body, { childList: true, subtree: true });
    
    console.log('HealthEase Self-Healing Theme Engine Active');
});
