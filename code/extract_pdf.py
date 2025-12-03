import os
import fitz  # PyMuPDF
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
from math import ceil
import camelot
import pdfplumber
import pandas as pd
from pathlib import Path
import re
import pymupdf4llm
from typing import Tuple
import traceback

INPUT_DIR = "data"
OUTPUT_DIR = "extracted_new"
N_WORKERS = None          # set e.g. to 8 to cap, else auto
SKIP_EXISTING = True      # set False to overwrite


def clean_hyphenation(text: str) -> str:
    # join words split across lines with hyphenation (common in Greek PDFs)
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
    # normalize multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

def process_batch(file_batch):
    for filename in file_batch:
        pdf_path = os.path.join(input_dir, filename)
        txt_path = os.path.join(output_dir, filename.rsplit(".", 1)[0] + ".txt")

        try:
            doc = fitz.open(pdf_path)
            text = "\n".join([page.get_text() for page in doc])
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception as e:
            print(f"Failed: {filename} – {e}")

def chunkify(lst, n):
    """Split list `lst` into `n` roughly equal chunks."""
    return [lst[i::n] for i in range(n)]


def clean_hyphenation(text: str) -> str:
    # join Greek (and general) words broken by hyphen at line end
    return re.sub(r'(\w)-\n(\w)', r'\1\2', text)

def extract_tables_markdown(pdf_path: str):
    tables_per_page = {}
    # Try Camelot lattice → stream
    try:
        cam = camelot.read_pdf(pdf_path, pages="all", flavor="lattice")
        if len(cam) == 0:
            cam = camelot.read_pdf(pdf_path, pages="all", flavor="stream")
        for t in cam:
            page = t.page
            md = t.df.to_markdown(index=False)
            tables_per_page.setdefault(page, []).append(md)
    except Exception:
        pass

    # Fallback with pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            if i in tables_per_page:
                continue
            tbls = page.extract_tables()
            if not tbls:
                continue
            md_list = []
            for tbl in tbls:
                df = pd.DataFrame(tbl[1:], columns=tbl[0]) if len(tbl) > 1 else pd.DataFrame(tbl)
                md_list.append(df.to_markdown(index=False))
            if md_list:
                tables_per_page[i] = md_list
    return tables_per_page

# Optional: silence MuPDF spam in console
# ------------------------------------------------------------------
#  -- optional: hide MuPDF spam --
try:
    fitz.TOOLS.mupdf_display_errors(False)
except AttributeError:
    # older PyMuPDF: fall back to lowering verbosity
    try:
        fitz.TOOLS.set_verbosity(0)
    except Exception:
        pass


def remove_surrogates(text: str) -> str:
    """Strip illegal lone UTF‑16 surrogate code points (\uD800–\uDFFF)."""
    return re.sub(r'[\ud800-\udfff]', '', text)

def safe_write_utf8(path: Path, text: str):
    """
    Write text as UTF‑8 but never crash on bad code points.
    Method: strip surrogates, then allow backslash escapes for anything
    that still fails.
    """
    clean = remove_surrogates(text)
    with open(path, "w", encoding="utf-8", errors="backslashreplace") as f:
        f.write(clean)

def safe_plain_markdown(pdf_path: str) -> str:
    """Fallback: use PyMuPDF's own markdown/text extractor per page."""
    parts = []
    with fitz.open(pdf_path) as doc:
        for p in doc:
            try:
                parts.append(p.get_text("markdown"))
            except Exception:
                parts.append(p.get_text("text"))
    return "\n\n---\n\n".join(parts)

def pdf_to_markdown_with_pymupdf4llm(pdf_path: str) -> str:
    """Primary extractor with fallback when MuPDF chokes on JPX images."""
    try:
        with fitz.open(pdf_path) as doc:
            return pymupdf4llm.to_markdown(doc)
    except Exception as e:
        # JPX / image related crashes commonly land here
        return safe_plain_markdown(pdf_path)

def process_file(args):
    pdf_name, in_dir, out_dir, skip = args
    in_fp  = Path(in_dir)  / pdf_name
    out_fp = Path(out_dir) / (Path(pdf_name).stem + ".md")

    try:
        if skip and out_fp.exists():
            return (pdf_name, True, "skipped")

        md = pdf_to_markdown_with_pymupdf4llm(str(in_fp))
        safe_write_utf8(out_fp, md)                  # ← 2. safe writer
        return (pdf_name, True, "")

    except Exception as e:
        return (
            pdf_name,
            False,
            f"{type(e).__name__}: {e}\n{traceback.format_exc()}",   # uses traceback now
        )

def main(input_dir: str, output_dir: str, n_workers=None, skip_existing=True):
    input_dir = str(Path(input_dir).resolve())
    output_dir = str(Path(output_dir).resolve())
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    all_pdfs = [f for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]
    if not all_pdfs:
        print("No PDF files found.")
        return

    # n_workers = n_workers or min(cpu_count(), len(all_pdfs))
    n_workers = 10
    print(n_workers)
    print(f"Found {len(all_pdfs)} PDFs")
    print(f"Using {n_workers} workers")

    tasks = [(f, input_dir, output_dir, skip_existing) for f in all_pdfs]

    ok = fail = 0
    errors = []

    with Pool(processes=n_workers) as pool:
        for fname, success, err in tqdm(
            pool.imap_unordered(process_file, tasks),
            total=len(tasks),
            desc="PDFs",
        ):
            if success:
                ok += 1
            else:
                fail += 1
                errors.append((fname, err))

    print(f"\nDone. OK: {ok}, Failed: {fail}")
    if errors:
        print("\nErrors:")
        for f, e in errors:
            print(f"--- {f} ---")
            print(e)

if __name__ == "__main__":
    INPUT_DIR = "data"
    OUTPUT_DIR = "extracted_new"
    N_WORKERS = None
    SKIP_EXISTING = True
    main(INPUT_DIR, OUTPUT_DIR, N_WORKERS, skip_existing=SKIP_EXISTING)