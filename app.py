import os
import sqlite3
import re
from datetime import datetime
from functools import wraps
from flask import Flask, g, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "muranga-county-secret-key"
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

if os.environ.get('RENDER'):
    DATABASE = "/tmp/muranga.db"
else:
    INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    DATABASE = os.path.join(INSTANCE_DIR, "muranga.db")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CATEGORIES = ["Broken Streetlight", "Water Issue", "Garbage Collection", "Road / Pothole", "Security Issue", "Other"]
STATUSES = ["Pending", "In Progress", "Resolved"]
WARDS = ["Kiharu", "Kandara", "Mathioya", "Kangema", "Maragua", "Kigumo", "Kahuro", "Gatanga", "Kihumbu-ini", "Wangu", "Mugoiri", "Mbiri", "Township", "Murarandia", "Kirogo", "Ichagaki", "Kamahuha", "Kakuzi"]

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DATABASE)
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            profile_photo TEXT,
            is_admin BOOLEAN DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT NOT NULL,
            image TEXT,
            status TEXT DEFAULT 'Pending',
            timeline TEXT,
            admin_note TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    ''')
    
    if db.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0:
        db.execute('INSERT INTO users (full_name, email, phone, password_hash, is_admin) VALUES (?, ?, ?, ?, ?)',
                   ('Admin Muranga', 'admin.muranga@gmail.com', '+254711223344', generate_password_hash('Admin@12345'), 1))
    
    db.commit()
    db.close()

init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('admin_login'))
        if not session.get('is_admin'):
            abort(403) 
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_globals():
    user = None
    if 'user_id' in session:
        user = get_db().execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    return dict(current_user=user, CATEGORIES=CATEGORIES, STATUSES=STATUSES, year=datetime.now().year)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['is_admin'] = bool(user['is_admin'])
            if session['is_admin']:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        flash("Invalid email or password.", "error")
    return render_template('auth.html', mode='login')

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        
        if user and check_password_hash(user['password_hash'], password):
            if user['is_admin']:
                session.clear()
                session['user_id'] = user['id']
                session['is_admin'] = True
                return redirect(url_for('admin_dashboard'))
            else:
                flash("Access denied. You are not an administrator.", "error")
        else:
            flash("Invalid email or password.", "error")
            
    return render_template('admin_login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        password = request.form['password']
        
        if password != request.form['confirm_password']:
            flash("Passwords do not match.", "error")
            return redirect(url_for('register'))
            
        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$", password):
            flash("Password must be at least 8 chars and include uppercase, lowercase, number, and symbol.", "error")
            return redirect(url_for('register'))
            
        try:
            db = get_db()
            db.execute("INSERT INTO users (full_name, phone, email, password_hash, is_admin) VALUES (?, ?, ?, ?, 0)",
                       (request.form['full_name'], request.form['phone'], request.form['email'], generate_password_hash(password)))
            db.commit()
            flash("Citizen account created! Please log in.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Email already exists.", "error")
    return render_template('auth.html', mode='register')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))

    db = get_db()
    page = request.args.get('page', 1, type=int)
    per_page = 5
    offset = (page - 1) * per_page

    all_reqs_count = db.execute("SELECT COUNT(*) FROM requests WHERE user_id = ?", (session['user_id'],)).fetchone()[0]
    
    reqs = db.execute("""
        SELECT * FROM requests 
        WHERE user_id = ? 
        ORDER BY id DESC 
        LIMIT ? OFFSET ?
    """, (session['user_id'], per_page, offset)).fetchall()
    
    stats = {
        'total': all_reqs_count,
        'pending': db.execute("SELECT COUNT(*) FROM requests WHERE user_id = ? AND status='Pending'", (session['user_id'],)).fetchone()[0],
        'progress': db.execute("SELECT COUNT(*) FROM requests WHERE user_id = ? AND status='In Progress'", (session['user_id'],)).fetchone()[0],
        'resolved': db.execute("SELECT COUNT(*) FROM requests WHERE user_id = ? AND status='Resolved'", (session['user_id'],)).fetchone()[0]
    }
    
    total_pages = (all_reqs_count + per_page - 1) // per_page

    return render_template('dashboard.html', 
                           requests=reqs, 
                           stats=stats, 
                           current_page=page, 
                           total_pages=total_pages)

@app.route('/new-request', methods=['GET', 'POST'])
@login_required
def new_request():
    if request.method == 'POST':
        db = get_db()
        count = db.execute("SELECT COUNT(*) as c FROM requests").fetchone()['c']
        ref = f"MCG-{count + 1:03d}"
        image_name = None
        file = request.files.get('image')
        if file and file.filename:
            image_name = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))
        ward = request.form.get('ward', '').strip()
        specific_location = request.form.get('location', '').strip()
        full_location = f"{ward} Ward, {specific_location}" if ward else specific_location
        db.execute("""INSERT INTO requests (reference, user_id, category, title, location, description, image, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                   (ref, session['user_id'], request.form['category'], request.form['title'], full_location, request.form['description'], image_name, datetime.now().strftime("%d %b %Y")))
        db.commit()
        flash(f"Request Submitted! Ref: {ref}", "success")
        return redirect(url_for('dashboard'))
    return render_template('new-request.html', WARDS=WARDS)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    db = get_db()
    file = request.files.get('profile_photo')
    
    if file and file.filename:
        image_name = secure_filename(f"profile_{session['user_id']}_{datetime.now().timestamp()}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))
        db.execute("UPDATE users SET profile_photo = ? WHERE id = ?", (image_name, session['user_id']))
        db.commit()
        flash("Profile photo updated successfully!", "success")
    else:
        flash("Please select a photo to upload.", "error")
        
    return redirect(url_for('profile'))

@app.route('/profile/remove-photo', methods=['POST'])
@login_required
def remove_profile_photo():
    db = get_db()
    user_id = session['user_id']
    user = db.execute("SELECT profile_photo FROM users WHERE id = ?", (user_id,)).fetchone()
    
    if user and user['profile_photo']:
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], user['profile_photo'])
        if os.path.exists(photo_path):
            os.remove(photo_path)
            
        db.execute("UPDATE users SET profile_photo = NULL WHERE id = ?", (user_id,))
        db.commit()
        flash("Profile photo removed successfully.", "success")
        
    return redirect(url_for('profile'))

@app.route('/profile/delete', methods=['POST'])
@login_required
def delete_account():
    db = get_db()
    user_id = session['user_id']
    
    user = db.execute("SELECT profile_photo FROM users WHERE id = ?", (user_id,)).fetchone()
    if user and user['profile_photo']:
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], user['profile_photo'])
        if os.path.exists(photo_path):
            os.remove(photo_path)
            
    db.execute("DELETE FROM requests WHERE user_id = ?", (user_id,))
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    
    db.commit()
    session.clear()
    flash("Your account has been permanently deleted.", "success")
    return redirect(url_for('index'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    db = get_db()
    all_reqs = db.execute("SELECT r.*, u.full_name, u.phone FROM requests r JOIN users u ON r.user_id = u.id ORDER BY r.id DESC").fetchall()
    
    total_count = db.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
    resolved = db.execute("SELECT COUNT(*) FROM requests WHERE status='Resolved'").fetchone()[0]
    pending = db.execute("SELECT COUNT(*) FROM requests WHERE status='Pending'").fetchone()[0]
    progress = db.execute("SELECT COUNT(*) FROM requests WHERE status='In Progress'").fetchone()[0]
    user_count = db.execute("SELECT COUNT(*) FROM users WHERE is_admin = 0").fetchone()[0]
    
    stats = {'total': total_count, 'pending': pending, 'progress': progress, 'resolved': resolved, 'users': user_count}
    return render_template('admin.html', requests=all_reqs, stats=stats)

@app.route('/admin/users')
@admin_required
def admin_users():
    db = get_db()
    users = db.execute("SELECT * FROM users WHERE is_admin = 0 ORDER BY id DESC").fetchall()
    return render_template('users.html', users=users)

@app.route('/admin/update/<int:id>', methods=['POST'])
@admin_required
def update_status(id):
    db = get_db()
    db.execute("UPDATE requests SET status = ?, admin_note = ?, timeline = ? WHERE id = ?", 
               (request.form['status'], request.form['admin_note'], request.form.get('timeline', ''), id))
    db.commit()
    flash("Request updated successfully.", "success")
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)