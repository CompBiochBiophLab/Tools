#!/usr/bin/env python3
"""Generate protein sequence tools from a FASTA file."""
from __future__ import annotations

import argparse
from pathlib import Path

from protein_sequence_report import analyse_record, parse_fasta, write_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyse protein FASTA records and generate sequence/structure reports.")
    parser.add_argument("fasta", help="Input protein FASTA file, with one or more records.")
    parser.add_argument("--output-dir", default="protein_sequence_report_results", help="Directory for reports and summaries.")
    parser.add_argument("--top-pdb", type=int, default=10, help="Number of RCSB sequence hits to inspect per sequence.")
    parser.add_argument("--identity-cutoff", type=float, default=0.25, help="RCSB sequence-search identity cutoff.")
    parser.add_argument("--evalue-cutoff", type=float, default=10.0, help="RCSB sequence-search E-value cutoff.")
    parser.add_argument("--id-source", choices=["auto", "record_id", "description", "first_token", "last_token", "index"], default="auto", help="How to name records from FASTA headers. Default auto uses useful unique header tokens when possible; use last_token for headers such as >JC A, or index to ignore titles.")
    args = parser.parse_args()

    records = parse_fasta(args.fasta, id_source=args.id_source)
    results = []
    for record in records:
        print(f"Analysing {record['id']} ({len(record['sequence'])} aa)")
        results.append(analyse_record(record, args.top_pdb, args.identity_cutoff, args.evalue_cutoff))
    write_outputs(results, Path(args.output_dir))
    print(f"Wrote reports to {args.output_dir}")


if __name__ == "__main__":
    main()
