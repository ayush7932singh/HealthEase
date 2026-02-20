import os
import jwt
import datetime
import urllib.parse  # Added for safe password encoding
from functools import wraps
from flask import Flask, jsonify, request, render_template # Added render_template
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

# --- App Setup (UPDATED) ---
# We tell Flask that templates (HTML) and static files (CSS/JS) 
# are in the sibling folder 'HealthEase_Frontend'
app = Flask(__name__, 
            template_folder='../HealthEase_Frontend',
            static_folder='../HealthEase_Frontend',
            static_url_path='')

# --- Database Configuration ---
# Handling the '@' in your password "Singh@2004" safely
db_password = urllib.parse.quote_plus("Singh@2004")
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://root:{db_password}@localhost/healthease'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-super-secret-and-complex-key-12345'

db = SQLAlchemy(app)
CORS(app) # Enables CORS for all routes

# --- Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(300))
    role = db.Column(db.String(20)) # 'patient' or 'admin'
    dob = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    specialization = db.Column(db.String(100))
    experience = db.Column(db.Integer)
    rating = db.Column(db.Float)
    consultation_fee = db.Column(db.Integer)
    image = db.Column(db.String(300))
    description = db.Column(db.String(400))

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patientId = db.Column(db.Integer, nullable=False)
    doctorId = db.Column(db.Integer, nullable=False)
    date = db.Column(db.String(20))
    time = db.Column(db.String(20))
    symptoms = db.Column(db.String(200))
    status = db.Column(db.String(20)) # 'upcoming', 'completed'

# --- Token Verification Decorator ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            parts = auth_header.split(" ")
            if len(parts) > 1:
                token = parts[1] # Extract token after 'Bearer'
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['id']).first()
            if not current_user:
                 return jsonify({'message': 'User invalid!'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except Exception as e:
            return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated


# ==========================================
#  FRONTEND ROUTES (This fixes the 404 Error)
# ==========================================

@app.route('/')
def home():
    try:
        return render_template('index.html')
    except Exception as e:
        return f"Error: Could not find index.html in ../HealthEase_Frontend. {str(e)}"

@app.route('/<page_name>.html')
def serve_pages(page_name):
    try:
        return render_template(f'{page_name}.html')
    except Exception as e:
        return f"Error: Could not find {page_name}.html. {str(e)}", 404


# ==========================================
#  API ENDPOINTS
# ==========================================

# 1. Register User
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'success': False, 'message': 'Email already exists'}), 409

    hashed_pw = generate_password_hash(data['password'])

    new_user = User(
        name=data['name'],
        email=data['email'],
        password_hash=hashed_pw,
        role=data['role'],
        dob=data.get('dob'),
        phone=data.get('phone'),
        address=data.get('address')
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'success': True, 'message': 'User registered successfully'})

# 2. Login User
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    print(f"Login attempt: {email}") # Debug log

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    
    token = jwt.encode({
        'id': user.id,
        'email': user.email,
        'role': user.role,
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({
        'success': True,
        'token': token,
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role
        }
    })

# 3. Verify Token Endpoint
@app.route('/api/auth/verify', methods=['GET'])
@token_required
def verify(current_user):
    return jsonify({
        'success': True,
        'user': {
            'id': current_user.id,
            'name': current_user.name,
            'email': current_user.email,
            'role': current_user.role
        }
    })

# 4. Get Doctors List
@app.route('/api/doctors', methods=['GET'])
def get_doctors():
    doctors = Doctor.query.all()
    result = []
    for d in doctors:
        result.append({
            'id': d.id,
            'name': d.name,
            'specialization': d.specialization,
            'experience': d.experience,
            'rating': d.rating,
            'consultation_fee': d.consultation_fee,
            'image': d.image,
            'description': d.description
        })
    return jsonify({'doctors': result})

# 5. Seed Doctors (Total 6 Doctors)
@app.route('/api/seed_doctors', methods=['GET'])
def seed_doctors():
    if Doctor.query.count() >= 6:
        return jsonify({'message': 'All 6 Doctors already exist in database'})
    
    # 1. Cardiologist
    doc1 = Doctor(name="Dr. Sharma", specialization="Cardiologist", experience=10, rating=4.5, consultation_fee=500, description="Heart specialist.", image="https://img.freepik.com/free-photo/doctor-with-his-arms-crossed-white-background_1368-5790.jpg")
    # 2. Dermatologist
    doc2 = Doctor(name="Dr. Verma", specialization="Dermatologist", experience=8, rating=4.8, consultation_fee=400, description="Skin specialist.", image="https://img.freepik.com/free-photo/woman-doctor-wearing-lab-coat-with-stethoscope-isolated_1303-29791.jpg")
    # 3. Pediatrician
    doc3 = Doctor(name="Dr. Anita Roy", specialization="Pediatrician", experience=12, rating=4.9, consultation_fee=600, description="Child specialist.", image="https://img.freepik.com/free-photo/portrait-smiling-medical-worker-girl-doctor-white-coat-holding-clipboard_1258-88134.jpg")
    # 4. Neurologist
    doc4 = Doctor(name="Dr. Rajesh Gupta", specialization="Neurologist", experience=15, rating=4.7, consultation_fee=800, description="Brain specialist.", image="https://img.freepik.com/free-photo/portrait-successful-mid-adult-doctor-with-crossed-arms_1262-12865.jpg")
    # 5. Orthopedic
    doc5 = Doctor(name="Dr. Vikram Singh", specialization="Orthopedic", experience=14, rating=4.6, consultation_fee=700, description="Bone specialist.", image="https://img.freepik.com/free-photo/doctor-standing-with-folder-stethoscope_1291-16.jpg")
    # 6. Psychiatrist
    doc6 = Doctor(name="Dr. Meera Nair", specialization="Psychiatrist", experience=9, rating=4.8, consultation_fee=900, description="Mental health.", image="https://img.freepik.com/free-photo/pleased-young-female-doctor-wearing-medical-robe-stethoscope-around-neck-standing-with-closed-posture_409827-254.jpg")
    
    docs = [doc1, doc2, doc3, doc4, doc5, doc6]
    added_count = 0
    
    for doc in docs:
        if not Doctor.query.filter_by(name=doc.name).first():
            db.session.add(doc)
            added_count += 1
    
    db.session.commit()
    return jsonify({'message': f'{added_count} new doctors added! Total 6 available.'})

# 6. Seed Admin
@app.route('/api/seed_admin', methods=['GET'])
def seed_admin():
    email = "admin@healthease.com" 
    password = "admin123"
    
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Admin user already exists!'})
    
    admin_user = User(
        name="Super Admin",
        email=email,
        password_hash=generate_password_hash(password),
        role="admin",  
        phone="9876543210",
        address="Admin Office, HealthEase",
        dob="1990-01-01"
    )
    
    db.session.add(admin_user)
    db.session.commit()
    
    return jsonify({'message': f'Admin created! Email: {email}, Password: {password}'})

# 7. Book Appointment
@app.route('/api/appointments', methods=['POST'])
@token_required
def book_appointment(current_user):
    data = request.get_json()

    new_appt = Appointment(
        patientId=current_user.id,
        doctorId=data['doctorId'],
        date=data['date'],
        time=data['time'],
        symptoms=data.get('symptoms', ''),
        status='upcoming'
    )

    db.session.add(new_appt)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Appointment booked successfully'})

# 8. Dashboard Stats
@app.route('/api/dashboard/stats', methods=['GET'])
@token_required
def get_stats(current_user):
    upcoming = Appointment.query.filter_by(patientId=current_user.id, status='upcoming').count()

    return jsonify({
        'upcomingAppointments': upcoming,
        'prescriptions': 2, 
        'labReports': 1     
    })

# --- Main Entry ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Database Connected & Tables Checked!")

    app.run(port=3000, debug=True)