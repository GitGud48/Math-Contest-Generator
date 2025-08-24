# mit_models.py


from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String, unique=True, nullable=False)

    # URLs for reference
    pdf_url = Column(String, nullable=True)              # Problems PDF
    #solutions_pdf_url = Column(String, nullable=True)    # Solutions PDF
    #problems_tex_url = Column(String, nullable=True)     # Problems TeX
    #solutions_tex_url = Column(String, nullable=True)    # Solutions TeX

# this is just a matter of how the website gives data, if it always gives all 4 files, ignore.
# also, PDF might be redundant UNLESS we want to give user option to view pdf.
    problems = relationship("Problem", back_populates="category")

    def __repr__(self):
        return f"<Category {self.category}>"

class Problem(Base):
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    statement = Column(Text, nullable=True)     # Problem text (LaTeX) LaTeX > PDF probably
    solution = Column(Text, nullable=True)      # Solution text (LaTeX or PDF text) LaTeX > PDF probably

    pdf_url = Column(String, nullable=True)     # Source file URL

    category = relationship("Category", back_populates="problems")

    def __repr__(self):
        return f"<Problem {self.id} ({self.category})>"