# models.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Year(Base):
    __tablename__ = "years"

    id = Column(Integer, primary_key=True)
    year = Column(Integer, unique=True, nullable=False)

    # URLs for reference
    pdf_url = Column(String, nullable=True)              # Problems PDF
    solutions_pdf_url = Column(String, nullable=True)    # Solutions PDF
    problems_tex_url = Column(String, nullable=True)     # Problems TeX
    solutions_tex_url = Column(String, nullable=True)    # Solutions TeX

    problems = relationship("Problem", back_populates="year")

    def __repr__(self):
        return f"<Year {self.year}>"

class Problem(Base):
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True)
    year_id = Column(Integer, ForeignKey("years.id"), nullable=False)

    part = Column(String(1), nullable=True)     # 'A' or 'B'
    number = Column(Integer, nullable=True)     # 1–6
    label = Column(String, nullable=True)       # e.g., 'A1', 'B3'

    statement = Column(Text, nullable=True)     # Problem text (LaTeX or PDF text)
    solution = Column(Text, nullable=True)      # Solution text (LaTeX or PDF text)

    pdf_url = Column(String, nullable=True)     # Source file URL

    year = relationship("Year", back_populates="problems")

    def __repr__(self):
        return f"<Problem {self.label} ({self.year.year})>"