from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from utils.decorators import admin_required 
from models import db, Evaluation, HumanAnnotation, ScientificMetric
from datetime import datetime

scientific_bp = Blueprint('scientific', __name__)

@scientific_bp.route('/scientific/experiments')
@admin_required
def scientific_experiments():
    """Liste des expériences scientifiques"""
    metrics = ScientificMetric.query.order_by(ScientificMetric.created_at.desc()).all()
   
    return render_template('scientific_experiments.html', today=datetime.now(), metrics=metrics)

@scientific_bp.route('/scientific/run_experiment', methods=['POST'])
@admin_required
def run_experiment():
    """Lancer une expérience de validation"""
    experiment_name = request.form.get('experiment_name', f'Experiment_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}')
    dataset_name = request.form.get('dataset_name')
   
    try:
        query = db.session.query(Evaluation, HumanAnnotation)\
            .join(HumanAnnotation, Evaluation.id == HumanAnnotation.evaluation_id)
       
        if dataset_name and dataset_name != 'all':
            query = query.filter(Evaluation.dataset_name == dataset_name)
       
        pairs = query.all()
       
        if len(pairs) < 5:
            flash(f'Pas assez de données annotées (minimum 5, trouvé {len(pairs)})', 'warning')
            return redirect(url_for('scientific.scientific_experiments'))
       
        tp = tn = fp = fn = 0
       
        for evaluation, annotation in pairs:
            gemini_says_illusory = evaluation.is_illusory
            human_says_illusory = annotation.is_illusory
           
            if gemini_says_illusory and human_says_illusory:
                tp += 1
            elif not gemini_says_illusory and not human_says_illusory:
                tn += 1
            elif gemini_says_illusory and not human_says_illusory:
                fp += 1
            elif not gemini_says_illusory and human_says_illusory:
                fn += 1
       
        metric = ScientificMetric(
            experiment_name=experiment_name,
            dataset_name=dataset_name or 'all',
            judge_model='gemini-2.5-flash',
            true_positives=tp,
            true_negatives=tn,
            false_positives=fp,
            false_negatives=fn
        )
       
        metric.calculate_metrics()
        db.session.add(metric)
        db.session.commit()
       
        flash(f'Expérience terminée ! F1-Score: {metric.f1_score:.3f}', 'success')
        return redirect(url_for('scientific.view_experiment', metric_id=metric.id))
       
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de l\'expérience: {str(e)}', 'danger')
        return redirect(url_for('scientific.scientific_experiments'))

@scientific_bp.route('/scientific/experiment/<int:metric_id>')
@admin_required
def view_experiment(metric_id):
    """Voir les détails d'une expérience"""
    metric = ScientificMetric.query.get_or_404(metric_id)
   
    total = metric.true_positives + metric.true_negatives + metric.false_positives + metric.false_negatives
   
    stats = {
        'total_samples': total,
        'illusory_rate': (metric.true_positives + metric.false_negatives) / total if total > 0 else 0,
        'agreement_rate': (metric.true_positives + metric.true_negatives) / total if total > 0 else 0
    }
   
    return render_template('view_experiment.html', metric=metric, stats=stats)

@scientific_bp.route('/scientific/export/<int:metric_id>')
@admin_required
def export_experiment(metric_id):
    """Exporter les résultats en JSON"""
    metric = ScientificMetric.query.get_or_404(metric_id)
   
    data = metric.to_dict()
    data['created_at'] = metric.created_at.isoformat()
   
    return jsonify(data)