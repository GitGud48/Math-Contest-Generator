from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import func
import os
import glob

# Import AoPS models (from your aops_models.py)
try:
    from backend.aops.aops_models import Problem, ContestYear, Contest
    AOPS_SCHEMA_AVAILABLE = True
except ImportError:
    AOPS_SCHEMA_AVAILABLE = False
    print("⚠️  Warning: aops_models.py not found or not importable")

# Import Putnam models (if you still want support for original Putnam database)
try:
    from backend.putnam.putnam_models import Problem as PutnamProblem, Year
    PUTNAM_SCHEMA_AVAILABLE = True
except ImportError:
    PUTNAM_SCHEMA_AVAILABLE = False
    print("⚠️  Warning: putnam_models.py not found or not importable")

# Import MIT models (if you still want support for original MIT database)
try:
    from backend.mit.mit_models import Problem as PutnamProblem, Year
    MIT_SCHEMA_AVAILABLE = True
except ImportError:
    MIT_SCHEMA_AVAILABLE = False
    print("⚠️  Warning: mit_models.py not found or not importable")

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
                # Check for AoPS schema (has contests table)
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='contests'"))
                if result.fetchone():
                    return 'aops'
                
                # Check for Putnam schema (has years table)
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
            if 'imo' in db_name.lower():
                return "International Mathematical Olympiad (IMO)"
            else:
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
                # Query AoPS database structure (IMO database)
                db_problems = (session.query(Problem)
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
                        "contest": p.contest_year.contest.full_name or p.contest_year.contest.name,
                        "subject": p.subject_area or "Unknown",
                        "source": db_name,
                        "problem_url": p.aops_problem_url
                    })
            
            elif schema_type == 'putnam' and PUTNAM_SCHEMA_AVAILABLE:
                # Query original Putnam database structure
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
                        "subject": "Mixed",
                        "source": db_name,
                        "problem_url": p.pdf_url
                    })
            
            elif schema_type == 'generic':
                # Handle generic database structure
                with self.databases[db_name]['engine'].connect() as conn:
                    result = conn.execute(text(f"""
                        SELECT * FROM problems 
                        ORDER BY RANDOM() 
                        LIMIT {limit}
                    """))
                    
                    columns = result.keys()
                    rows = result.fetchall()
                    
                    for row in rows:
                        row_dict = dict(zip(columns, row))
                        problems.append({
                            "label": row_dict.get('label', row_dict.get('problem_label', f"Problem {row_dict.get('id', '?')}")),
                            "statement": row_dict.get('statement', "Statement not available"),
                            "solution": row_dict.get('solution', "Solution not available"),
                            "year": row_dict.get('year', 'Unknown'),
                            "contest": db_name.replace('_', ' ').title(),
                            "subject": row_dict.get('subject_area', 'Unknown'),
                            "source": db_name,
                            "problem_url": row_dict.get('aops_problem_url', row_dict.get('pdf_url'))
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
                    problem_count = session.query(Problem).count()
                    contest_count = session.query(Contest).count()
                elif db_info['schema'] == 'putnam' and PUTNAM_SCHEMA_AVAILABLE:
                    problem_count = session.query(PutnamProblem).count()
                    contest_count = 1  # Only Putnam
                else:
                    with db_info['engine'].connect() as conn:
                        result = conn.execute(text("SELECT COUNT(*) FROM problems"))
                        problem_count = result.scalar()
                        contest_count = "Unknown"
                
                db_list.append({
                    'id': db_name,
                    'name': db_info['display_name'],
                    'schema': db_info['schema'],
                    'problem_count': problem_count,
                    'contest_count': contest_count
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
        db_name = request.args.get('database')
        limit = int(request.args.get('limit', 20))
        limit = min(limit, 100)
        
        # If no database specified, prefer IMO database
        if not db_name:
            if 'imo_complete' in db_manager.databases:
                db_name = 'imo_complete'
            elif 'imo_problems' in db_manager.databases:
                db_name = 'imo_problems'
            elif 'imo_test' in db_manager.databases:
                db_name = 'imo_test'
            elif db_manager.databases:
                db_name = list(db_manager.databases.keys())[0]
            else:
                return jsonify({
                    "problems": [],
                    "error": "No databases available"
                }), 404
        
        if db_name not in db_manager.databases:
            return jsonify({
                "problems": [],
                "error": f"Database '{db_name}' not found",
                "available_databases": list(db_manager.databases.keys())
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

@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "databases_connected": len(db_manager.databases),
        "databases": {
            db_name: {
                "name": db_data["display_name"],
                "schema": db_data["schema"]
            } 
            for db_name, db_data in db_manager.databases.items()
        },
        "schema_support": {
            "aops": AOPS_SCHEMA_AVAILABLE,
            "putnam": PUTNAM_SCHEMA_AVAILABLE
        }
    })

if __name__ == "__main__":
    print(f"🚀 Starting server with {len(db_manager.databases)} databases")
    for db_name, db_info in db_manager.databases.items():
        print(f"   - {db_info['display_name']} ({db_info['schema']})")
    app.run(debug=True, host='0.0.0.0', port=3000)
