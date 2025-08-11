"""
putnam_scraper.py

Usage:
    python putnam_scraper.py
"""
import os
import re
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import pdfplumber
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from tqdm import tqdm
import time

BASE_URL = "https://kskedlaya.org/putnam-archive/"
DOWNLOAD_DIR = "pdfs"
DB_PATH = "sqlite:///putnam.sqlite"

# SQLAlchemy setup
Base = declarative_base()

class Year(Base):
    __tablename__ = "years"
    id = Column(Integer, primary_key=True)
    year = Column(String, unique=True, nullable=False)
    pdf_url = Column(String)
    solutions_pdf_url = Column(String)
    problems = relationship("Problem", back_populates="year_obj")

class Problem(Base):
    __tablename__ = "problems"
    id = Column(Integer, primary_key=True)
    year_id = Column(Integer, ForeignKey("years.id"), index=True)
    part = Column(String)   # 'A' or 'B' (or None if unknown)
    number = Column(Integer, nullable=True)   # 1..6 (or None)
    label = Column(String)  # e.g., 'A1' or 'B6' or raw label
    statement = Column(Text)
    solution = Column(Text)
    pdf_url = Column(String)
    page_range = Column(String)  # optional: "3-4"
    year_obj = relationship("Year", back_populates="problems")
    __table_args__ = (UniqueConstraint("year_id", "label", name="_year_label_uc"),)

engine = create_engine(DB_PATH, echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/115.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive"
}

def get_index_links():
    resp = requests.get(BASE_URL, headers=HEADERS)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    pdf_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.lower().endswith(".pdf"):
            pdf_links.append(urljoin(BASE_URL, href))
    return sorted(set(pdf_links))

def download_file(url, dest_folder=DOWNLOAD_DIR, chunk_size=1024):
    os.makedirs(dest_folder, exist_ok=True)
    local_name = os.path.join(dest_folder, os.path.basename(urlparse(url).path))
    if os.path.exists(local_name):
        return local_name
    with requests.get(url, stream=True, headers={"User-Agent":"Mozilla/5.0"}) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        with open(local_name, "wb") as f, tqdm(total=total, unit="B", unit_scale=True, desc=os.path.basename(local_name)) as pbar:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
    # small delay to be polite
    time.sleep(0.5)
    return local_name

def extract_pdf_text(path):
    """Return list of page texts (page 1 at index 0)."""
    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages.append(text)
    return pages

# Heuristics to parse problem PDFs:
PROB_LABEL_RE = re.compile(
    r'^\s*([AB])\s*([1-6])\b|^\s*(A|B)([1-6])\b|^\s*((?:A|B)[1-6])\b',
    re.IGNORECASE | re.MULTILINE
)
# Another pattern: "Problem 1." or "A1." or "A1)"
GENERIC_PROB_RE = re.compile(r'^\s*(?:Problem\s*)?([AB]?[1-6])[\.\)]\s*', re.IGNORECASE)

def split_problems_from_text(full_text):
    """
    Attempt to split a problem PDF text into dicts: [{'label':'A1','text':...}, ...]
    This is heuristic: some PDFs format differently; fallback returns entire text as one block.
    """
    # Normalize: replace multiple newlines with single marker to make regex stable
    # we'll attempt to find occurrences of A1, A2, ..., B6
    labels = []
    for part in ("A", "B"):
        for n in range(1,7):
            labels.append(f"{part}{n}")
    # Build pattern that finds labels like 'A1.' or 'A1)' or 'A1 ' at line start
    pattern = re.compile(r'(?m)^\s*(' + "|".join(labels) + r')[\.\)\s-]+', re.IGNORECASE)
    matches = list(pattern.finditer(full_text))
    if not matches:
        # fallback: try generic 'Problem 1' style followed by 1..12 (older formats)
        fallback = re.compile(r'(?m)^\s*Problem\s+([1-9]|1[0-2])[\.\)]\s*', re.IGNORECASE)
        fm = list(fallback.finditer(full_text))
        if not fm:
            return None  # can't split
        # create labels 1..n
        items = []
        for i, m in enumerate(fm):
            start = m.start()
            end = fm[i+1].start() if i+1 < len(fm) else len(full_text)
            label = f"P{m.group(1)}"
            items.append({"label": label, "text": full_text[start:end].strip()})
        return items

    items = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i+1].start() if i+1 < len(matches) else len(full_text)
        label = m.group(1).upper()
        items.append({"label": label, "text": full_text[start:end].strip()})
    return items

def pair_problem_and_solution(problem_items, solution_items):
    """Match problem labels like A1..B6 to solutions by label; returns dict label->(pb_text, sol_text)"""
    sol_map = {it['label'].upper(): it['text'] for it in (solution_items or [])}
    paired = []
    for p in (problem_items or []):
        lab = p['label'].upper()
        pb = p['text']
        sol = sol_map.get(lab)
        paired.append((lab, pb, sol))
    return paired

def year_from_pdfname(name):
    # assumes filenames like '2024.pdf' or '2024s.pdf'
    m = re.search(r'(\d{4})', name)
    return m.group(1) if m else None

def main():
    sess = Session()
    print("Finding PDF links on the index page...")
    pdf_links = get_index_links()
    # Filter to files that look like year PDFs (e.g., 2019.pdf, 2019s.pdf, 2024.pdf)
    pdf_links = [u for u in pdf_links if re.search(r'/\d{4}(?:s)?\.pdf$', u)]
    print(f"Found {len(pdf_links)} year PDFs (problems & solutions).")
    # group problem pdf and solutions pdf by year
    by_year = {}
    for url in pdf_links:
        fname = os.path.basename(urlparse(url).path)
        y = year_from_pdfname(fname)
        if not y:
            continue
        entry = by_year.setdefault(y, {"problems": None, "solutions": None})
        if fname.lower().endswith("s.pdf"):
            entry["solutions"] = url
        else:
            entry["problems"] = url

    for year, entry in sorted(by_year.items(), reverse=True):
        print(f"\nProcessing year {year} ...")
        problems_url = entry["problems"]
        sols_url = entry["solutions"]

        # record year in DB
        year_obj = sess.query(Year).filter_by(year=year).first()
        if not year_obj:
            year_obj = Year(year=year, pdf_url=problems_url, solutions_pdf_url=sols_url)
            sess.add(year_obj)
            sess.commit()

        # Download PDFs
        if problems_url:
            p_local = download_file(problems_url)
            pages_p = extract_pdf_text(p_local)
            full_text_p = "\n\n".join(pages_p)
            problem_items = split_problems_from_text(full_text_p)
        else:
            problem_items = None
        if sols_url:
            s_local = download_file(sols_url)
            pages_s = extract_pdf_text(s_local)
            full_text_s = "\n\n".join(pages_s)
            solution_items = split_problems_from_text(full_text_s)
        else:
            solution_items = None

        # If split_problems_from_text returned None for either, keep fallback: try to split by "A1 A2 ... B6" sequence
        if problem_items is None and full_text_p:
            # naive fallback: attempt to split by 'A1', 'A2', ... presence anywhere
            items = []
            # try pattern that captures 'A1' labels even inline
            for part in ("A", "B"):
                for n in range(1,7):
                    label = f"{part}{n}"
                    idx = full_text_p.find(label)
                    if idx != -1:
                        items.append({"label": label, "text": ""})  # we will fill later
            if items:
                # crude strategy: split by label occurrences
                pattern = re.compile(r'(?m)(' + "|".join([re.escape(it['label']) for it in items]) + r')', re.IGNORECASE)
                splits = pattern.split(full_text_p)
                assembled = []
                # splits will alternate between text and labels; reconstruct
                i = 1
                while i < len(splits):
                    lab = splits[i].strip()
                    body = splits[i+1] if i+1 < len(splits) else ""
                    assembled.append({"label": lab.upper(), "text": (lab + " " + body).strip()})
                    i += 2
                if assembled:
                    problem_items = assembled

        # Now pair problems to solutions
        paired = pair_problem_and_solution(problem_items or [], solution_items or [])

        # store into DB
        for lab, pb_text, sol_text in paired:
            # parse label into part/number
            m = re.match(r'([AB])([1-6])', lab, re.IGNORECASE)
            part = None; number = None
            if m:
                part = m.group(1).upper()
                number = int(m.group(2))
            # upsert problem
            existing = sess.query(Problem).filter_by(year_id=year_obj.id, label=lab).first()
            if existing:
                updated = False
                if pb_text and existing.statement != pb_text:
                    existing.statement = pb_text
                    updated = True
                if sol_text and existing.solution != sol_text:
                    existing.solution = sol_text
                    updated = True
                if updated:
                    sess.add(existing)
            else:
                p = Problem(
                    year_id=year_obj.id,
                    part=part,
                    number=number,
                    label=lab,
                    statement=pb_text,
                    solution=sol_text,
                    pdf_url=problems_url
                )
                sess.add(p)
        sess.commit()
        print(f"Stored {len(paired)} problems for year {year}.")
    print("\nDone. DB saved to putnam.sqlite")

if __name__ == "__main__":
    main()
