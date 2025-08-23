from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.expression import func
from models import Problem, Year

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# Configure your database
engine = create_engine("sqlite:///putnam.sqlite")
Session = sessionmaker(bind=engine)

@app.route("/")
def serve_index():
    return send_from_directory(".", "index.html")

@app.route("/problems")
def get_problems():
    try:
        sess = Session()
        problems = sess.query(Problem).order_by(func.random()).limit(20).all()
        result = [
            { #yo
                "label": p.label,
                "statement": p.statement,
                "solution": p.solution,
                "year": p.year.year
            }
            for p in problems
        ]
        sess.close()
        return jsonify(result)  # Always returns a list
    except Exception as e:
        print("Error fetching problems:", e)
        return jsonify([]), 500  # Return empty array on error

if __name__ == "__main__":
    app.run(debug=True)
