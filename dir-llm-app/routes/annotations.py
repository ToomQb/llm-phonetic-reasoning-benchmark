from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Evaluation, HumanAnnotation, IllusionType
import time

annotations_bp = Blueprint('annotations', __name__)

@annotations_bp.route('/annotate')
@login_required
def annotate_list():
    """Liste des évaluations à annoter"""
    page = request.args.get('page', 1, type=int)
   
    annotated_ids = db.session.query(HumanAnnotation.evaluation_id)\
        .filter(HumanAnnotation.annotator_id == current_user.id)\
        .subquery()
   
    evaluations = Evaluation.query\
        .filter_by(user_id=current_user.id)\
        .filter(~Evaluation.id.in_(annotated_ids))\
        .order_by(Evaluation.created_at.desc())\
        .paginate(page=page, per_page=20, error_out=False)
   
    total_annotations = HumanAnnotation.query.filter_by(annotator_id=current_user.id).count()
   
    return render_template('annotate_list.html',
                         evaluations=evaluations,
                         total_annotations=total_annotations)

@annotations_bp.route('/annotate/<int:eval_id>', methods=['GET', 'POST'])
@login_required
def annotate_evaluation(eval_id):
    """Annoter une évaluation spécifique"""
    evaluation = Evaluation.query.get_or_404(eval_id)
   
    existing = HumanAnnotation.query.filter_by(
        evaluation_id=eval_id,
        annotator_id=current_user.id
    ).first()
   
    if request.method == 'POST':
        start_time = request.form.get('start_time', type=int)
        current_time = int(time.time())
        annotation_time = current_time - start_time if start_time else 0
       
        is_illusory = request.form.get('is_illusory') == 'true'
        illusion_types = request.form.getlist('illusion_types')
        explanation = request.form.get('explanation', '')
        confidence = float(request.form.get('confidence', 0.5))
       
        if existing:
            existing.is_illusory = is_illusory
            existing.set_illusion_types(illusion_types)
            existing.explanation = explanation
            existing.confidence = confidence
            existing.annotation_time_seconds = annotation_time
        else:
            annotation = HumanAnnotation(
                evaluation_id=eval_id,
                annotator_id=current_user.id,
                is_illusory=is_illusory,
                explanation=explanation,
                confidence=confidence,
                annotation_time_seconds=annotation_time
            )
            annotation.set_illusion_types(illusion_types)
            db.session.add(annotation)
       
        db.session.commit()
        flash('Annotation enregistrée avec succès !', 'success')
        return redirect(url_for('annotations.annotate_list'))
   
    illusion_types_list = IllusionType.query.all()
   
    return render_template('annotate_form.html',
                         evaluation=evaluation,
                         existing=existing,
                         illusion_types=illusion_types_list,
                         start_time=int(time.time()))

@annotations_bp.route('/annotations/my')
@login_required
def my_annotations():
    """Mes annotations"""
    page = request.args.get('page', 1, type=int)
   
    annotations = HumanAnnotation.query\
        .filter_by(annotator_id=current_user.id)\
        .order_by(HumanAnnotation.created_at.desc())\
        .paginate(page=page, per_page=20, error_out=False)
   
    return render_template('my_annotations.html', annotations=annotations)

@annotations_bp.route('/annotations/<int:annotation_id>/delete', methods=['POST'])
@login_required
def delete_annotation(annotation_id):
    """Supprimer une annotation"""
    annotation = HumanAnnotation.query.get_or_404(annotation_id)
   
    if annotation.annotator_id != current_user.id and not current_user.is_admin:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('annotations.my_annotations'))
   
    db.session.delete(annotation)
    db.session.commit()
   
    flash('Annotation supprimée', 'success')
    return redirect(url_for('annotations.my_annotations'))