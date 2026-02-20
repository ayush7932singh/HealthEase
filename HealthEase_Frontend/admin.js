// admin.js - Handles Admin Login & Dashboard Logic

const API_BASE = 'http://127.0.0.1:3000/api';

document.addEventListener('DOMContentLoaded', () => {
    console.log("Admin Script Loaded"); // Debugging ke liye

    // --- 1. HANDLE ADMIN LOGIN (Login Page Logic) ---
    const adminLoginForm = document.getElementById('adminLoginForm');

    if (adminLoginForm) {
        adminLoginForm.addEventListener('submit', async (e) => {
            e.preventDefault(); // Page reload rokna

            const email = document.getElementById('adminEmail').value;
            const password = document.getElementById('adminPassword').value;
            const btn = e.target.querySelector('button');
            const originalText = btn.innerHTML;

            // UI Feedback (Button loading state)
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Verifying...';
            btn.disabled = true;

            try {
                console.log("Sending request to:", `${API_BASE}/auth/login`);
                
                const res = await fetch(`${API_BASE}/auth/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });

                const data = await res.json();
                console.log("Server Response:", data);

                if (!res.ok) {
                    throw new Error(data.message || 'Invalid credentials');
                }

                // IMPORTANT: Check Role
                if (data.user && data.user.role === 'admin') {
                    console.log("Role Verified: Admin");
                    
                    // Save token and user
                    localStorage.setItem('token', data.token);
                    localStorage.setItem('user', JSON.stringify(data.user));

                    alert('Admin Login Successful!');
                    
                    // Redirect to admin panel
                    window.location.href = 'admin_panel.html';
                } else {
                    console.warn("Role Denied:", data.user.role);
                    throw new Error('Access Denied: You are not an Admin.');
                }

            } catch (err) {
                console.error("Login Error:", err);
                alert(err.message || 'Network error while trying to login.');
            } finally {
                // Reset Button
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        });
    }

    // --- 2. DASHBOARD LOGIC (Admin Name Show Karna) ---
    const adminNameEl = document.getElementById('adminNameDisplay');
    if (adminNameEl) {
        const user = JSON.parse(localStorage.getItem('user'));
        if (user) adminNameEl.textContent = user.name;
    }
});

// --- 3. GLOBAL FUNCTIONS (HTML onclick ke liye zaroori hain) ---

// Sidebar Toggle karna (Mobile ke liye)
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) sidebar.classList.toggle('active');
}

// Logout Function
function logout() {
    if(confirm('Are you sure you want to logout?')) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = 'admin_login.html'; // Wapas login page par bhejo
    }
}