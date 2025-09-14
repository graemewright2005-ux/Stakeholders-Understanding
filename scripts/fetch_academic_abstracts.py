import os
import requests
import re
from pathlib import Path

REFERENCES_FILE = Path("interrogation-materials/references.txt")
OUTPUT_DIR = Path("extracted")
OUTPUT_DIR.mkdir(exist_ok=True)

CROSSREF_API = "https://api.crossref.org/works"
UNPAYWALL_API = "https://api.unpaywall.org/v2"
UNPAYWALL_EMAIL = "graemewright@weston.ac.uk"  # Replace with your real email for polite API use

def search_crossref(reference):
    params = {'query.bibliographic': reference, 'rows': 1}
    try:
        r = requests.get(CROSSREF_API, params=params, timeout=15)
        r.raise_for_status()
        items = r.json().get('message', {}).get('items', [])
        if items:
            return items[0]
        return None
    except Exception as e:
        print(f"Crossref search failed for: {reference}\n{e}")
        return None

def get_unpaywall_data(doi):
    url = f"{UNPAYWALL_API}/{doi}"
    params = {'email': UNPAYWALL_EMAIL}
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Unpaywall failed for DOI {doi}: {e}")
        return None

def safe_filename(text):
    return re.sub(r'[^a-zA-Z0-9]+', '_', text)[:80] + ".txt"

def main():
    if not REFERENCES_FILE.exists():
        print(f"No references file found at {REFERENCES_FILE}")
        return
    with open(REFERENCES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            reference = line.strip()
            if not reference:
                continue
            print(f"Processing: {reference}")
            cr_item = search_crossref(reference)
            if not cr_item:
                print(f"No Crossref match for: {reference}")
                continue
            doi = cr_item.get('DOI', '')
            title = cr_item.get('title', [""])[0]
            abstract = cr_item.get('abstract', '')
            authors = '; '.join([a.get('family', '') + ", " + a.get('given', '') for a in cr_item.get('author', [])]) if cr_item.get('author') else ''
            journal = cr_item.get('container-title', [""])[0]
            year = cr_item.get('published-print', {}).get('date-parts', [[None]])[0][0] or cr_item.get('published-online', {}).get('date-parts', [[None]])[0][0]
            url = cr_item.get('URL', '')
            unpaywall_info = get_unpaywall_data(doi) if doi else None
            oa_link = unpaywall_info['best_oa_location']['url_for_pdf'] if unpaywall_info and unpaywall_info.get('best_oa_location') and unpaywall_info['best_oa_location'].get('url_for_pdf') else ''
            oa_status = unpaywall_info['oa_status'] if unpaywall_info and 'oa_status' in unpaywall_info else 'unknown'

            txt = f"Reference: {reference}\n"
            txt += f"Title: {title}\n"
            txt += f"Authors: {authors}\n"
            txt += f"Journal: {journal}\n"
            txt += f"Year: {year}\n"
            txt += f"DOI: {doi}\n"
            txt += f"Publisher Link: {url}\n"
            txt += f"Open Access: {oa_status}\n"
            if oa_link:
                txt += f"Open Access PDF: {oa_link}\n"
            if abstract:
                # Crossref sometimes returns XML abstracts; strip tags
                txt += f"\nAbstract:\n{re.sub('<.*?>', '', abstract)}\n"
            else:
                txt += "\nAbstract: Not found\n"
            out_path = OUTPUT_DIR / safe_filename(title or reference)
            with open(out_path, "w", encoding="utf-8") as outf:
                outf.write(txt)
            print(f"Saved: {out_path}")

if __name__ == "__main__":
    main()
