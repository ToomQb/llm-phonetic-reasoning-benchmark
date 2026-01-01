from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from utils.decorators import admin_required 
from models import db, Dataset, DatasetSample
from services.dataset_loader import DatasetLoader

datasets_bp = Blueprint('datasets', __name__)

@datasets_bp.route('/admin/datasets')
@admin_required
def admin_datasets():
    """Page de gestion des datasets"""
    datasets = Dataset.query.all()
   
    stats = {
        'total_datasets': len(datasets),
        'total_samples': sum(d.total_samples for d in datasets),
        'categories': {}
    }
   
    for ds in datasets:
        cat = ds.category or 'unknown'
        stats['categories'][cat] = stats['categories'].get(cat, 0) + 1
   
    return render_template('admin_datasets.html', datasets=datasets, stats=stats)

@datasets_bp.route('/admin/datasets/load', methods=['POST'])
@admin_required
def load_datasets():
    """Charge les datasets depuis Hugging Face"""
    max_samples = request.form.get('max_samples', type=int)
    dataset_name = request.form.get('dataset_name', 'all')
   
    loader = DatasetLoader(db)
   
    try:
        if dataset_name == 'all':
            results = loader.load_all_datasets(max_samples)
            success_count = sum(1 for r in results.values() if r.get('success'))
            flash(f'{success_count} datasets chargés avec succès !', 'success')
        else:
            if dataset_name == 'ProntoQA':
                result = loader.load_prontoqa(max_samples)
            elif dataset_name == 'FOLIO':
                result = loader.load_folio(max_samples)
            elif dataset_name == 'LogiQA':
                result = loader.load_logiqa(max_samples)
            elif dataset_name == 'GSM8K':
                result = loader.load_gsm8k(max_samples)
            else:
                flash('Dataset inconnu', 'danger')
                return redirect(url_for('datasets.admin_datasets'))
           
            if result.get('success'):
                flash(f'{dataset_name} chargé : {result["count"]} échantillons', 'success')
            else:
                flash(f'Erreur : {result.get("message", result.get("error"))}', 'warning')
       
    except Exception as e:
        flash(f'Erreur lors du chargement : {str(e)}', 'danger')
   
    return redirect(url_for('datasets.admin_datasets'))

@datasets_bp.route('/admin/datasets/<int:dataset_id>/delete', methods=['POST'])
@admin_required
def delete_dataset(dataset_id):
    """Supprime un dataset et tous ses échantillons"""
    dataset = Dataset.query.get_or_404(dataset_id)
   
    DatasetSample.query.filter_by(dataset_id=dataset_id).delete()
    db.session.delete(dataset)
    db.session.commit()
   
    flash(f'Dataset {dataset.name} supprimé avec succès', 'success')
    return redirect(url_for('datasets.admin_datasets'))

@datasets_bp.route('/datasets')
@login_required
def view_datasets():
    """Page publique pour voir les datasets disponibles"""
    datasets = Dataset.query.all()
    return render_template('datasets.html', datasets=datasets)

@datasets_bp.route('/datasets/<int:dataset_id>')
@login_required
def dataset_detail(dataset_id):
    """Détail d'un dataset avec ses échantillons"""
    dataset = Dataset.query.get_or_404(dataset_id)
    page = request.args.get('page', 1, type=int)
   
    samples = DatasetSample.query.filter_by(dataset_id=dataset_id)\
        .paginate(page=page, per_page=20, error_out=False)
   
    return render_template('dataset_detail.html', dataset=dataset, samples=samples)

@datasets_bp.route('/evaluate/from_dataset/<int:sample_id>')
@login_required
def evaluate_from_dataset(sample_id):
    """Pré-remplit le formulaire d'évaluation avec un échantillon du dataset"""
    sample = DatasetSample.query.get_or_404(sample_id)
   
    return render_template('evaluate.html',
                         prefill_question= sample.context + "\n " + sample.question,
                         prefill_answer=sample.answer,
                         prefill_dataset=sample.dataset.name)

@datasets_bp.route('/api/sample/<int:sample_id>')
@login_required
def api_get_sample(sample_id):
    """API pour récupérer les détails d'un échantillon de dataset"""
    try:
        sample = DatasetSample.query.get_or_404(sample_id)
       
        return jsonify({
            'id': sample.id,
            'sample_id': sample.sample_id,
            'question': sample.question,
            'context': sample.context or '',
            'answer': sample.answer or '',
            'full_solution': sample.full_solution or '',
            'category': sample.category or '',
            'dataset_id': sample.dataset_id,
            'dataset_name': sample.dataset.name if sample.dataset else '',
            'created_at': sample.created_at.isoformat() if sample.created_at else ''
        })
       
    except Exception as e:
        print(f"Erreur API sample {sample_id}: {str(e)}")
        return jsonify({
            'error': 'Erreur lors du chargement de l\'échantillon',
            'details': str(e)
        }), 500