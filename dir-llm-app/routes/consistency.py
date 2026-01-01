from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Evaluation, ConsistencyCheck  
from services import consistency_checker
import json
import requests
from config import Config

consistency_bp = Blueprint('consistency', __name__)

@consistency_bp.route('/consistency/check/<int:eval_id>', methods=['POST'])
@login_required
def check_consistency(eval_id):
    """Vérifier la cohérence d'une évaluation"""
    evaluation = Evaluation.query.get_or_404(eval_id)
   
    if evaluation.user_id != current_user.id and not current_user.is_admin:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.dashboard'))
   
    try:
        def generate_response(question, temperature=0.7):
            prompt = f"Réponds à cette question de manière concise:\n\n{question}"
           
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": 512
                }
            }
           
            response = requests.post(Config.GEMINI_API_URL, json=payload, timeout=30)
            result = response.json()
           
            if "candidates" in result and len(result["candidates"]) > 0:
                return result["candidates"][0]["content"]["parts"][0]["text"]
           
            return "Erreur de génération"
       
        result = consistency_checker.check_consistency(
            evaluation.question,
            generate_response,
            temperature=0.7
        )
       
        consistency = ConsistencyCheck(
            evaluation_id=eval_id,
            num_samples=result['num_samples'],
            responses=json.dumps(result['responses']),
            final_answers=json.dumps(result['final_answers']),
            is_consistent=result['is_consistent'],
            inconsistency_score=result['inconsistency_score'],
            divergent_steps=json.dumps(result['divergent_steps'])
        )
       
        db.session.add(consistency)
        db.session.commit()
       
        flash(f'Vérification terminée ! Cohérence: {"✓" if result["is_consistent"] else "✗"}',
              'success' if result['is_consistent'] else 'warning')
       
        return redirect(url_for('consistency.view_consistency', consistency_id=consistency.id))
       
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('main.evaluation_detail', eval_id=eval_id))

@consistency_bp.route('/consistency/<int:consistency_id>')
@login_required
def view_consistency(consistency_id):
    """Voir les résultats d'une vérification de cohérence"""
    consistency = ConsistencyCheck.query.get_or_404(consistency_id)
   
    if consistency.evaluation.user_id != current_user.id and not current_user.is_admin:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('main.dashboard'))
   
    responses = json.loads(consistency.responses)
    final_answers = json.loads(consistency.final_answers)
    divergent_steps = json.loads(consistency.divergent_steps)
   
    return render_template('view_consistency.html',
                         consistency=consistency,
                         responses=responses,
                         final_answers=final_answers,
                         divergent_steps=divergent_steps)