import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import Config
from models import db, init_db_complete
from routes import init_routes
from flask_login import LoginManager
from models.user import User 

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialiser extensions
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Configurer user_loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Initialiser routes
    init_routes(app)

    # Initialisation DB si nécessaire
    with app.app_context():
        init_db_complete()

    return app

if __name__ == '__main__':
    import sys
    app = create_app()

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'load-datasets':
            from services.dataset_loader import DatasetLoader
            max_samples = None
            if '--max-samples' in sys.argv:
                idx = sys.argv.index('--max-samples')
                if idx + 1 < len(sys.argv):
                    max_samples = int(sys.argv[idx + 1])
            with app.app_context():
                loader = DatasetLoader(db)
                results = loader.load_all_datasets(max_samples)
                print("Datasets chargés !")
        elif command == 'init-complete':
            with app.app_context():
                init_db_complete()
        elif command == 'run-benchmark':
            from models.metrics import run_benchmark_experiment
            with app.app_context():
                run_benchmark_experiment()
        else:
            print("Commandes disponibles: load-datasets [--max-samples N], init-complete, run-benchmark")
    else:
        app.run(debug=True, port=5000)