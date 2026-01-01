from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from models.user import User  
from models import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    """Page d'accueil"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Inscription utilisateur"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
   
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
       
        # Validations
        if not all([username, email, password, confirm_password]):
            flash('Tous les champs sont requis', 'danger')
            return redirect(url_for('auth.register'))
       
        if password != confirm_password:
            flash('Les mots de passe ne correspondent pas', 'danger')
            return redirect(url_for('auth.register'))
       
        if len(password) < 6:
            flash('Le mot de passe doit contenir au moins 6 caractères', 'danger')
            return redirect(url_for('auth.register'))
       
        # Vérifier si l'utilisateur existe
        if User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur est déjà pris', 'danger')
            return redirect(url_for('auth.register'))
       
        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé', 'danger')
            return redirect(url_for('auth.register'))
       
        # Créer l'utilisateur
        user = User(username=username, email=email)
        user.set_password(password)
       
        # Premier utilisateur = admin
        if User.query.count() == 0:
            user.is_admin = True
       
        db.session.add(user)
        db.session.commit()
       
        flash('Compte créé avec succès ! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('auth.login'))
   
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Connexion utilisateur"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
   
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
       
        user = User.query.filter_by(username=username).first()
       
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f'Bienvenue, {user.username} !', 'success')
           
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('Identifiants incorrects', 'danger')
   
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Déconnexion"""
    logout_user()
    flash('Vous êtes déconnecté', 'info')
    return redirect(url_for('auth.index'))