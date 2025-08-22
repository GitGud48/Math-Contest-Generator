from flask import Flask, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Year, Problem

app = Flask(__name__)
engine = create_engine("sqlite:///putnam.sqlite")
Session = sessionmaker(bind=engine)

@app.route("/problems")
def get_problems():
    sess = Session()
    problems = sess.query(Problem).limit(20).all()
    result = [
        {
            "label": p.label,
            "statement": p.statement,
            "solution": p.solution,
            "year": p.year.year
        }
        for p in problems
    ]
    sess.close()
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)