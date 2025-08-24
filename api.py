from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import func
import os
import glob

# Import Putnam models (original models.py)
try:
    from models import Problem as PutnamProblem, Year
    PUTNAM_SCHEMA_AVAILABLE = True
except ImportError:
    PUTNAM_SCHEMA_AVAILABLE = False
    print("⚠️  Warning: models.py (Putnam) not found or not importable")

# Import AoPS models (aops_models.py)
try:
    from aops_models import Problem as AoPSProblem, ContestYear, Contest
    AOPS_SCHEMA_AVAILABLE = True
except ImportError:
    AOPS_SCHEMA_AVAILABLE = False
    print("⚠️  Warning: aops_models.py not found or not importable")
from putnam_models import Problem, Year

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

class DatabaseManager:
    def __init__(self):
        self.databases = {}
        self.sessions = {}
        self._discover_databases()
    
    def _discover_databases(self):
        """Discover all available database files"""
        db_patterns = [
            "./databases/*.db",
            "./databases/*.sqlite", 
            "./databases/*.sqlite3",
            "./putnam.sqlite",
            "./aops_contests.db"
        ]
        
        db_files = []
        for pattern in db_patterns:
            db_files.extend(glob.glob(pattern))
        
        unique_dbs = list(set(db_files))
        
        for db_path in unique_dbs:
            if os.path.exists(db_path):
                try:
                    db_name = os.path.basename(db_path).split('.')[0]
                    engine = create_engine(f"sqlite:///{db_path}")
                    schema_type = self._detect_schema_type(engine)
                    
                    if schema_type:
                        self.databases[db_name] = {
                            'engine': engine,
                            'path': db_path,
                            'schema': schema_type,
                            'display_name': self._get_display_name(db_name, schema_type)
                        }
                        
                        Session = sessionmaker(bind=engine)
                        self.sessions[db_name] = Session
                        print(f"✅ Connected: {db_name} ({schema_type})")
                
                except Exception as e:
                    print(f"❌ Failed to connect to {db_path}: {e}")
    
    def _detect_schema_type(self, engine):
        """Detect database schema type"""
        try:
            with engine.connect() as conn:
                # Check for AoPS schema
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='contests'"))
                if result.fetchone():
                    return 'aops'
                
                # Check for Putnam schema
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='years'"))
                if result.fetchone():
                    return 'putnam'
                
                # Check for generic problems table
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='problems'"))
                if result.fetchone():
                    return 'generic'
        except Exception as e:
            print(f"Schema detection error: {e}")
        return None
    
    def _get_display_name(self, db_name, schema_type):
        """Generate user-friendly display name"""
        if schema_type == 'putnam':
            return "Putnam Competition"
        elif schema_type == 'aops':
            return "Art of Problem Solving (Multiple Contests)"
        else:
            return db_name.replace('_', ' ').title()
    
    def get_problems_from_db(self, db_name, limit=20):
        """Get random problems from specific database"""
        if db_name not in self.sessions:
            return []
        
        try:
            Session = self.sessions[db_name]
            session = Session()
            schema_type = self.databases[db_name]['schema']
            problems = []
            
            if schema_type == 'aops' and AOPS_SCHEMA_AVAILABLE:
                db_problems = (session.query(AoPSProblem)
                             .join(ContestYear)
                             .join(Contest)
                             .order_by(func.random())
                             .limit(limit)
                             .all())
                
                for p in db_problems:
                    problems.append({
                        "label": p.problem_label or f"Problem {p.problem_number}",
                        "statement": p.statement or "Statement not available",
                        "solution": p.solution or "Solution not available",
                        "year": p.contest_year.year,
                        "contest": p.contest_year.contest.name,
                        "source": db_name
                    })
            
            elif schema_type == 'putnam' and PUTNAM_SCHEMA_AVAILABLE:
                db_problems = (session.query(PutnamProblem)
                             .join(Year)
                             .order_by(func.random())
                             .limit(limit)
                             .all())
                
                for p in db_problems:
                    problems.append({
                        "label": p.label or f"{p.part}{p.number}",
                        "statement": p.statement or "Statement not available",
                        "solution": p.solution or "Solution not available",
                        "year": p.year.year,
                        "contest": "Putnam Competition",
                        "source": db_name
                    })
            
            session.close()
            return problems
        
        except Exception as e:
            print(f"Error fetching from {db_name}: {e}")
            return []
    
    def get_database_list(self):
        """Get list of available databases"""
        db_list = []
        for db_name, db_info in self.databases.items():
            try:
                Session = self.sessions[db_name]
                session = Session()
                
                if db_info['schema'] == 'aops' and AOPS_SCHEMA_AVAILABLE:
                    problem_count = session.query(AoPSProblem).count()
                elif db_info['schema'] == 'putnam' and PUTNAM_SCHEMA_AVAILABLE:
                    problem_count = session.query(PutnamProblem).count()
                else:
                    with db_info['engine'].connect() as conn:
                        result = conn.execute(text("SELECT COUNT(*) FROM problems"))
                        problem_count = result.scalar()
                
                db_list.append({
                    'id': db_name,
                    'name': db_info['display_name'],
                    'schema': db_info['schema'],
                    'problem_count': problem_count
                })
                
                session.close()
            except Exception as e:
                db_list.append({
                    'id': db_name,
                    'name': db_info['display_name'],
                    'schema': db_info['schema'],
                    'problem_count': 0,
                    'error': str(e)
                })
        
        return sorted(db_list, key=lambda x: x['name'])

# Initialize database manager
db_manager = DatabaseManager()

@app.route("/")
def serve_index():
    return send_from_directory(".", "index.html")

@app.route("/problems")
def get_problems():
    """Get problems from specified database or default"""
    try:
        # Get database from query parameter
        db_name = request.args.get('database', 'putnam')  # Default to putnam
        limit = int(request.args.get('limit', 20))
        limit = min(limit, 100)
        
        if db_name not in db_manager.databases:
            # If requested database doesn't exist, use the first available
            if db_manager.databases:
                db_name = list(db_manager.databases.keys())[0]
            else:
                return jsonify({
                    "problems": [],
                    "error": "No databases available"
                }), 404
        
        problems = db_manager.get_problems_from_db(db_name, limit)
        
        return jsonify({
            "problems": problems,
            "database_used": db_name,
            "database_name": db_manager.databases[db_name]['display_name'],
            "total_returned": len(problems)
        })
    
    except Exception as e:
        print(f"Error fetching problems: {e}")
        return jsonify({
            "problems": [],
            "error": str(e)
        }), 500

@app.route("/databases")
def get_databases():
    """Get list of available databases"""
    try:
        databases = db_manager.get_database_list()
        return jsonify({
            "databases": databases,
            "total": len(databases)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print(f"🚀 Starting server with {len(db_manager.databases)} databases")
    for db_name, db_info in db_manager.databases.items():
        print(f"   - {db_info['display_name']} ({db_info['schema']})")
    app.run(debug=True, host='0.0.0.0', port=3000)
