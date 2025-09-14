import re
import requests
from pathlib import Path
from bs4 import BeautifulSoup
import PyPDF2
import tempfile
import os

URLS_FILE = Path("interrogation-materials/urls-to-fetch.txt")
OUTPUT_DIR = Path("extracted")
OUTPUT_DIR.mkdir(exist_ok=True)

def fetch_html(url):
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        return text[:200000]  # Limit to first 200K chars just in case
    except Exception as e:
        return f"ERROR fetching HTML from {url}: {e}"

def fetch_pdf(url):
    try:
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                temp_pdf_path = f.name
        text = ""
        with open(temp_pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        os.remove(temp_pdf_path)
        return text[:200000]
    except Exception as e:
        return f"ERROR fetching PDF from {url}: {e}"

def fetch_youtube(url):
    return f"YOUTUBE VIDEO: {url}\nPlease view the content manually or use a transcript extraction tool."

def fetch_unknown(url):
    return f"UNSUPPORTED OR RESTRICTED CONTENT: {url}\nManual review may be required."

def url_to_filename(url):
    safe = re.sub(r'[^a-zA-Z0-9]', '_', url)
    return safe[:100] + ".txt"

def main():
    if not URLS_FILE.exists():
        print("No URL file found.")
        return
    with open(URLS_FILE, "r") as f:
        for line in f:
            url = line.strip()
            if not url:
                continue
            print(f"Processing: {url}")
            if url.endswith(".pdf"):
                text = fetch_pdf(url)
            elif "youtube.com" in url or "youtu.be" in url:
                text = fetch_youtube(url)
            elif re.search(r"\.pdf(\?|$)", url):
                text = fetch_pdf(url)
            elif url.startswith("http"):
                text = fetch_html(url)
            else:
                text = fetch_unknown(url)
            out_file = OUTPUT_DIR / url_to_filename(url)
            with open(out_file, "w", encoding="utf-8") as outf:
                outf.write(f"URL: {url}\n\n{text}")
            print(f"Saved: {out_file}")

if __name__ == "__main__":
    main()
