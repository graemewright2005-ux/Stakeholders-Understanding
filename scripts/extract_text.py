import os
from pathlib import Path
import PyPDF2
import docx

INPUT_DIR = Path("interrogation-materials")
OUTPUT_DIR = Path("extracted")
OUTPUT_DIR.mkdir(exist_ok=True)

def extract_pdf_text(pdf_path):
    text = ""
    with open(pdf_path, "rb") as f:
        try:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        except Exception as e:
            print(f"Failed to extract {pdf_path}: {e}")
    return text

def extract_docx_text(docx_path):
    text = ""
    try:
        doc = docx.Document(docx_path)
        text = "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        print(f"Failed to extract {docx_path}: {e}")
    return text

for file in INPUT_DIR.iterdir():
    if file.suffix.lower() == ".pdf":
        txt = extract_pdf_text(file)
        out_file = OUTPUT_DIR / (file.stem + ".txt")
        out_file.write_text(txt, encoding="utf-8")
        print(f"Extracted {file} -> {out_file}")
    elif file.suffix.lower() == ".docx":
        txt = extract_docx_text(file)
        out_file = OUTPUT_DIR / (file.stem + ".txt")
        out_file.write_text(txt, encoding="utf-8")
        print(f"Extracted {file} -> {out_file}")
