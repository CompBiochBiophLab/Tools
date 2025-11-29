# petita eina generada amb chatgPT i modificada per poder llegir publicacions d'investigadors a ORCID
# i guardar-les en un CSV, evitant duplicats basats en DOI

import csv
import requests
from datetime import datetime
import os

def obtenir_publicacions_orcid(orcid, any_inici=2022):
    base_url = "https://pub.orcid.org/v3.0/"
    headers = {"Accept": "application/json"}
    resultats = []

    # Crida inicial: llista d'obres
    url = f"{base_url}{orcid}/works"
    res = requests.get(url, headers=headers)

    if res.status_code != 200:
        print(f"Error accedint a ORCID {orcid}: {res.status_code}")
        return resultats

    dades = res.json()
    items = dades.get("group", [])
    
    for grp in items:
        work = grp.get("work-summary", [{}])[0]

        # --- DATA ---
        date = work.get("publication-date")
        if not date or not isinstance(date, dict):
            continue
        year = date.get("year", {}).get("value")
        if not year or not str(year).isdigit():
            continue

        year = int(year)
        if year < any_inici:
            continue

        # --- TITOL ---
        titol = (
            work.get("title", {})
            .get("title", {})
            .get("value", "Sense títol")
        )

        # --- PUTCODE (per obtenir DOI i revista) ---
        putcode = work.get("put-code")
        details_url = f"{base_url}{orcid}/work/{putcode}"
        details = requests.get(details_url, headers=headers).json()

        # --- DOI ---
        external_ids = details.get("external-ids", {}).get("external-id", [])
        doi = None
        for ext in external_ids:
            if ext.get("external-id-type") == "doi":
                doi = ext.get("external-id-value")
        
        # --- REVISTA / CONTAINER TITLE ---
        journal = details.get("journal-title")
        if isinstance(journal, dict):
            revista = journal.get("value")
        else:
            revista = None

        if not revista:
        # Provar altres camps possibles
            titulo = details.get("title", {})
            if isinstance(titulo, dict):
                subt = titulo.get("subtitle")
            if isinstance(subt, dict):
                revista = subt.get("value")

        if not revista:
            revista = "Desconegut"

        resultats.append({
            "títol": titol,
            "revista": revista,
            "doi": doi,
            "any": year
        })

    return resultats


def eliminar_duplicats_per_doi(llista):
    """
    Rep una llista de dicts amb claus:
    nom, títol, revista, doi, any
    i elimina duplicats basats en DOI.
    """
    vistos = set()
    resultat = []

    for item in llista:
        doi = item.get("doi")
        if not doi:
            # Si no hi ha DOI, afegim l'entrada igualment
            resultat.append(item)
            continue

        if doi in vistos:
            continue  # ja existeix → saltar
        vistos.add(doi)
        resultat.append(item)

    return resultat


# ------------------------------------------------------------------------
# ❗ FITXERS D'ENTRADA / SORTIDA (ubicats dins la carpeta indicada per $SCRATCH)
# INPUT: CSV amb camps
# nom,orcid
# Jordi Villà-Freixa,0000-0002-6359-3929

scratch = os.environ.get("SCRATCH")
if not scratch:
    raise RuntimeError("La variable d'entorn SCRATCH no està definida")

scratch = os.path.abspath(os.path.expanduser(scratch))
os.makedirs(scratch, exist_ok=True)

INPUT = os.path.join(scratch, "investigadors.csv")
OUTPUT = os.path.join(scratch, "publicacions_orcid.csv")


def main():
    # Llegeix investigadors i ORCIDs
    investigadors = []
    with open(INPUT, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "nom" in row and "orcid" in row:
                nom = row["nom"].strip()
                orcid = row["orcid"].strip()
                investigadors.append((nom, orcid))

    # Preparar llista completa de publicacions
    totes_pub = []

    for nom, orcid in investigadors:
        print(f"Processant {nom} ({orcid})...")
        pubs = obtenir_publicacions_orcid(orcid)
        for p in pubs:
            p["nom"] = nom  # afegir el nom
            totes_pub.append(p)

    # Eliminar duplicats basats en DOI
    totes_pub = eliminar_duplicats_per_doi(totes_pub)

    # Escriure CSV de sortida
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["nom", "títol", "revista", "doi", "any"])
        for p in totes_pub:
            writer.writerow([
                p["nom"],
                p["títol"],
                p["revista"],
                p["doi"] if p["doi"] else "",
                p["any"]
            ])

    print(f"\n✔ Resultats guardats a: {OUTPUT}")


if __name__ == "__main__":
    main()
