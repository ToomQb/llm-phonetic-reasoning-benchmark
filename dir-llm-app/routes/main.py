from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Evaluation
from services import gemini_judge  
from models.user import User 

main_bp = Blueprint('main', __name__)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Tableau de bord principal"""
    # Statistiques utilisateur
    total_evaluations = Evaluation.query.filter_by(user_id=current_user.id).count()
    illusory_count = Evaluation.query.filter_by(user_id=current_user.id, is_illusory=True).count()
   
    recent_evaluations = Evaluation.query.filter_by(user_id=current_user.id)\
        .order_by(Evaluation.created_at.desc()).limit(5).all()
   
    # Statistiques globales (admin)
    global_stats = None
    if current_user.is_admin:
        global_stats = {
            'total_users': User.query.count(),
            'total_evaluations': Evaluation.query.count(),
            'total_illusory': Evaluation.query.filter_by(is_illusory=True).count()
        }
   
    return render_template('dashboard.html',
                         total_evaluations=total_evaluations,
                         illusory_count=illusory_count,
                         recent_evaluations=recent_evaluations,
                         global_stats=global_stats)

@main_bp.route('/evaluate', methods=['GET', 'POST'])
@login_required
def evaluate():
    """Page d'évaluation de raisonnement"""
    if request.method == 'POST':
        question = request.form.get('question')
        llm_response = request.form.get('llm_response')
        expected_answer = request.form.get('expected_answer')
        dataset_name = request.form.get('dataset_name', 'Custom')
       
        if not question or not llm_response:
            flash('La question et la réponse sont requises', 'danger')
            return redirect(url_for('main.evaluate'))
       
        # Évaluation avec Gemini
        try:
            result = gemini_judge.evaluate_reasoning(question, llm_response, expected_answer)
           
            # Sauvegarder en base
            evaluation = Evaluation(
                user_id=current_user.id,
                question=question,
                llm_response=llm_response,
                expected_answer=expected_answer,
                dataset_name=dataset_name,
                is_illusory=result['is_illusory'],
                explanation=result['explanation'],
                confidence=result['confidence']
            )
            evaluation.set_illusion_types(result['illusion_types'])
           
            db.session.add(evaluation)
            db.session.commit()
           
            flash('Évaluation terminée !', 'success')
            return redirect(url_for('main.evaluation_detail', eval_id=evaluation.id))
           
        except Exception as e:
            flash(f'Erreur lors de l\'évaluation: {str(e)}', 'danger')
            return redirect(url_for('main.evaluate'))
   
    return render_template('evaluate.html')

@main_bp.route('/evaluation/<int:eval_id>')
@login_required
def evaluation_detail(eval_id):
    """Détail d'une évaluation"""
    evaluation = Evaluation.query.get_or_404(eval_id)
   
    # Vérifier que l'utilisateur peut voir cette évaluation
    if evaluation.user_id != current_user.id and not current_user.is_admin:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.dashboard'))
   
    return render_template('evaluation_detail.html', evaluation=evaluation)

@main_bp.route('/history')
@login_required
def history():
    """Historique des évaluations"""
    page = request.args.get('page', 1, type=int)
   
    evaluations = Evaluation.query.filter_by(user_id=current_user.id)\
        .order_by(Evaluation.created_at.desc())\
        .paginate(page=page, per_page=20, error_out=False)
   
    return render_template('history.html', evaluations=evaluations)

@main_bp.route('/statistics')
@login_required
def statistics():
    """Page de statistiques"""
    user_evals = Evaluation.query.filter_by(user_id=current_user.id).all()
   
    if not user_evals:
        flash('Aucune évaluation disponible', 'info')
        return redirect(url_for('main.dashboard'))
   
    # Calculer les statistiques
    total = len(user_evals)
    illusory = sum(1 for e in user_evals if e.is_illusory)
   
    # Distribution des types d'illusions
    illusion_dist = {}
    for eval in user_evals:
        for itype in eval.get_illusion_types():
            illusion_dist[itype] = illusion_dist.get(itype, 0) + 1
   
    stats = {
        'total': total,
        'illusory': illusory,
        'valid': total - illusory,
        'illusion_rate': (illusory / total * 100) if total > 0 else 0,
        'avg_confidence': sum(e.confidence for e in user_evals) / total if total > 0 else 0,
        'illusion_distribution': illusion_dist
    }
   
    return render_template('statistics.html', stats=stats)

@main_bp.route('/delete_evaluation/<int:eval_id>', methods=['POST'])
@login_required
def delete_evaluation(eval_id):
    """Supprimer une évaluation"""
    from models.analysis import ConsistencyCheck, LogicalAnalysis 
    from models.annotation import HumanAnnotation 
    evaluation = Evaluation.query.get_or_404(eval_id)
   
    if evaluation.user_id != current_user.id and not current_user.is_admin:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.dashboard'))
   
    try:
        # Suppression manuelle des enregistrements liés
        ConsistencyCheck.query.filter_by(evaluation_id=eval_id).delete()
        LogicalAnalysis.query.filter_by(evaluation_id=eval_id).delete()
        HumanAnnotation.query.filter_by(evaluation_id=eval_id).delete()
        db.session.delete(evaluation)
        db.session.commit()
        flash('Évaluation supprimée avec succès', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Erreur suppression évaluation {eval_id}: {str(e)}")
        flash(f'Erreur lors de la suppression: {str(e)}', 'danger')
   
    return redirect(url_for('main.history'))