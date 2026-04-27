#!/usr/bin/env python3
"""Validate user-selected PDB entries against FASTA sequences.

The mapping CSV must contain at least two columns: seq_id,pdb_id. The script
checks every polymer entity in each PDB entry and reports the best matching
entity for the corresponding FASTA sequence.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd

from protein_sequence_report import hit_from_entity, parse_fasta, polymer_entity_ids


def read_mapping(path: str | Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or "seq_id" not in rows[0] or "pdb_id" not in rows[0]:
        raise ValueError("Mapping CSV must contain seq_id and pdb_id columns")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate selected PDB entries for FASTA sequences.")
    parser.add_argument("fasta", help="Input protein FASTA file.")
    parser.add_argument("mapping_csv", help="CSV with columns seq_id,pdb_id.")
    parser.add_argument("--output", default="pdb_choice_validation.csv", help="Output CSV path.")
    parser.add_argument("--id-source", choices=["auto", "record_id", "description", "first_token", "last_token", "index"], default="auto", help="How to name records from FASTA headers. Default auto uses useful unique header tokens when possible; use last_token for headers such as >JC A, or index to ignore titles.")
    args = parser.parse_args()

    records = {record["id"]: record for record in parse_fasta(args.fasta, id_source=args.id_source)}
    rows = []
    for item in read_mapping(args.mapping_csv):
        seq_id = item["seq_id"]
        pdb_id = item["pdb_id"].upper()
        if seq_id not in records:
            raise KeyError(f"Sequence {seq_id!r} not found in FASTA")
        query = records[seq_id]["sequence"]
        best = None
        for entity_id in polymer_entity_ids(pdb_id):
            hit = hit_from_entity(query, pdb_id, entity_id)
            if best is None or hit.alignment.score > best.alignment.score:
                best = hit
        if best is None:
            rows.append({"seq_id": seq_id, "pdb_id": pdb_id, "error": "no polymer entities found"})
            continue
        aln = best.alignment
        rows.append({
            "seq_id": seq_id,
            "pdb_id": pdb_id,
            "best_entity": best.entity_id,
            "description": best.description,
            "title": best.title,
            "chains": ";".join(best.chains),
            "resolution": best.resolution,
            "query_coverage": aln.query_coverage,
            "entity_coverage": aln.target_coverage,
            "identity": aln.identity,
            "query_region": f"{aln.query_start}-{aln.query_end}",
            "entity_region": f"{aln.target_start}-{aln.target_end}",
            "uniprot_refs": ";".join(best.uniprot_refs),
            "flags": ";".join(best.flags),
        })
    pd.DataFrame(rows).to_csv(args.output, index=False)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
