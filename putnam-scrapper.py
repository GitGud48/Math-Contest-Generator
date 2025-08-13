import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Year, Problem  # Your existing models
import pdfplumber

BASE_URL = "https://kskedlaya.org/putnam-archive/"
DB_PATH = "putnam.sqlite"

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
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    return [urljoin(BASE_URL, a["href"]) for a in soup.find_all("a", href=True)]

def year_from_filename(fname):
    m = re.match(r"(\d{4})(s)?\.(pdf|tex)$", fname.lower())
    if m:
        year = int(m.group(1))
        is_solution = bool(m.group(2))
        return year, is_solution
    return None, None

def download_file(url):
    local_name = os.path.basename(urlparse(url).path)
    resp = get_url(url)
    resp.raise_for_status()
    with open(local_name, "wb") as f:
        f.write(resp.content)
    return local_name

def extract_pdf_text(path):
    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages.append(text)
    return "\n\n".join(pages)

def extract_tex_text(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def split_problems_from_tex(tex_content):
    # You can refine this — for now, split by \item[A1], etc.
    pattern = re.compile(r'\\item\[(A|B)([1-6])\]')
    parts = pattern.split(tex_content)
    problems = []
    for i in range(1, len(parts), 3):
        label = f"{parts[i]}{parts[i+1]}"
        body = parts[i+2].strip()
        problems.append({"label": label, "text": body})
    return problems

def pair_problem_and_solution(problems, solutions):
    sol_map = {p["label"]: p["text"] for p in solutions}
    return [(p["label"], p["text"], sol_map.get(p["label"], "")) for p in problems]

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

        year_obj = sess.query(Year).filter_by(year=year).first()
        if not year_obj:
            year_obj = Year(year=year,
                            pdf_url=entry["problems_pdf"],
                            solutions_pdf_url=entry["solutions_pdf"])
            sess.add(year_obj)
            sess.commit()

        # Prefer TEX over PDF
        if entry["problems_tex"]:
            local = download_file(entry["problems_tex"])
            problem_items = split_problems_from_tex(extract_tex_text(local))
        elif entry["problems_pdf"]:
            local = download_file(entry["problems_pdf"])
            problem_items = [{"label": None, "text": extract_pdf_text(local)}]
        else:
            problem_items = []

        if entry["solutions_tex"]:
            local = download_file(entry["solutions_tex"])
            solution_items = split_problems_from_tex(extract_tex_text(local))
        elif entry["solutions_pdf"]:
            local = download_file(entry["solutions_pdf"])
            solution_items = [{"label": None, "text": extract_pdf_text(local)}]
        else:
            solution_items = []

        paired = pair_problem_and_solution(problem_items, solution_items)

        for lab, pb_text, sol_text in paired:
            m = re.match(r'([AB])([1-6])', lab or "")
            part, number = (m.group(1), int(m.group(2))) if m else (None, None)

            existing = sess.query(Problem).filter_by(year_id=year_obj.id, label=lab).first()
            if existing:
                existing.statement = pb_text
                existing.solution = sol_text
            else:
                p = Problem(
                    year_id=year_obj.id,
                    part=part,
                    number=number,
                    label=lab,
                    statement=pb_text,
                    solution=sol_text,
                    pdf_url=entry["problems_tex"] or entry["problems_pdf"]
                )
                sess.add(p)

        sess.commit()
        print(f"Stored {len(paired)} problems for {year}.")

    print("\nDone. DB saved to putnam.sqlite")

if __name__ == "__main__":
    main()