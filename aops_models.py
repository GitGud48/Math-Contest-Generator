# models.py
# Updated data models to accommodate diverse math contest problems from AoPS

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Float
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Contest(Base):
    __tablename__ = "contests"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)  # e.g., "Putnam", "IMO", "USAMO", "AMC"
    full_name = Column(String, nullable=True)  # e.g., "International Mathematical Olympiad"
    country = Column(String, nullable=True)  # e.g., "USA", "International", "Canada"
    organization = Column(String, nullable=True)  # e.g., "MAA", "IMO Committee"
    
    # Contest metadata
    contest_type = Column(String, nullable=True)  # e.g., "Olympiad", "Multiple Choice", "Proof-based"
    target_level = Column(String, nullable=True)  # e.g., "High School", "University", "Middle School"
    difficulty_rating = Column(Float, nullable=True)  # 1-10 scale based on AoPS ratings
    
    # Contest format information
    duration_minutes = Column(Integer, nullable=True)  # Contest duration
    max_score = Column(Integer, nullable=True)  # Maximum possible score
    num_problems = Column(Integer, nullable=True)  # Number of problems per contest
    
    # URLs and references
    official_website = Column(String, nullable=True)
    aops_wiki_url = Column(String, nullable=True)  # AoPS wiki page for this contest
    
    # Relationships
    years = relationship("ContestYear", back_populates="contest")
    
    def __repr__(self):
        return f"<Contest {self.name}>"

class ContestYear(Base):
    __tablename__ = "contest_years"
    
    id = Column(Integer, primary_key=True)
    contest_id = Column(Integer, ForeignKey("contests.id"), nullable=False)
    year = Column(Integer, nullable=False)
    
    # Year-specific metadata
    date_held = Column(DateTime, nullable=True)  # Actual contest date
    location = Column(String, nullable=True)  # Where contest was held
    num_participants = Column(Integer, nullable=True)
    
    # File URLs for this specific year
    problems_pdf_url = Column(String, nullable=True)
    solutions_pdf_url = Column(String, nullable=True)
    problems_tex_url = Column(String, nullable=True)
    solutions_tex_url = Column(String, nullable=True)
    aops_problems_url = Column(String, nullable=True)  # AoPS wiki problems page
    aops_solutions_url = Column(String, nullable=True)  # AoPS wiki solutions page
    
    # Additional contest-specific info
    theme = Column(String, nullable=True)  # e.g., for themed contests
    notes = Column(Text, nullable=True)  # Any special notes about this year
    
    # Relationships
    contest = relationship("Contest", back_populates="years")
    problems = relationship("Problem", back_populates="contest_year")
    
    def __repr__(self):
        return f"<ContestYear {self.contest.name} {self.year}>"

class Problem(Base):
    __tablename__ = "problems"
    
    id = Column(Integer, primary_key=True)
    contest_year_id = Column(Integer, ForeignKey("contest_years.id"), nullable=False)
    
    # Problem identification
    problem_number = Column(Integer, nullable=True)  # 1, 2, 3, etc.
    problem_part = Column(String(10), nullable=True)  # 'A', 'B', 'Day 1', 'Geometry', etc.
    problem_label = Column(String(20), nullable=True)  # 'A1', 'Problem 3', 'Geometry 2', etc.
    
    # Problem metadata
    subject_area = Column(String, nullable=True)  # 'Algebra', 'Geometry', 'Number Theory', 'Combinatorics'
    difficulty_rating = Column(Float, nullable=True)  # 1-10 scale
    time_limit_minutes = Column(Integer, nullable=True)  # Time allotted for this problem
    max_points = Column(Integer, nullable=True)  # Points this problem is worth
    
    # Problem content
    statement = Column(Text, nullable=True)  # Problem statement (preferably LaTeX)
    statement_format = Column(String(10), nullable=True)  # 'latex', 'html', 'plaintext'
    
    # Solution content
    solution = Column(Text, nullable=True)  # Official solution (preferably LaTeX)
    solution_format = Column(String(10), nullable=True)  # 'latex', 'html', 'plaintext'
    
    # Additional solutions from AoPS community
    alternate_solutions = relationship("AlternateSolution", back_populates="problem")
    
    # Source URLs
    aops_problem_url = Column(String, nullable=True)  # Direct AoPS wiki link to this problem
    official_source_url = Column(String, nullable=True)  # Original contest source
    
    # Problem statistics (if available)
    solve_rate = Column(Float, nullable=True)  # Percentage of contestants who solved it
    average_score = Column(Float, nullable=True)  # Average score on this problem
    
    # Content metadata
    has_diagram = Column(Boolean, default=False)  # Whether problem includes diagrams
    requires_proof = Column(Boolean, default=False)  # Whether it's a proof problem
    is_multiple_choice = Column(Boolean, default=False)  # Whether it's multiple choice
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    contest_year = relationship("ContestYear", back_populates="problems")
    
    def __repr__(self):
        return f"<Problem {self.problem_label} ({self.contest_year.contest.name} {self.contest_year.year})>"

class AlternateSolution(Base):
    __tablename__ = "alternate_solutions"
    
    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey("problems.id"), nullable=False)
    
    # Solution metadata
    author = Column(String, nullable=True)  # AoPS username or contributor name
    solution_method = Column(String, nullable=True)  # 'Coordinate Geometry', 'Barycentric', etc.
    difficulty_rating = Column(Float, nullable=True)  # How difficult this solution approach is
    
    # Solution content
    solution_text = Column(Text, nullable=False)
    solution_format = Column(String(10), default='latex')  # 'latex', 'html', 'plaintext'
    
    # Metadata
    is_official = Column(Boolean, default=False)  # Whether this is the official solution
    upvotes = Column(Integer, default=0)  # Community rating
    aops_url = Column(String, nullable=True)  # Link to AoPS discussion
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    problem = relationship("Problem", back_populates="alternate_solutions")
    
    def __repr__(self):
        return f"<AlternateSolution for {self.problem.problem_label} by {self.author}>"

class ContestCategory(Base):
    __tablename__ = "contest_categories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)  # 'Mathematical Olympiads', 'AMC Series', etc.
    description = Column(Text, nullable=True)
    aops_category_url = Column(String, nullable=True)
    
    # Many-to-many relationship with contests
    contests = relationship("Contest", secondary="contest_category_mapping")

class ContestCategoryMapping(Base):
    __tablename__ = "contest_category_mapping"
    
    contest_id = Column(Integer, ForeignKey("contests.id"), primary_key=True)
    category_id = Column(Integer, ForeignKey("contest_categories.id"), primary_key=True)

# Indexes for better query performance
from sqlalchemy import Index

# Create indexes on commonly queried fields
Index('idx_contest_name', Contest.name)
Index('idx_contest_year_year', ContestYear.year)
Index('idx_problem_number', Problem.problem_number)
Index('idx_problem_subject', Problem.subject_area)
Index('idx_problem_difficulty', Problem.difficulty_rating)
