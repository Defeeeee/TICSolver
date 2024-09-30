import json
import os
import re
import tempfile
from datetime import datetime, timedelta
from random import randint

import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_apscheduler import APScheduler
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

import TICSolver
from models import db, User, History

from flask_dance.contrib.google import make_google_blueprint, google

# Fetch Google credentials and Mailgun API key from environment variables
google_client_id = os.environ.get('GOOGLE_ID')
google_client_secret = os.environ.get('GOOGLE_SECRET')
db_credentials = os.environ.get('db_postgres')
mailgun_api_key = os.environ.get('MAILGUN_API_KEY')

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
    'SQLALCHEMY_DATABASE_URI'] = db_credentials
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

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


@scheduler.task('interval', id='delete_unverified_users', minutes=30)
def delete_unverified_users():
    with app.app_context():
        thirty_minutes_ago = datetime.utcnow() - timedelta(minutes=30)
        unverified_users = User.query.filter_by(email_verified=False, registered_with_google=False).filter(
            User.timestamp < thirty_minutes_ago).all()
        for user in unverified_users:
            db.session.delete(user)
        db.session.commit()


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
    try:
        user = User.query.filter_by(email=google_info['email']).first()
    except OperationalError as e:
        # Handle the OperationalError (e.g., retry, log the error, show a user-friendly message)
        db.session.rollback()  # Rollback the transaction in case of an error
        flash('Error temporal en la base de datos. Por favor, inténtalo de nuevo.', 'error')
        return redirect(url_for('login'))
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
    if current_user.is_authenticated:
        user_history = History.query.filter_by(user_id=current_user.id).all()
    else:
        user_history = None
    return render_template('upload.html', history=user_history)


@app.route('/history/show/<int:history_id>')
@login_required
def view_history(history_id):
    history_entry = History.query.get_or_404(history_id)

    # Authorization check: Ensure the history entry belongs to the current user
    if history_entry.user_id != current_user.id:
        flash('No tienes permiso para ver este historial.', 'error')  # Or handle this differently
        return redirect(url_for('history'))  # Redirect to the user's own history page

    results = json.loads(history_entry.result)
    return render_template('history_details.html', results=results, filename=history_entry.file_name)


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


def send_simple_message(to, subject, text):
    api_key = os.environ.get('MAILGUN_API_KEY')
    domain_name = 'ts.fdiaznem.me'
    return requests.post(
        f"https://api.mailgun.net/v3/{domain_name}/messages",
        auth=("api", api_key),
        data={"from": f"TICSolver <mailgun@{domain_name}>",
              "to": [to],
              "subject": subject,
              "text": text})


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
            flash('Las  contraseñas no coinciden', 'error')
            return redirect(url_for('register'))

        if len(password) < 10:
            flash('La contraseña debe tener al menos 10 caracteres.', 'error')
            return redirect(url_for('register'))

        if not re.search("[a-z]", password) or \
                not re.search("[A-Z]", password) or \
                not re.search("[0-9]", password) or \
                not re.search("[!@#$%^&*()_+=[{};':\"\\|,.<>/?]", password):  
            flash(
                'La contraseña debe contener al menos una letra mayúscula, una letra minúscula, un número y un símbolo.',
                'error')
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

            # Generate verification code
            verification_code = str(randint(100000, 999999))

            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(
                username=username,
                password=hashed_password,  

                first_name=first_name,
                last_name=last_name,
                email=email,
                verification_code=verification_code
            )
            db.session.add(new_user)
            db.session.commit()

            # Send verification email using Mailgun
            subject = 'Verificación de correo electrónico'
            text = f'Tu código de verificación es: {verification_code}'
            send_simple_message(to=email, subject=subject, text=text)

            flash('¡Registro exitoso! Por favor, verifica tu correo electrónico.', 'success')
            return redirect(url_for('verify_email')) 

        except SQLAlchemyError as e:
            db.session.rollback()
            flash('Error al registrar el usuario. Por favor, inténtalo de nuevo.', 'error')
            return redirect(url_for('register'))

    else:  # Handle GET requests
        return render_template('register.html') 

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and not user.registered_with_google and check_password_hash(user.password, password):
            if user.email_verified:  # Check if email is verified
                login_user(user)
                return redirect(url_for('ticsolver'))
            else:
                flash('Por favor, verifica tu correo electrónico para iniciar sesión.', 'error')
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

@app.route('/verify_email', methods=['GET', 'POST'])
def verify_email():
    if current_user.is_authenticated and current_user.email_verified:
        return redirect(url_for('ticsolver'))

    if request.method == 'POST':
        code = request.form['verification_code']

        # Find the user with the matching verification code
        user = User.query.filter_by(verification_code=code).first()

        if user:
            user.email_verified = True
            user.verification_code = None  # Clear the verification code after successful verification
            db.session.commit()
            flash('¡Correo electrónico verificado exitosamente! Ahora puedes iniciar sesión.', 'success')

            if not current_user.is_authenticated:
                login_user(user)

            return redirect(url_for('login'))  # Or redirect to another appropriate page
        else:
            flash('Código de verificación inválido. Por favor, inténtalo de nuevo.', 'error')

    return render_template('verify_email.html')

if __name__ == '__main__':
    app.run(debug=True)