from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .evaluation import Evaluation
from .dataset import Dataset, DatasetSample
from .annotation import HumanAnnotation, IllusionType
from .analysis import ConsistencyCheck, LogicalAnalysis
from .metrics import ScientificMetric

__all__ = ['db', 'User', 'Evaluation', 'Dataset', 'DatasetSample', 'HumanAnnotation', 'IllusionType', 'ConsistencyCheck', 'LogicalAnalysis', 'ScientificMetric']


def init_illusion_types():
    """Initialise la typologie formelle des illusions"""
    if IllusionType.query.count() > 0:
        print("Typologie déjà initialisée")
        return
       
    
    types = [
        {
            'name': 'inference_error',
            'category': 'logical',
            'description': 'Conclusion logiquement invalide qui ne découle pas des prémisses',
            'example': 'Tous les A sont B, donc tous les B sont A'
        },
        {
            'name': 'contradiction',
            'category': 'logical',
            'description': 'Affirmations contradictoires dans le même raisonnement',
            'example': 'X est vrai et X est faux'
        },
        {
            'name': 'false_causality',
            'category': 'causal',
            'description': 'Attribution incorrecte de relation causale entre événements',
            'example': 'A précède B, donc A cause B'
        },
        {
            'name': 'overgeneralization',
            'category': 'argumentative',
            'description': 'Généralisation excessive à partir de cas limités',
            'example': 'J\'ai vu deux corbeaux noirs, donc tous les corbeaux sont noirs'
        },
        {
            'name': 'post_hoc_justification',
            'category': 'causal',
            'description': 'Explication fabriquée après coup pour justifier une conclusion',
            'example': 'Je dois avoir raison parce que sinon ce serait embarrassant'
        },
        {
            'name': 'circular_reasoning',
            'category': 'logical',
            'description': 'La conclusion est présente dans les prémisses',
            'example': 'C\'est vrai parce que c\'est vrai'
        },
        {
            'name': 'false_dichotomy',
            'category': 'argumentative',
            'description': 'Présentation d\'un faux choix binaire',
            'example': 'Soit tu es avec nous, soit tu es contre nous'
        },
        {
            'name': 'invalid_assumption',
            'category': 'logical',
            'description': 'Prémisse non fondée ou contestable',
            'example': 'Puisque tout le monde pense X, alors X est vrai'
        },
        {
            'name': 'logical_fallacy',
            'category': 'argumentative',
            'description': 'Autre sophisme ou erreur de raisonnement',
            'example': 'Attaque ad hominem, appel à l\'autorité, etc.'
        }
    ]
    
    for t in types:
        illusion_type = IllusionType(**t)
        db.session.add(illusion_type)
       
    db.session.commit()
    print(f"{len(types)} types d'illusions initialisés")

def init_db_complete():
    """Initialise la base de données avec toutes les tables"""
    db.create_all()
    print("Base de données initialisée")
       
    # Créer admin si nécessaire
    if User.query.count() == 0:
        admin = User(username='admin', email='admin@dirllm.com', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Utilisateur admin créé (admin/admin123)")
       
    # Initialiser la typologie
    init_illusion_types()
       
    print("\n=== BASE DE DONNÉES COMPLÈTE ===")
    print(f"Tables créées: {len(db.metadata.tables)}")
    print(f"Types d'illusions: {IllusionType.query.count()}")