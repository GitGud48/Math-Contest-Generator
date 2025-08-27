from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session, joinedload
from sqlalchemy.sql.expression import func
import os
import sys
import glob

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import AoPS models
try:
    from backend.aops.aops_models import Problem, ContestYear, Contest
    AOPS_SCHEMA_AVAILABLE = True
except ImportError as e:
    AOPS_SCHEMA_AVAILABLE = False
    print(f"⚠️  Warning: Could not import aops_models: {e}")

# Import Putnam models  
try:
    from backend.putnam.putnam_models import Problem as PutnamProblem, Year
    PUTNAM_SCHEMA_AVAILABLE = True
except ImportError as e:
    PUTNAM_SCHEMA_AVAILABLE = False
    print(f"⚠️  Warning: Could not import putnam_models: {e}")

# Import MIT models
try:
    from backend.mit.mit_models import Problem as MITProblem, Year as MITYear
    MIT_SCHEMA_AVAILABLE = True
except ImportError as e:
    MIT_SCHEMA_AVAILABLE = False
    print(f"⚠️  Warning: Could not import mit_models: {e}")

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app, supports_credentials=True)

class DatabaseManager:
    def __init__(self):
        self.databases = {}
        self.sessions = {}
        self._discover_databases()
    
    def _discover_databases(self):
        """Discover all available database files - FIXED FOR FRONTEND DIRECTORY"""
        # Since we're in frontend/, go up one level to find databases/
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        databases_dir = os.path.join(base_dir, 'databases')
        
        print(f"🔍 Looking for databases in: {databases_dir}")
        
        # Database file patterns - adjusted for frontend directory location
        db_patterns = [
            "../databases/*.sqlite",
            "../databases/*.db", 
            "../databases/*.sqlite3",
            # Also check root directory
            "../*.sqlite",
            "../*.db"
        ]
        
        db_files = []
        for pattern in db_patterns:
            matches = glob.glob(pattern)
            db_files.extend(matches)
        
        # Remove duplicates
        unique_dbs = list(set(db_files))
        
        print(f"📋 Found database files: {unique_dbs}")
        
        for db_path in unique_dbs:
            if os.path.exists(db_path):
                try:
                    db_name = os.path.basename(db_path).split('.')[0]
                    # Convert relative path to absolute
                    abs_db_path = os.path.abspath(db_path)
                    engine = create_engine(f"sqlite:///{abs_db_path}")
                    schema_type = self._detect_schema_type(engine)
                    
                    if schema_type:
                        self.databases[db_name] = {
                            'engine': engine,
                            'path': abs_db_path,
                            'schema': schema_type,
                            'display_name': self._get_display_name(db_name, schema_type)
                        }
                        
                        SessionLocal = scoped_session(sessionmaker(bind=engine))
                        self.sessions[db_name] = SessionLocal
                        print(f"✅ Connected: {db_name} ({schema_type}) at {abs_db_path}")
                
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
            elif 'mit' in db_name.lower():
                return "MIT Mathematics Competition"
            else:
                return "Art of Problem Solving (Multiple Contests)"
        else:
            return db_name.replace('_', ' ').title()
    
    def get_problems_from_db(self, db_name, limit=20):
        """Get random problems from specific database - FIXED VERSION"""
        if db_name not in self.sessions:
            return []
        
        try:
            SessionLocal = self.sessions[db_name]
            session = SessionLocal()
            schema_type = self.databases[db_name]['schema']
            problems = []
            
            if schema_type == 'aops' and AOPS_SCHEMA_AVAILABLE:
                # FIXED: Use eager loading to prevent detached session issues
                db_problems = (session.query(Problem)
                             .options(
                                 joinedload(Problem.contest_year)
                                 .joinedload(ContestYear.contest)
                             )
                             .order_by(func.random())
                             .limit(limit)
                             .all())
                
                # Process all data while session is active
                for p in db_problems:
                    try:
                        problems.append({
                            "label": p.problem_label or f"Problem {p.problem_number}",
                            "statement": p.statement or "Statement not available",
                            "solution": p.solution or "Solution not available",
                            "year": p.contest_year.year if p.contest_year else "Unknown",
                            "contest": (p.contest_year.contest.full_name or p.contest_year.contest.name) if (p.contest_year and p.contest_year.contest) else "Unknown Contest",
                            "subject": p.subject_area or "Unknown",
                            "source": db_name,
                            "problem_url": p.aops_problem_url
                        })
                    except Exception as e:
                        print(f"Error processing problem: {e}")
                        continue
            
            elif schema_type == 'putnam' and PUTNAM_SCHEMA_AVAILABLE:
                # Handle Putnam schema
                db_problems = (session.query(PutnamProblem)
                             .options(joinedload(PutnamProblem.year))
                             .order_by(func.random())
                             .limit(limit)
                             .all())
                
                for p in db_problems:
                    try:
                        problems.append({
                            "label": p.label or f"{p.part}{p.number}",
                            "statement": p.statement or "Statement not available",
                            "solution": p.solution or "Solution not available",
                            "year": p.year.year if p.year else "Unknown",
                            "contest": "Putnam Competition",
                            "subject": "Mixed",
                            "source": db_name,
                            "problem_url": getattr(p, 'pdf_url', None)
                        })
                    except Exception as e:
                        print(f"Error processing Putnam problem: {e}")
                        continue
            
            elif schema_type == 'generic':
                # Handle generic problems table
                with self.databases[db_name]['engine'].connect() as conn:
                    result = conn.execute(text(f"""
                        SELECT * FROM problems 
                        ORDER BY RANDOM() 
                        LIMIT {limit}
                    """))
                    
                    columns = result.keys()
                    rows = result.fetchall()
                    
                    for row in rows:
                        try:
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
                        except Exception as e:
                            print(f"Error processing generic problem: {e}")
                            continue
            
            session.close()
            return problems
        
        except Exception as e:
            print(f"❌ Error fetching from {db_name}: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_database_list(self):
        """Get list of available databases"""
        db_list = []
        for db_name, db_info in self.databases.items():
            try:
                SessionLocal = self.sessions[db_name]
                session = SessionLocal()
                
                if db_info['schema'] == 'aops' and AOPS_SCHEMA_AVAILABLE:
                    problem_count = session.query(Problem).count()
                    contest_count = session.query(Contest).count()
                elif db_info['schema'] == 'putnam' and PUTNAM_SCHEMA_AVAILABLE:
                    problem_count = session.query(PutnamProblem).count()
                    contest_count = 1
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
        db_name = request.args.get('database')
        limit = int(request.args.get('limit', 20))
        limit = min(limit, 100)
        
        # Default database selection
        if not db_name:
            if 'imo' in db_manager.databases:
                db_name = 'imo'
            elif 'putnam' in db_manager.databases:
                db_name = 'putnam'  
            elif 'mit' in db_manager.databases:
                db_name = 'mit'
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
        import traceback
        traceback.print_exc()
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
        "current_directory": os.getcwd(),
        "databases": {
            db_name: {
                "name": db_data["display_name"],
                "schema": db_data["schema"],
                "path": db_data["path"]
            } 
            for db_name, db_data in db_manager.databases.items()
        },
        "schema_support": {
            "aops": AOPS_SCHEMA_AVAILABLE,
            "putnam": PUTNAM_SCHEMA_AVAILABLE,
            "mit": MIT_SCHEMA_AVAILABLE
        }
    })

if __name__ == "__main__":
    print(f"🚀 Starting server from: {os.getcwd()}")
    print(f"🔍 Parent directory: {os.path.dirname(os.getcwd())}")
    print(f"📊 Connected databases: {len(db_manager.databases)}")
    for db_name, db_info in db_manager.databases.items():
        print(f"   - {db_info['display_name']} ({db_info['schema']}) at {db_info['path']}")
    app.run(debug=True, host='0.0.0.0', port=4000)
