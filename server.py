import os
import json
import tempfile
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash

import TICSolver
from models import db, User, History

from flask_dance.contrib.google import make_google_blueprint, google

# Fetch Google credentials from environment variables
google_client_id = os.environ.get('GOOGLE_ID')
google_client_secret = os.environ.get('GOOGLE_SECRET')

blueprint = make_google_blueprint(
    client_id=google_client_id,
    client_secret=google_client_secret,
    scope=[
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
        "openid"
    ],
    redirect_to="google_authorized"
)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
app.config[
    'SQLALCHEMY_DATABASE_URI'] = "postgresql://default:JdcNLQ8b5xyY@ep-shiny-surf-a4imudfy-pooler.us-east-1.aws.neon.tech:5432/verceldb?sslmode=require"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.urandom(24)

db.init_app(app)

# Create database tables if they don't exist
with app.app_context():
    db.create_all()

app.register_blueprint(blueprint, url_prefix="/login")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/login/google_authorized")
def google_authorized():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    assert resp.ok, resp.text
    google_info = resp.json()

    # Check if user exists, if not create one (excluding 'password')
    user = User.query.filter_by(email=google_info['email']).first()
    if not user:
        user = User(
            username=google_info['name'],
            first_name=google_info['name'],
            email=google_info['email'],
            registered_with_google=True
        )
        db.session.add(user)

    # Debugging: Print the SQL query and user data before committing
    print(user.__table__.insert().compile().string)
    print(user.__dict__)

    db.session.commit()

    login_user(user)
    return redirect(url_for("ticsolver"))


@app.route('/favicon.ico')
def favicon():
    return redirect(url_for('static', filename='favicon.ico'))


@app.route('/', methods=['GET', 'POST'])
def ticsolver():
    return render_template('upload.html')


@app.route('/results', methods=['POST'])
@login_required
def results():
    if request.method == 'POST':
        try:
            file = request.files['file']
            if not file.filename.lower().endswith('.html'):
                return render_template('error.html', error="Error: El archivo no es un archivo HTML.", isNotFound=True)
            if file:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(file_path)

                rowpag_data = TICSolver.extract_html_data(file_path)
                os.remove(file_path)
                if rowpag_data:
                    correct_answers = TICSolver.extract_correct_answers(rowpag_data)
                    history_entry = History(user_id=current_user.id, file_name=file.filename,
                                            result=json.dumps(correct_answers))
                    db.session.add(history_entry)
                    db.session.commit()
                    return render_template('results.html', answers=correct_answers)
                else:
                    return "Error: No data extracted from the file."
            else:
                return "Error: No file uploaded."
        except Exception as e:
            return render_template('error.html', isNotFound=("codec can't decode" in str(e)))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']

        confirm_password = request.form['confirm_password']

        # Check if passwords match
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return redirect(url_for('register'))

        try:
            # Check if email already exists
            existing_user_email = User.query.filter_by(email=email).first()
            if existing_user_email:
                flash('El correo electrónico ya está registrado', 'error')
                return redirect(url_for('register'))

            # Check if username already exists
            existing_user_username = User.query.filter_by(username=username).first()
            if existing_user_username:
                flash('El nombre de usuario ya está en uso', 'error')
                return redirect(url_for('register'))

            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(
                username=username,
                password=hashed_password,

                first_name=first_name,
                last_name=last_name,
                email=email
            )
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))


        except SQLAlchemyError as e:
            db.session.rollback()
            flash('Error al registrar el usuario. Por favor, inténtalo de nuevo.', 'error')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and not user.registered_with_google and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('ticsolver'))
        else:
            flash('Invalid username or password or you registered with Google', 'error')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('ticsolver'))


@app.route('/history')
@login_required
def history():
    user_history = History.query.filter_by(user_id=current_user.id).all()
    return render_template('history.html', history=user_history)


if __name__ == '__main__':
    app.run(debug=True)
