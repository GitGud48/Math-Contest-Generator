from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from BACKEND.putnam.putnam_models import Year, Problem


DB_PATH = "putnam.sqlite"
engine = create_engine(f"sqlite:///{DB_PATH}")
Session = sessionmaker(bind=engine)
sess = Session()

# Display all years
for year in sess.query(Year).order_by(Year.year):
    print(f"Year: {year.year}")
    print(f"  Problems PDF: {year.pdf_url}")
    print(f"  Solutions PDF: {year.solutions_pdf_url}")
    print(f"  Problems TeX: {year.problems_tex_url}")
    print(f"  Solutions TeX: {year.solutions_tex_url}")
    # Display problems for this year
    for problem in year.problems:
        print(f"    Problem: {problem.label} - {problem.statement[:60]}...")

sess.close()