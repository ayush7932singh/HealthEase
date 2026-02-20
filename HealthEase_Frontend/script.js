/* =========================================
   1. GLOBAL CONFIG & STARTUP
   ========================================= */
const API_BASE = 'http://127.0.0.1:3000/api';
let currentUser = null;

document.addEventListener('DOMContentLoaded', () => {
    // 1. Check Login Status (Without Redirecting)
    checkAuth();

    // 2. Load Page Specific Data
    const path = window.location.pathname;
    
    // Page: Doctors
    if (path.includes('doctors.html')) {
        loadDoctors();
    }
    
    // Page: Features or Home
    if (path.includes('features.html') || path.includes('index.html') || path === '/') {
        loadFeatures(); 
    }
    
    // Page: Home (Featured Doctors)
    if (path.includes('index.html') || path === '/') {
        loadFeaturedDoctors(); 
    }

    // 3. Admin Protection (Only Redirect HERE)
    if (path.includes('admin_panel.html')) {
        const user = JSON.parse(localStorage.getItem('user'));
        if (!user || user.role !== 'admin') {
            window.location.href = 'index.html'; // Safe redirect
        }
    }

    // 4. Modal Close Handlers
    window.onclick = (e) => {
        const authModal = document.getElementById('authModal');
        const apptModal = document.getElementById('appointmentModal');
        if (e.target == authModal) closeAuthModal();
        if (e.target == apptModal && apptModal) apptModal.style.display = 'none';
    };
});

/* =========================================
   2. AUTHENTICATION LOGIC
   ========================================= */
function checkAuth() {
    const userStr = localStorage.getItem('user');
    const container = document.getElementById('authBtnContainer'); 
    const adminLink = document.getElementById('adminLink');

    if (userStr) {
        // --- LOGGED IN ---
        const user = JSON.parse(userStr);
        currentUser = user;
        
        if (container) {
            container.innerHTML = `
                <span style="font-weight:600; color:var(--primary); margin-right:15px; display:inline-block;">
                    Hi, ${user.name.split(' ')[0]}
                </span>
                <button class="btn btn-outline" onclick="logout()" style="padding: 8px 20px;">Logout</button>
            `;
        }
        if (user.role === 'admin' && adminLink) adminLink.style.display = 'block';
    } else {
        // --- GUEST (Logged Out) ---
        currentUser = null;
        if (container) {
            // Just show the Login button. DO NOT REDIRECT.
            container.innerHTML = `<button class="btn btn-primary" onclick="openAuthModal('login')">Login / Sign Up</button>`;
        }
        if (adminLink) adminLink.style.display = 'none';
    }
}

// --- Login API Call ---
async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    const btn = e.target.querySelector('button');
    const originalText = btn.innerHTML;

    try {
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Checking...';
        btn.disabled = true;

        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        
        if (res.ok) { 
            localStorage.setItem('token', data.token);
            localStorage.setItem('user', JSON.stringify(data.user));
            alert('Login Successful!');
            closeAuthModal();
            checkAuth();
            
            // Redirect logic ONLY after successful login
            if(data.user.role === 'admin') {
                window.location.href = 'admin_panel.html';
            } else if(window.location.pathname.includes('login.html')) {
                window.location.href = 'dashboard.html';
            }
        } else {
            alert('Error: ' + (data.message || 'Login Failed'));
        }
    } catch (err) { 
        console.error(err); 
        alert('Server Error: Is the backend running?'); 
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

// --- Signup API Call ---
async function handleSignup(e) {
    e.preventDefault();
    const name = document.getElementById('signupName').value;
    const email = document.getElementById('signupEmail').value;
    const password = document.getElementById('signupPassword').value;
    const roleSelect = document.getElementById('signupRole');
    const role = roleSelect ? roleSelect.value : 'patient';
    const btn = e.target.querySelector('button');
    const originalText = btn.innerHTML;

    try {
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';
        btn.disabled = true;

        const res = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password, role })
        });
        const data = await res.json();

        if(res.ok) {
            alert('Account Created! Please Login.');
            switchTab('login');
        } else {
            alert(data.message || 'Registration Failed');
        }
    } catch (err) { 
        alert('Registration Failed: Server Error'); 
    } finally { 
        btn.innerHTML = originalText; 
        btn.disabled = false; 
    }
}

// Attach Event Listeners
const loginForm = document.getElementById('loginForm');
if(loginForm) loginForm.addEventListener('submit', handleLogin);

const signupForm = document.getElementById('signupForm');
if(signupForm) signupForm.addEventListener('submit', handleSignup);

window.logout = function() {
    if(confirm('Are you sure you want to logout?')) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = 'index.html';
    }
}

/* =========================================
   3. UI MODALS & TABS
   ========================================= */
window.openAuthModal = (type = 'login') => {
    const modal = document.getElementById('authModal');
    if(modal) {
        modal.style.display = 'flex'; 
        switchTab(type);
    }
};

window.closeAuthModal = () => {
    const modal = document.getElementById('authModal');
    if(modal) modal.style.display = 'none';
};

window.switchTab = (tab) => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.auth-section').forEach(s => s.classList.remove('active'));

    if(tab === 'login') {
        const btns = document.querySelectorAll('button[onclick*="login"]');
        btns.forEach(b => { if(b.classList.contains('tab-btn')) b.classList.add('active'); });
        const section = document.getElementById('loginFormSection') || document.getElementById('loginSection');
        if(section) section.classList.add('active');
    } else {
        const btns = document.querySelectorAll('button[onclick*="signup"]');
        btns.forEach(b => { if(b.classList.contains('tab-btn')) b.classList.add('active'); });
        const section = document.getElementById('signupFormSection') || document.getElementById('signupSection');
        if(section) section.classList.add('active');
    }
};

/* =========================================
   4. DATA LOADING
   ========================================= */
async function loadDoctors(targetSelectOnly = false) {
    const grid = document.getElementById('doctorsGrid');
    const select = document.getElementById('doctorSelect'); 
    if(!grid && !select) return;

    try {
        const res = await fetch(`${API_BASE}/doctors`);
        const data = await res.json();
        const doctors = data.doctors || [];

        if(select) {
            select.innerHTML = '<option value="">Select Doctor</option>' + 
                doctors.map(d => `<option value="${d.id}">${d.name} (${d.specialization})</option>`).join('');
        }

        if(grid && !targetSelectOnly) {
            if(doctors.length === 0) {
                grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;">No doctors found.</div>';
            } else {
                grid.innerHTML = doctors.map(doc => `
                    <div class="doctor-card">
                        <div class="doc-img-container">
                            <img src="${doc.image || 'https://via.placeholder.com/300'}" onerror="this.src='https://ui-avatars.com/api/?name=${doc.name}'">
                        </div>
                        <div class="doc-info">
                            <h3 class="doc-name">${doc.name}</h3>
                            <p class="doc-spec">${doc.specialization}</p>
                            <div class="doc-stats">
                                <span><i class="fas fa-star" style="color:#ffc107"></i> ${doc.rating}</span>
                                <span>${doc.experience} Yrs Exp</span>
                            </div>
                            <button class="btn btn-primary full-width" onclick="openBooking('${doc.id}', '${doc.name}')">Book Appointment</button>
                        </div>
                    </div>
                `).join('');
            }
        }
    } catch (err) { 
        console.error('API Error:', err);
        if(grid && !targetSelectOnly) grid.innerHTML = '<p style="color:red; text-align:center;">Failed to load doctors.</p>';
    }
}

async function loadFeaturedDoctors() {
    const grid = document.getElementById('featuredDoctorsGrid');
    if(!grid) return;
    try {
        const res = await fetch(`${API_BASE}/doctors`);
        const data = await res.json();
        const top3 = (data.doctors || []).slice(0, 3);
        
        if(top3.length === 0) {
             grid.innerHTML = '<p>No featured doctors available.</p>';
             return;
        }

        grid.innerHTML = top3.map(doc => `
            <div style="background:white; padding:20px; border-radius:12px; text-align:center; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
                <img src="${doc.image}" style="width:80px; height:80px; border-radius:50%; margin-bottom:10px; object-fit:cover;" onerror="this.src='https://ui-avatars.com/api/?name=${doc.name}'">
                <h3 style="font-size:1.1rem; margin-bottom:5px;">${doc.name}</h3>
                <p style="color:var(--primary); font-size:0.9rem;">${doc.specialization}</p>
            </div>
        `).join('');
    } catch(e) { grid.innerHTML = '<p>Backend not connected.</p>'; }
}

function loadFeatures() {
    const grid = document.getElementById('featuresGrid');
    if(!grid) return;
    
    const features = [
        {icon:'fa-user-md', t:'Expert Doctors', d:'Top specialists available.'},
        {icon:'fa-clock', t:'24/7 Support', d:'Always here for you.'},
        {icon:'fa-shield-alt', t:'Secure Data', d:'Your health data is safe.'},
        {icon:'fa-video', t:'Video Consult', d:'Connect from home.'}
    ];
    
    if(grid.innerHTML.trim() === '' || grid.innerHTML.includes('Loading')) {
        grid.innerHTML = features.map(f => `
            <div class="feature-box">
                <div class="icon-circle"><i class="fas ${f.icon}"></i></div>
                <h3>${f.t}</h3>
                <p>${f.d}</p>
            </div>
        `).join('');
    }
}

/* =========================================
   5. BOOKING LOGIC
   ========================================= */
window.openBooking = async (docId, docName) => {
    if(!currentUser) { 
        openAuthModal('login'); 
        return; 
    }
    
    const modal = document.getElementById('appointmentModal');
    if(modal) {
        modal.style.display = 'flex';
        const select = document.getElementById('doctorSelect');
        if(select && select.options.length <= 1) {
            await loadDoctors(true);
        }
        if(docId && select) {
            select.value = docId;
        }
    }
};

const apptForm = document.getElementById('appointmentForm');
if(apptForm) {
    apptForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const token = localStorage.getItem('token');
        const docSelect = document.getElementById('doctorSelect');
        const dateInput = document.getElementById('appointmentDate');
        const timeInput = document.getElementById('appointmentTime');
        const symInput = document.getElementById('symptoms');

        if(!docSelect.value) { alert("Please select a doctor"); return; }

        const payload = {
            doctorId: docSelect.value,
            date: dateInput.value,
            time: timeInput.value,
            symptoms: symInput ? symInput.value : ''
        };

        try {
            const res = await fetch(`${API_BASE}/appointments`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            
            if(res.ok) {
                alert('Appointment Booked Successfully!');
                document.getElementById('appointmentModal').style.display = 'none';
                apptForm.reset();
            } else {
                alert('Failed: ' + data.message);
            }
        } catch (err) { alert('Booking Failed: Server Error'); }
    });
}