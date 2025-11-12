from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import hashlib
from sqlalchemy import func

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///voting.db'
app.config['UPLOAD_FOLDER'] = 'uploads'

candidates = [
    {'name': 'Candidate A', 'image': 'https://via.placeholder.com/150/FF5733/FFFFFF?text=A'},
    {'name': 'Candidate B', 'image': 'https://via.placeholder.com/150/33FF57/FFFFFF?text=B'},
    {'name': 'Candidate C', 'image': 'https://via.placeholder.com/150/3357FF/FFFFFF?text=C'}
]

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    documents = db.relationship('Document', backref='user', lazy=True)
    votes = db.relationship('Vote', backref='user', lazy=True)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(150), nullable=False)
    hash_value = db.Column(db.String(256), nullable=False)
    verified = db.Column(db.Boolean, default=False)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    candidate = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            with open(file_path, 'rb') as f:
                hash_value = hashlib.sha256(f.read()).hexdigest()
            document = Document(user_id=current_user.id, filename=filename, hash_value=hash_value)
            db.session.add(document)
            db.session.commit()
            flash('Document uploaded and hashed')
    return render_template('upload.html')

@app.route('/verify/<int:doc_id>')
@login_required
def verify(doc_id):
    doc = Document.query.get(doc_id)
    if doc and doc.user_id == current_user.id:
        doc.verified = True
        db.session.commit()
        flash('Document verified')
    return redirect(url_for('dashboard'))

@app.route('/vote', methods=['GET', 'POST'])
@login_required
def vote():
    if request.method == 'POST':
        candidate = request.form['candidate']
        if not Vote.query.filter_by(user_id=current_user.id).first():
            vote = Vote(user_id=current_user.id, candidate=candidate)
            db.session.add(vote)
            db.session.commit()
            flash('Vote cast')
        else:
            flash('Already voted')
    return render_template('vote.html', candidates=candidates)

@app.route('/dashboard')
@login_required
def dashboard():
    documents = Document.query.filter_by(user_id=current_user.id).all()
    total_users = User.query.count()
    has_voted = Vote.query.filter_by(user_id=current_user.id).first() is not None
    return render_template('dashboard.html', documents=documents, total_users=total_users, has_voted=has_voted)

@app.route('/results')
@login_required
def results():
    vote_rows = db.session.query(Vote.candidate, func.count(Vote.id)).group_by(Vote.candidate).all()
    votes = [[row[0], row[1]] for row in vote_rows]
    total_users = User.query.count()
    total_documents = Document.query.count()
    total_votes = Vote.query.count()
    return render_template('results.html', votes=votes, total_users=total_users, total_documents=total_documents, total_votes=total_votes)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
