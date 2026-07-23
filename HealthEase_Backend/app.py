import os
import jwt
import datetime
import urllib.parse
from functools import wraps
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()  # Load .env file locally

# --- App Setup ---
app = Flask(__name__, 
            template_folder='../HealthEase_Frontend',
            static_folder='../HealthEase_Frontend',
            static_url_path='')

# --- Database Configuration ---
# Uses DATABASE_URL from Render/Railway env variable, falls back to local MySQL
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    # Railway provides mysql:// — convert to pymysql driver
    if DATABASE_URL.startswith('mysql://'):
        DATABASE_URL = DATABASE_URL.replace('mysql://', 'mysql+pymysql://', 1)
    # Render provides postgres:// — convert to postgresql:// driver
    elif DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
else:
    # Local fallback
    db_password = urllib.parse.quote_plus("Singh@2004")
    DATABASE_URL = f'mysql+pymysql://root:{db_password}@localhost/healthease'

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-super-secret-and-complex-key-12345')

db = SQLAlchemy(app)
CORS(app)

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
    if Doctor.query.count() > 0:
        return jsonify({'message': 'Doctors already seeded'})
    
    doctors_data = [
        {'name': 'Dr. Sarah Johnson', 'specialization': 'Cardiologist', 'experience': 15, 'rating': 4.9, 'consultation_fee': 500, 'image': '', 'description': 'Expert in cardiovascular health.'},
        {'name': 'Dr. Michael Chen', 'specialization': 'Neurologist', 'experience': 12, 'rating': 4.8, 'consultation_fee': 600, 'image': '', 'description': 'Specialist in brain and nervous system.'},
        {'name': 'Dr. Emily Davis', 'specialization': 'Pediatrician', 'experience': 10, 'rating': 4.7, 'consultation_fee': 450, 'image': '', 'description': 'Dedicated to children health and wellness.'},
        {'name': 'Dr. Vikram Singh', 'specialization': 'Orthopedic', 'experience': 14, 'rating': 4.8, 'consultation_fee': 700, 'image': '', 'description': 'Expert in bone and joint care.'},
        {'name': 'Dr. Priya Patel', 'specialization': 'Dermatologist', 'experience': 8, 'rating': 4.6, 'consultation_fee': 400, 'image': '', 'description': 'Specialist in skin, hair, and nail treatments.'},
        {'name': 'Dr. Robert Smith', 'specialization': 'Psychiatrist', 'experience': 20, 'rating': 4.9, 'consultation_fee': 800, 'image': '', 'description': 'Mental health expert.'}
    ]
    
    for d_data in doctors_data:
        doc = Doctor(**d_data)
        db.session.add(doc)
    
    db.session.commit()
    return jsonify({'message': '6 Doctors seeded successfully!'})

# 6. Seed Admin - DISABLED FOR PRODUCTION
# @app.route('/api/seed_admin', methods=['GET'])
# def seed_admin():
#     return jsonify({'message': 'Endpoint disabled'})

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

# 7b. Get Appointments (Patient's own)
@app.route('/api/appointments', methods=['GET'])
@token_required
def get_appointments(current_user):
    appointments = Appointment.query.filter_by(patientId=current_user.id).order_by(Appointment.id.desc()).all()
    result = []
    for apt in appointments:
        doctor = Doctor.query.get(apt.doctorId)
        result.append({
            'id': apt.id,
            'doctorName': doctor.name if doctor else 'Unknown Doctor',
            'specialization': doctor.specialization if doctor else '',
            'date': apt.date,
            'time': apt.time,
            'symptoms': apt.symptoms,
            'status': apt.status
        })
    return jsonify({'appointments': result})

# 8. Dashboard Stats
@app.route('/api/dashboard/stats', methods=['GET'])
@token_required
def get_stats(current_user):
    total     = Appointment.query.filter_by(patientId=current_user.id).count()
    upcoming  = Appointment.query.filter_by(patientId=current_user.id, status='upcoming').count()
    completed = Appointment.query.filter_by(patientId=current_user.id, status='completed').count()

    return jsonify({
        'totalAppointments':     total,
        'upcomingAppointments':  upcoming,
        'completedAppointments': completed,
    })

# --- Initialize Database (Runs for both local and production) ---
with app.app_context():
    db.create_all()
    print("[OK] Database Connected & Tables Checked!")

# --- Main Entry ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') != 'production')