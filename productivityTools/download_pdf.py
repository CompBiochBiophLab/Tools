import requests
import bibtexparser
import sys

def fetch_bibtex(doi):
    url = f"https://doi.org/{doi}"
    headers = {"Accept": "application/x-bibtex"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to fetch BibTeX for DOI: {doi}")
        return None

def generate_bib_file(doi_file, output_bib):
    bib_entries = []
    with open(doi_file, 'r') as f:
        dois = [line.strip() for line in f if line.strip()]
    for doi in dois:
        bibtex = fetch_bibtex(doi)
        if bibtex:
            bib_entries.append(bibtex)
    with open(output_bib, 'w') as out:
        out.write('\n\n'.join(bib_entries))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python download_pdf.py <doi_file.txt> <output.bib>")
    else:
        generate_bib_file(sys.argv[1], sys.argv[2])