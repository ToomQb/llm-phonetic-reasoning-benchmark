from datasets import load_dataset
from models import db, Dataset, DatasetSample

class DatasetLoader:
    """Chargeur de datasets de raisonnement logique avec insertion en DB"""
   
    def __init__(self, db_session):
        self.db = db_session
   
    # ---------------- ProntoQA ----------------
    def load_prontoqa(self, max_samples: int = None) -> dict:
        """Charge et insère le dataset ProntoQA"""
        print("Chargement de ProntoQA...")
        try:
            existing = Dataset.query.filter_by(name='ProntoQA').first()
            if existing:
                print(f"ProntoQA déjà chargé ({existing.total_samples} échantillons)")
                return {'success': False, 'message': 'Dataset déjà chargé', 'dataset': existing}
            dataset = load_dataset("logicreasoning/logi_glue", "prontoqa", split="test")
            ds = Dataset(
                name='ProntoQA',
                description='Dataset de logique formelle avec raisonnement déductif',
                category='formal_logic',
                total_samples=0
            )
            self.db.session.add(ds)
            self.db.session.commit()
            count = 0
            for i, item in enumerate(dataset):
                if max_samples and i >= max_samples:
                    break
                # Conversion des listes en texte pour SQLite
                full_solution = item.get("ground_truth_cots", "")
                if isinstance(full_solution, list):
                    full_solution = "\n".join(full_solution)
                sample = DatasetSample(
                    dataset_id=ds.id,
                    sample_id=f"prontoqa_{i}",
                    question=item.get("input", ""),
                    context="", # pas de champ context disponible
                    answer=item.get("answer_text", ""),
                    full_solution=full_solution,
                    category="formal_logic"
                )
                self.db.session.add(sample)
                count += 1
                if count % 50 == 0:
                    self.db.session.commit()
            ds.total_samples = count
            self.db.session.commit()
            print(f"ProntoQA chargé: {count} échantillons")
            return {'success': True, 'dataset': ds, 'count': count}
        except Exception as e:
            self.db.session.rollback()
            print(f"Erreur ProntoQA: {e}")
            return {'success': False, 'error': str(e)}
    # ---------------- FOLIO ----------------
    def load_folio(self, max_samples: int = None) -> dict:
        print("Chargement de FOLIO...")
        try:
            existing = Dataset.query.filter_by(name='FOLIO').first()
            if existing:
                print(f"FOLIO déjà chargé ({existing.total_samples} échantillons)")
                return {'success': False, 'message': 'Dataset déjà chargé', 'dataset': existing}
           
            dataset = load_dataset("logicreasoning/logi_glue", "folio", split="test")
            ds = Dataset(
                name='FOLIO',
                description='First-Order Logic dataset avec inférence complexe',
                category='first_order_logic',
                total_samples=0
            )
            self.db.session.add(ds)
            self.db.session.commit()
           
            count = 0
            for i, item in enumerate(dataset):
                if max_samples and i >= max_samples:
                    break
               
                sample = DatasetSample(
                    dataset_id=ds.id,
                    sample_id=f"folio_{i}",
                    question=item.get("question", ""),
                    context=item.get("context", ""),
                    answer=item.get("answer_text", ""),
                    full_solution=item.get("proof", ""),
                    category="first_order_logic"
                )
                self.db.session.add(sample)
                count += 1
                if count % 50 == 0:
                    self.db.session.commit()
           
            ds.total_samples = count
            self.db.session.commit()
            print(f"FOLIO chargé: {count} échantillons")
            return {'success': True, 'dataset': ds, 'count': count}
        except Exception as e:
            self.db.session.rollback()
            print(f"Erreur FOLIO: {e}")
            return {'success': False, 'error': str(e)}
    # ---------------- LogiQA ----------------
    def load_logiqa(self, max_samples: int = None) -> dict:
        print("Chargement de LogiQA...")
        try:
            existing = Dataset.query.filter_by(name='LogiQA').first()
            if existing:
                print(f"LogiQA déjà chargé ({existing.total_samples} échantillons)")
                return {'success': False, 'message': 'Dataset déjà chargé', 'dataset': existing}
           
            dataset = load_dataset("logicreasoning/logi_glue", "logiQA", split="test")
            ds = Dataset(
                name='LogiQA',
                description='Dataset de raisonnement logique avec questions complexes',
                category='logical_reasoning',
                total_samples=0
            )
            self.db.session.add(ds)
            self.db.session.commit()
           
            count = 0
            for i, item in enumerate(dataset):
                if max_samples and i >= max_samples:
                    break
               
                sample = DatasetSample(
                    dataset_id=ds.id,
                    sample_id=f"logiqa_{i}",
                    question=item.get("question", ""),
                    context=item.get("context", ""),
                    answer=item.get("answer_text", ""),
                    full_solution=item.get("proof", ""),
                    category="logical_reasoning"
                )
                self.db.session.add(sample)
                count += 1
                if count % 50 == 0:
                    self.db.session.commit()
           
            ds.total_samples = count
            self.db.session.commit()
            print(f"LogiQA chargé: {count} échantillons")
            return {'success': True, 'dataset': ds, 'count': count}
        except Exception as e:
            self.db.session.rollback()
            print(f"Erreur LogiQA: {e}")
            return {'success': False, 'error': str(e)}
    # ---------------- GSM8K ----------------
    def load_gsm8k(self, max_samples: int = None) -> dict:
        print("Chargement de GSM8K...")
        try:
            existing = Dataset.query.filter_by(name='GSM8K').first()
            if existing:
                print(f"GSM8K déjà chargé ({existing.total_samples} échantillons)")
                return {'success': False, 'message': 'Dataset déjà chargé', 'dataset': existing}
           
            dataset = load_dataset("openai/gsm8k", "main", split="test")
            ds = Dataset(
                name='GSM8K',
                description='Grade School Math - Problèmes mathématiques avec solutions',
                category='mathematical_reasoning',
                total_samples=0
            )
            self.db.session.add(ds)
            self.db.session.commit()
           
            count = 0
            for i, item in enumerate(dataset):
                if max_samples and i >= max_samples:
                    break
                answer_text = item.get("answer", "")
                final_answer = self._extract_final_answer(answer_text)
                sample = DatasetSample(
                    dataset_id=ds.id,
                    sample_id=f"gsm8k_{i}",
                    question=item.get("question", ""),
                    context="",
                    answer=final_answer,
                    full_solution=answer_text,
                    category="mathematical_reasoning"
                )
                self.db.session.add(sample)
                count += 1
                if count % 50 == 0:
                    self.db.session.commit()
           
            ds.total_samples = count
            self.db.session.commit()
            print(f"GSM8K chargé: {count} échantillons")
            return {'success': True, 'dataset': ds, 'count': count}
        except Exception as e:
            self.db.session.rollback()
            print(f"Erreur GSM8K: {e}")
            return {'success': False, 'error': str(e)}
    # ---------------- Méthodes utilitaires ----------------
    def _extract_final_answer(self, answer_text: str) -> str:
        """Extrait la réponse finale après ####"""
        if "####" in answer_text:
            return answer_text.split("####")[1].strip()
        return answer_text
    def load_all_datasets(self, max_samples_per_dataset: int = None) -> dict:
        """Charge tous les datasets disponibles"""
        print("CHARGEMENT DE TOUS LES DATASETS")
        results = {}
        results['ProntoQA'] = self.load_prontoqa(max_samples_per_dataset)
        results['FOLIO'] = self.load_folio(max_samples_per_dataset)
        results['LogiQA'] = self.load_logiqa(max_samples_per_dataset)
        results['GSM8K'] = self.load_gsm8k(max_samples_per_dataset)
       
        total_samples = sum(r.get('count', 0) for r in results.values() if r.get('success'))
        total_datasets = sum(1 for r in results.values() if r.get('success'))
        print(f"RÉSUMÉ: {total_datasets} datasets chargés, {total_samples} échantillons totaux")
        return results