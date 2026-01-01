from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from utils.decorators import admin_required 
from models import db, User, Dataset, IllusionType 

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
@admin_required
def admin_panel():
    """Panel d'administration"""
    users = User.query.all()
    datasets = Dataset.query.all()
   
    return render_template('admin.html', users=users, datasets=datasets)

@admin_bp.route('/admin/users')
@admin_required
def admin_users():
    """Gestion des utilisateurs"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', users=users)

@admin_bp.route('/admin/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user_details(user_id):
    """Récupérer les détails d'un utilisateur pour modification"""
    user = User.query.get_or_404(user_id)
   
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_admin': user.is_admin,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'evaluation_count': len(user.evaluations),
        'annotation_count': len(user.annotations)
    })

@admin_bp.route('/admin/users/<int:user_id>/update', methods=['POST'])
@admin_required
def update_user(user_id):
    """Mettre à jour un utilisateur"""
    try:
        user = User.query.get_or_404(user_id)
       
        if user.id == current_user.id:
            if not request.form.get('is_admin') and User.query.filter_by(is_admin=True).count() <= 1:
                flash('Impossible de retirer les droits admin : au moins un admin est requis', 'danger')
                return redirect(url_for('admin.admin_users'))
       
        username = request.form.get('username')
        email = request.form.get('email')
        is_admin = request.form.get('is_admin') == 'true'
        new_password = request.form.get('new_password')
       
        if not username or not email:
            flash('Nom d\'utilisateur et email sont requis', 'danger')
            return redirect(url_for('admin.admin_users'))
       
        existing_user = User.query.filter(
            User.username == username,
            User.id != user_id
        ).first()
        if existing_user:
            flash('Ce nom d\'utilisateur est déjà utilisé', 'danger')
            return redirect(url_for('admin.admin_users'))
       
        existing_email = User.query.filter(
            User.email == email,
            User.id != user_id
        ).first()
        if existing_email:
            flash('Cet email est déjà utilisé', 'danger')
            return redirect(url_for('admin.admin_users'))
       
        user.username = username
        user.email = email
        user.is_admin = is_admin
       
        if new_password:
            if len(new_password) < 6:
                flash('Le mot de passe doit contenir au moins 6 caractères', 'danger')
                return redirect(url_for('admin.admin_users'))
            user.set_password(new_password)
       
        db.session.commit()
        flash('Utilisateur mis à jour avec succès', 'success')
       
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la mise à jour: {str(e)}', 'danger')
   
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Supprimer un utilisateur"""
    try:
        user = User.query.get_or_404(user_id)
       
        if user.id == current_user.id:
            flash('Vous ne pouvez pas supprimer votre propre compte', 'danger')
            return redirect(url_for('admin.admin_users'))
       
        if user.is_admin and User.query.filter_by(is_admin=True).count() <= 1:
            flash('Impossible de supprimer le dernier administrateur', 'danger')
            return redirect(url_for('admin.admin_users'))
       
        db.session.delete(user)
        db.session.commit()
       
        flash(f'Utilisateur {user.username} supprimé avec succès', 'success')
       
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression: {str(e)}', 'danger')
   
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/admin/users/create', methods=['POST'])
@admin_required
def create_user():
    """Créer un nouvel utilisateur"""
    try:
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_admin = request.form.get('is_admin') == 'true'
       
        if not all([username, email, password]):
            flash('Tous les champs sont requis', 'danger')
            return redirect(url_for('admin.admin_users'))
       
        if len(password) < 6:
            flash('Le mot de passe doit contenir au moins 6 caractères', 'danger')
            return redirect(url_for('admin.admin_users'))
       
        if User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur est déjà pris', 'danger')
            return redirect(url_for('admin.admin_users'))
       
        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé', 'danger')
            return redirect(url_for('admin.admin_users'))
       
        user = User(username=username, email=email, is_admin=is_admin)
        user.set_password(password)
       
        db.session.add(user)
        db.session.commit()
       
        flash(f'Utilisateur {username} créé avec succès', 'success')
       
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la création: {str(e)}', 'danger')
   
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/admin/users/<int:user_id>/evaluations')
@admin_required
def get_user_evaluations(user_id):
    """Récupérer les évaluations d'un utilisateur"""
    from models.evaluation import Evaluation 
    user = User.query.get_or_404(user_id)
    page = request.args.get('page', 1, type=int)
   
    evaluations = Evaluation.query.filter_by(user_id=user_id)\
        .order_by(Evaluation.created_at.desc())\
        .paginate(page=page, per_page=10, error_out=False)
   
    evaluations_data = [{
        'id': e.id,
        'question': e.question[:100] + '...' if len(e.question) > 100 else e.question,
        'is_illusory': e.is_illusory,
        'confidence': e.confidence,
        'created_at': e.created_at.strftime('%Y-%m-%d %H:%M'),
        'dataset_name': e.dataset_name or ''
    } for e in evaluations.items]
   
    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        },
        'evaluations': evaluations_data,
        'pagination': {
            'page': evaluations.page,
            'pages': evaluations.pages,
            'total': evaluations.total,
            'has_next': evaluations.has_next,
            'has_prev': evaluations.has_prev
        }
    })





@admin_bp.route('/admin/illusion_types')
@admin_required
def manage_illusion_types():
    """Gérer la typologie des illusions"""
    illusion_types = IllusionType.query.all()
    return render_template('manage_illusion_types.html', illusion_types=illusion_types)


@admin_bp.route('/admin/illusion_types/add', methods=['POST'])
@admin_required
def add_illusion_type():
    """Ajouter un type d'illusion"""
    name = request.form.get('name')
    description = request.form.get('description')
    example = request.form.get('example')
    category = request.form.get('category')
    
    if not name or not description:
        flash('Nom et description requis', 'danger')
        return redirect(url_for('admin.manage_illusion_types'))
    
    # Vérifier si existe déjà
    existing = IllusionType.query.filter_by(name=name).first()
    if existing:
        flash('Ce type existe déjà', 'warning')
        return redirect(url_for('admin.manage_illusion_types'))
    
    illusion_type = IllusionType(
        name=name,
        description=description,
        example=example,
        category=category
    )
    
    db.session.add(illusion_type)
    db.session.commit()
    
    flash('Type d\'illusion ajouté', 'success')
    return redirect(url_for('admin.manage_illusion_types'))


@admin_bp.route('/admin/illusion_types/<int:type_id>/delete', methods=['POST'])
@admin_required
def delete_illusion_type(type_id):
    """Supprimer un type d'illusion"""
    illusion_type = IllusionType.query.get_or_404(type_id)
    
    db.session.delete(illusion_type)
    db.session.commit()
    
    flash('Type d\'illusion supprimé', 'success')
    return redirect(url_for('admin.manage_illusion_types'))