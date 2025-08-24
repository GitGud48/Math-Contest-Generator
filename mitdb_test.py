from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from mit_models import Category, Problem


DB_PATH = "mit.sqlite"
engine = create_engine(f"sqlite:///{DB_PATH}")
Session = sessionmaker(bind=engine)
sess = Session()

# Display all years
for category in sess.query(Category).order_by(Category.id):
    print(f"Category: {category}")
    # Display problems for this year
    for problem in category.problems:
        print(f"    Problem {problem.id} - {problem.statement[:60]}...")

sess.close()