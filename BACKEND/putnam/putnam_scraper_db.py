'''
with this code, you do the same processing as in the other file, however 
you do not download files locally, which is good. they are instead sent to the db.

in the db, the url for pdfs are stored, however the url for tex files are
of None type. If this is a problem, we can easily add it, however I think that
the TeX file as is suffices.

non exhaustive list of things to test/try:
- is it normal that there are so many None values for early years?
- do we have duplicates in db if we run scraper multiple times?
- do we want to store tex file urls as well as pdf file urls?
'''

# putnam_scraper.py
import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from putnam_models import Base, Year, Problem

BASE_URL = "https://kskedlaya.org/putnam-archive/"
DB_PATH = "BACKEND/putnam/putnam.sqlite"

# ----------------------------
# DB Setup
# ----------------------------
engine = create_engine(f"sqlite:///{DB_PATH}")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# ----------------------------
# Helpers
# ----------------------------
def get_url(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/127.0.0.0 Safari/537.36"
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp

def get_index_links():
    resp = get_url(BASE_URL)
    soup = BeautifulSoup(resp.text, "html.parser")
    return [urljoin(BASE_URL, a["href"]) for a in soup.find_all("a", href=True)]

def year_from_filename(fname):
    m = re.match(r"(\d{4})(s)?\.(pdf|tex)$", fname.lower())
    if m:
        year = int(m.group(1))
        is_solution = bool(m.group(2))
        return year, is_solution
    return None, None

def fetch_tex_content(url):
    if url is None:
        return ""
    resp = get_url(url)
    resp.raise_for_status()
    return resp.text

def split_problems_from_tex(tex_content):
    # Split by \item[A1], \item[B3], etc.
    pattern = re.compile(r'\\item\[(A|B)([1-6])\]')
    parts = pattern.split(tex_content)
    problems = []
    for i in range(1, len(parts), 3):
        label = f"{parts[i]}{parts[i+1]}"
        body = parts[i+2].strip()
        problems.append({"label": label, "text": body})
    return problems

def add_problems_to_db(sess, year_obj, tex_url):
    tex_content = fetch_tex_content(tex_url)
    if not tex_content:
        return

    problems = split_problems_from_tex(tex_content)
    for p in problems:
        number = int(p["label"][1])
        part = p["label"][0]
        # Avoid duplicates
        exists = sess.query(Problem).filter_by(year_id=year_obj.id, label=p["label"]).first()
        if exists:
            continue
        prob_obj = Problem(
            year=year_obj,
            label=p["label"],
            part=part,
            number=number,
            statement=p["text"],
            solution=None,
            pdf_url=None
        )
        sess.add(prob_obj)
    sess.commit()

# ----------------------------
# Main
# ----------------------------
def main():
    sess = Session()

    print("Fetching index...")
    all_links = get_index_links()

    # Group files by year
    by_year = {}
    for url in all_links:
        fname = os.path.basename(urlparse(url).path)
        year, is_solution = year_from_filename(fname)
        if not year:
            continue
        entry = by_year.setdefault(year, {"problems_pdf": None, "solutions_pdf": None,
                                          "problems_tex": None, "solutions_tex": None})
        if fname.endswith(".pdf"):
            if is_solution:
                entry["solutions_pdf"] = url
            else:
                entry["problems_pdf"] = url
        elif fname.endswith(".tex"):
            if is_solution:
                entry["solutions_tex"] = url
            else:
                entry["problems_tex"] = url

    for year, entry in sorted(by_year.items(), reverse=True):
        print(f"\nProcessing {year}...")

        # Avoid duplicate Year entries
        year_obj = sess.query(Year).filter_by(year=year).first()
        if not year_obj:
            year_obj = Year(
                year=year,
                pdf_url=entry["problems_pdf"],
                solutions_pdf_url=entry["solutions_pdf"],
                problems_tex_url=entry["problems_tex"],
                solutions_tex_url=entry["solutions_tex"]
            )
            sess.add(year_obj)
            sess.commit()

        # Add Problem rows from TeX
        add_problems_to_db(sess, year_obj, entry["problems_tex"])

    print("\nDone. DB saved to putnam.sqlite")

if __name__ == "__main__":
    main()
