import re
from mit_models import Base, Category, Problem
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# --- Setup DB ---
engine = create_engine("sqlite:///mit.sqlite", echo=True)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

for table in reversed(Base.metadata.sorted_tables):
    session.execute(table.delete())
session.commit()

# --- Load TeX file ---
with open("BACKEND/mit/mit_problems.tex", "r", encoding="utf-8") as f:
    tex = f.read()

# --- Split into categories ---
section_pattern = r"\\section\*\{([^}]*)\}(.*?)((?=\\section\*{)|\Z)"
matches = re.findall(section_pattern, tex, flags=re.S)

for section_name, content, _ in matches:
    # Create category row if not exists
    category = session.query(Category).filter_by(category=section_name).first()
    if not category:
        category = Category(category=section_name)
        session.add(category)
        session.commit()

    # Extract problems
    problem_pattern = r"\\begin\{problem\}(.*?)\\end\{problem\}"
    problems = re.findall(problem_pattern, content, flags=re.S)

    for p in problems:
        # Clean whitespace
        statement = p.strip()
        prob = Problem(category_id=category.id, statement=statement)
        session.add(prob)

session.commit()
print("✅ All problems inserted!")
