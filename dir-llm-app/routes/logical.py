from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Evaluation, LogicalAnalysis
from services import logical_analyzer
import json

logical_bp = Blueprint('logical', __name__)

@logical_bp.route('/logical/analyze/<int:eval_id>', methods=['POST'])
@login_required
def analyze_logical(eval_id):
    """Analyser la logique d'une évaluation"""
    evaluation = Evaluation.query.get_or_404(eval_id)
   
    if evaluation.user_id != current_user.id and not current_user.is_admin:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.dashboard'))
   
    try:
        result = logical_analyzer.analyze(evaluation.llm_response)
       
        analysis = LogicalAnalysis(
            evaluation_id=eval_id,
            has_contradiction=result['has_contradiction'],
            has_circular_reasoning=result['has_circular_reasoning'],
            has_invalid_quantifier=result['has_invalid_quantifier'],
            contradictions_found=json.dumps(result['contradictions_found']),
            circular_patterns=json.dumps(result['circular_patterns']),
            logical_errors=json.dumps(result['logical_errors'])
        )
       
        db.session.add(analysis)
        db.session.commit()
       
        errors_found = sum([
            result['has_contradiction'],
            result['has_circular_reasoning'],
            result['has_invalid_quantifier']
        ])
       
        flash(f'Analyse terminée ! {errors_found} erreur(s) détectée(s)',
              'warning' if errors_found > 0 else 'success')
       
        return redirect(url_for('logical.view_logical_analysis', analysis_id=analysis.id))
       
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('main.evaluation_detail', eval_id=eval_id))

@logical_bp.route('/logical/<int:analysis_id>')
@login_required
def view_logical_analysis(analysis_id):
    """Voir les résultats d'une analyse logique"""
    analysis = LogicalAnalysis.query.get_or_404(analysis_id)
   
    if analysis.evaluation.user_id != current_user.id and not current_user.is_admin:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.dashboard'))
   
    contradictions = json.loads(analysis.contradictions_found)
    circular_patterns = json.loads(analysis.circular_patterns)
    logical_errors = json.loads(analysis.logical_errors)
   
    return render_template('view_logical_analysis.html',
                         analysis=analysis,
                         contradictions=contradictions,
                         circular_patterns=circular_patterns,
                         logical_errors=logical_errors)