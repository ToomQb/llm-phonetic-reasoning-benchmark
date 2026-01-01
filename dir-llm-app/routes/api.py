from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Evaluation, HumanAnnotation, IllusionType, ScientificMetric
from services import gemini_judge 

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/evaluate', methods=['POST'])
@login_required
def api_evaluate():
    """API pour évaluation rapide"""
    data = request.get_json()
   
    if not data or 'question' not in data or 'response' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
   
    try:
        result = gemini_judge.evaluate_reasoning(
            data['question'],
            data['response'],
            data.get('expected_answer')
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/stats')
@login_required
def api_stats():
    """API pour statistiques utilisateur"""
    evals = Evaluation.query.filter_by(user_id=current_user.id).all()
   
    return jsonify({
        'total': len(evals),
        'illusory': sum(1 for e in evals if e.is_illusory),
        'valid': sum(1 for e in evals if not e.is_illusory)
    })

@api_bp.route('/api/illusion_types')
@login_required
def api_illusion_types():
    """API pour récupérer la typologie"""
    types = IllusionType.query.all()
    return jsonify([t.to_dict() for t in types])

@api_bp.route('/api/metrics/summary')
@login_required
def api_metrics_summary():
    """Résumé des métriques scientifiques"""
    metrics = ScientificMetric.query.all()
   
    if not metrics:
        return jsonify({'error': 'No metrics available'}), 404
   
    summary = {
        'experiments_count': len(metrics),
        'avg_precision': sum(m.precision for m in metrics) / len(metrics),
        'avg_recall': sum(m.recall for m in metrics) / len(metrics),
        'avg_f1': sum(m.f1_score for m in metrics) / len(metrics),
        'best_f1': max(m.f1_score for m in metrics),
        'latest': metrics[-1].to_dict() if metrics else None
    }
   
    return jsonify(summary)

@api_bp.route('/api/annotations/stats')
@login_required
def api_annotation_stats():
    """Statistiques d'annotations de l'utilisateur"""
    annotations = HumanAnnotation.query.filter_by(annotator_id=current_user.id).all()
   
    if not annotations:
        return jsonify({'total': 0})
   
    stats = {
        'total': len(annotations),
        'illusory_count': sum(1 for a in annotations if a.is_illusory),
        'avg_confidence': sum(a.confidence for a in annotations) / len(annotations),
        'avg_time_seconds': sum(a.annotation_time_seconds or 0 for a in annotations) / len(annotations),
        'illusion_types_distribution': {}
    }
   
    for annotation in annotations:
        for itype in annotation.get_illusion_types():
            stats['illusion_types_distribution'][itype] = \
                stats['illusion_types_distribution'].get(itype, 0) + 1
   
    return jsonify(stats)