from flask import Flask, render_template, request, jsonify, g
import json
import sqlite3
from typing import Dict, Optional
import os
from datetime import datetime
from config import Config

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from generate_charade import generate_charade


app = Flask(__name__)
app.config['DATABASE'] = 'charades.db'

# =====================================================
# BASE DE DONNÉES
# =====================================================

def init_db():
    """Initialise la base de données SQLite."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # Table pour stocker les générations
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS charades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            generation_id TEXT UNIQUE,
            prompt_type TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            target_word TEXT,
            num_segments INTEGER,
            temperature REAL,
            raw_response TEXT,
            charade_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            execution_time REAL,
            user_rating INTEGER DEFAULT 0,
            user_feedback TEXT
        )
        ''')
        
        db.commit()

def get_db():
    """Obtient la connexion à la base de données."""
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    """Ferme la connexion à la base de données."""
    if 'db' in g:
        g.db.close()

def generate_unique_id():
    """Génère un ID unique pour une génération."""
    return f"charade_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(2).hex()}"

# =====================================================
# ROUTES FLASK
# =====================================================

@app.route('/')
def index():
    """Page d'accueil avec interface unique."""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """Génère une charade."""
    data = request.json
    difficulty = data.get('difficulty', 'easy')
    prompt_type = data.get('prompt_type', 'simple')
    target_word = data.get('target_word', '')
    num_segments = data.get('num_segments', 3)
    
    use_prompt_engineering = (prompt_type == 'engineered')
    
    result = generate_charade(
        difficulty=difficulty,
        use_prompt_engineering=use_prompt_engineering,
        num_segments=num_segments,
        target_word=target_word if target_word else None
    )

    print("Génération result:", result)
    
    if result['success']:
        # Enregistrer dans la base de données
        generation_id = generate_unique_id()
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
        INSERT INTO charades 
        (generation_id, prompt_type, difficulty, target_word, num_segments, 
         raw_response, charade_data, execution_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            generation_id,
            prompt_type,
            difficulty,
            target_word if target_word else None,
            num_segments,
            result['raw_response'],
            json.dumps(result['charade'], ensure_ascii=False),
            result['execution_time']
        ))
        
        db.commit()
        
        result['generation_id'] = generation_id
        result['created_at'] = datetime.now().isoformat()
    
    return jsonify(result)

@app.route('/history')
def get_history():
    """Récupère l'historique des charades."""
    db = get_db()
    cursor = db.cursor()
    
    # Récupérer avec pagination
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    offset = (page - 1) * limit
    
    cursor.execute('''
    SELECT generation_id, prompt_type, difficulty, target_word, 
           created_at, execution_time, user_rating, charade_data
    FROM charades 
    ORDER BY created_at DESC 
    LIMIT ? OFFSET ?
    ''', (limit, offset))
    
    charades = []
    for row in cursor.fetchall():
        charade_data = json.loads(row['charade_data']) if row['charade_data'] else {}
        charades.append({
            "id": row['generation_id'],
            "prompt_type": row['prompt_type'],
            "difficulty": row['difficulty'],
            "target_word": row['target_word'],
            "created_at": row['created_at'],
            "execution_time": row['execution_time'],
            "user_rating": row['user_rating'],
            "target_word_display": charade_data.get('target_word', ''),
            "clue_definition": charade_data.get('clue_definition', ''),
            "segments_count": len(charade_data.get('segments', []))
        })
    
    # Compter le total
    cursor.execute('SELECT COUNT(*) as total FROM charades')
    total = cursor.fetchone()['total']
    
    return jsonify({
        "charades": charades,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit
    })

@app.route('/charade/<generation_id>')
def get_charade_detail(generation_id):
    """Récupère les détails d'une charade spécifique."""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
    SELECT * FROM charades WHERE generation_id = ?
    ''', (generation_id,))
    
    row = cursor.fetchone()
    
    if not row:
        return jsonify({"error": "Charade non trouvée"}), 404
    
    charade_data = json.loads(row['charade_data']) if row['charade_data'] else {}
    
    return jsonify({
        "id": row['generation_id'],
        "prompt_type": row['prompt_type'],
        "difficulty": row['difficulty'],
        "target_word": row['target_word'],
        "created_at": row['created_at'],
        "execution_time": row['execution_time'],
        "user_rating": row['user_rating'],
        "user_feedback": row['user_feedback'],
        "charade": charade_data,
        "raw_response": row['raw_response'][:500] + "..." if len(row['raw_response']) > 500 else row['raw_response']
    })

@app.route('/rate/<generation_id>', methods=['POST'])
def rate_charade(generation_id):
    """Note une charade."""
    data = request.json
    rating = data.get('rating')
    feedback = data.get('feedback', '')
    
    if rating not in [1, 2, 3, 4, 5]:
        return jsonify({"error": "La note doit être entre 1 et 5"}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
    UPDATE charades 
    SET user_rating = ?, user_feedback = ?
    WHERE generation_id = ?
    ''', (rating, feedback, generation_id))
    
    db.commit()
    
    return jsonify({"success": True, "message": "Note enregistrée avec succès"})

@app.route('/delete/<generation_id>', methods=['DELETE'])
def delete_charade(generation_id):
    """Supprime une charade."""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('DELETE FROM charades WHERE generation_id = ?', (generation_id,))
    db.commit()
    
    return jsonify({"success": True, "message": "Charade supprimée"})

@app.route('/stats')
def get_stats():
    """Récupère les statistiques."""
    db = get_db()
    cursor = db.cursor()
    
    # Statistiques globales
    cursor.execute('''
    SELECT 
        COUNT(*) as total_charades,
        AVG(execution_time) as avg_execution_time,
        AVG(user_rating) as avg_rating
    FROM charades
    ''')
    
    stats = cursor.fetchone()
    
    # Statistiques par type de prompt
    cursor.execute('''
    SELECT 
        prompt_type,
        COUNT(*) as count,
        AVG(user_rating) as avg_rating,
        AVG(execution_time) as avg_time
    FROM charades
    GROUP BY prompt_type
    ''')
    
    prompt_stats = {}
    for row in cursor.fetchall():
        prompt_stats[row['prompt_type']] = {
            "count": row['count'],
            "avg_rating": round(row['avg_rating'], 1) if row['avg_rating'] else 0,
            "avg_time": round(row['avg_time'], 2) if row['avg_time'] else 0
        }
    
    # Dernières charades
    cursor.execute('''
    SELECT generation_id, target_word, prompt_type, difficulty, user_rating
    FROM charades
    ORDER BY created_at DESC
    LIMIT 5
    ''')
    
    recent = []
    for row in cursor.fetchall():
        recent.append({
            "id": row['generation_id'],
            "target_word": row['target_word'],
            "prompt_type": row['prompt_type'],
            "difficulty": row['difficulty'],
            "rating": row['user_rating']
        })
    
    return jsonify({
        "total_charades": stats['total_charades'],
        "avg_execution_time": round(stats['avg_execution_time'], 2) if stats['avg_execution_time'] else 0,
        "avg_rating": round(stats['avg_rating'], 1) if stats['avg_rating'] else 0,
        "prompt_stats": prompt_stats,
        "recent_charades": recent
    })


# =====================================================
# LANCEMENT DE L'APPLICATION
# =====================================================

if __name__ == '__main__':
    # Initialiser la base de données
    init_db()
    
    print("\nApplication Flask prête!")
    print("Interface disponible à l'adresse: http://localhost:5000")
    print("\nLancement de l'application...")
    
    app.run(debug=True, port=5000)