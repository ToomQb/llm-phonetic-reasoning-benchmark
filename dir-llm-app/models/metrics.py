from datetime import datetime
from . import db

class ScientificMetric(db.Model):
    """Métriques scientifiques (Precision, Recall, F1)"""
    id = db.Column(db.Integer, primary_key=True)
   
    # Métadonnées
    experiment_name = db.Column(db.String(100), nullable=False)
    dataset_name = db.Column(db.String(100))
    judge_model = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
   
    # Confusion Matrix
    true_positives = db.Column(db.Integer, default=0)
    true_negatives = db.Column(db.Integer, default=0)
    false_positives = db.Column(db.Integer, default=0)
    false_negatives = db.Column(db.Integer, default=0)
   
    # Métriques calculées
    precision = db.Column(db.Float)
    recall = db.Column(db.Float)
    f1_score = db.Column(db.Float)
    accuracy = db.Column(db.Float)
   
    def calculate_metrics(self):
        """Calcule les métriques à partir de la confusion matrix"""
        tp, tn, fp, fn = self.true_positives, self.true_negatives, self.false_positives, self.false_negatives
       
        # Precision
        self.precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
       
        # Recall
        self.recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
       
        # F1
        if self.precision + self.recall > 0:
            self.f1_score = 2 * (self.precision * self.recall) / (self.precision + self.recall)
        else:
            self.f1_score = 0.0
       
        # Accuracy
        total = tp + tn + fp + fn
        self.accuracy = (tp + tn) / total if total > 0 else 0.0
   
    def to_dict(self):
        return {
            'experiment_name': self.experiment_name,
            'precision': round(self.precision, 3) if self.precision else 0,
            'recall': round(self.recall, 3) if self.recall else 0,
            'f1_score': round(self.f1_score, 3) if self.f1_score else 0,
            'accuracy': round(self.accuracy, 3) if self.accuracy else 0,
            'tp': self.true_positives,
            'tn': self.true_negatives,
            'fp': self.false_positives,
            'fn': self.false_negatives
        }

def run_benchmark_experiment():
    """Lancer une expérience benchmark complète (utilisée en CLI)"""
    from .evaluation import Evaluation
    from .annotation import HumanAnnotation
    from datetime import datetime
    print("\n=== BENCHMARK EXPERIMENT ===")
       
    # Vérifier qu'on a des annotations
    annotation_count = HumanAnnotation.query.count()
    print(f"Annotations disponibles: {annotation_count}")
       
    if annotation_count < 10:
        print("Pas assez d'annotations (minimum 10)")
        return
       
    # Créer une métrique
    pairs = db.session.query(Evaluation, HumanAnnotation)\
        .join(HumanAnnotation, Evaluation.id == HumanAnnotation.evaluation_id)\
        .all()
       
    tp = tn = fp = fn = 0
       
    for evaluation, annotation in pairs:
        if evaluation.is_illusory and annotation.is_illusory:
            tp += 1
        elif not evaluation.is_illusory and not annotation.is_illusory:
            tn += 1
        elif evaluation.is_illusory and not annotation.is_illusory:
            fp += 1
        else:
            fn += 1
       
    metric = ScientificMetric(
        experiment_name='Benchmark_CLI',
        dataset_name='all',
        judge_model='gemini-2.5-flash',
        true_positives=tp,
        true_negatives=tn,
        false_positives=fp,
        false_negatives=fn
    )
       
    metric.calculate_metrics()
    db.session.add(metric)
    db.session.commit()
       
    print(f"\n RÉSULTATS:")
    print(f" Precision: {metric.precision:.3f}")
    print(f" Recall: {metric.recall:.3f}")
    print(f" F1-Score: {metric.f1_score:.3f}")
    print(f" Accuracy: {metric.accuracy:.3f}")