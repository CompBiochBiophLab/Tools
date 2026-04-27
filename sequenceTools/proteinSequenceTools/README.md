# Protein sequence tools

This subfolder contains command-line tools for protein FASTA analysis. The scripts are generic: they accept a single protein sequence or a multi-FASTA collection and do not assume any specific dataset, organism, protein family or assignment.

The tools are designed to help move from an input sequence to a defensible sequence-structure-function interpretation using standard bioinformatics libraries and public biological database APIs. They gather local sequence descriptors, experimental structure candidates, database cross-references and residue-level annotations, then write human-readable and machine-readable reports. They do not call ChatGPT, Codex, OpenAI APIs or any generative model.

## Contents

- `analyze_fasta.py`: main command-line workflow. It reads protein FASTA records, searches RCSB PDB by sequence, fetches structural and functional annotations, and writes reports.
- `validate_pdb_choice.py`: checks whether user-selected PDB entries actually match the input sequences. Useful when a PDB has already been chosen manually.
- `protein_sequence_report.py`: shared implementation used by the command-line scripts. It contains FASTA parsing, Biopython descriptors, sequence alignment, RCSB/UniProt/AlphaFold helpers and report generation.
- `requirements.txt`: minimal Python requirements for pip-based installation.
- `environment.yml`: conda environment for this subfolder.

## Installation

Recommended conda workflow from the repository root:

```bash
conda env create -f sequenceTools/proteinSequenceTools/environment.yml
conda activate tools-protein-sequence-tools
```

Equivalent from this subfolder:

```bash
conda env create -f environment.yml
conda activate tools-protein-sequence-tools
```

For pip-only environments:

```bash
python3 -m pip install -r requirements.txt
```

The scripts use internet resources through public bioinformatics APIs. RCSB PDB, UniProt and AlphaFold DB requests require network access.

## Data sources and APIs

The workflow is a Python wrapper around common bioinformatics resources. It is intentionally transparent: every reported identifier, annotation or structure candidate should be traceable to one of these sources.

- Biopython: FASTA parsing, protein descriptors and pairwise sequence alignment with BLOSUM62.
- RCSB PDB Search API: sequence search against experimental protein structures.
- RCSB PDB Data API: PDB entry/entity/chain metadata, SIFTS-UniProt cross-references, non-polymer ligands, chain features and domain annotations exposed by RCSB.
- UniProt REST API: protein names, gene names, EC numbers, function comments, catalytic activity, variants, PTMs and residue features.
- AlphaFold DB API: links to AlphaFold DB predictions for UniProt accessions.
- BRENDA: manual EC-number follow-up links when EC numbers are retrieved from UniProt/PDB metadata.
- ChimeraX/DSSP or equivalent structural viewers are still needed for visual validation of hydrogen bonds, contacts, active sites and biological assemblies.

The scripts do not use generative AI services. They only automate reproducible calls to the resources above and local sequence calculations.

## Main workflow

Generate reports for all sequences in a FASTA file:

```bash
python3 analyze_fasta.py input_sequences.fasta --output-dir results
```

Common options:

```bash
python3 analyze_fasta.py input_sequences.fasta \
  --output-dir results \
  --top-pdb 10 \
  --identity-cutoff 0.25 \
  --evalue-cutoff 10 \
  --id-source auto
```

`--id-source auto` tries to choose useful unique identifiers from FASTA headers. If headers are ambiguous or look like titles rather than identifiers, it falls back to stable names such as `sequence_1`, `sequence_2`, etc.

Identifier options:

- `auto`: default; choose useful unique IDs when possible.
- `record_id`: Biopython's FASTA record ID, normally the first header token.
- `first_token`: first whitespace-separated token in the header.
- `last_token`: last whitespace-separated token in the header. Useful for headers such as `>JC A`.
- `description`: sanitized full FASTA description.
- `index`: ignore headers and name records `sequence_1`, `sequence_2`, etc.

## Outputs

The main workflow writes:

- `summary.csv`: compact table with one row per sequence.
- `summary.json`: complete structured output for downstream processing.
- `reports/<sequence_id>.md`: detailed Markdown report for each sequence.

Each report contains:

- Basic sequence descriptors: length, molecular weight, pI, GRAVY, amino-acid composition summaries, cysteines, ambiguous residues and common tags.
- Recommended PDB structure candidates ranked by sequence coverage, identity, resolution and construct relevance.
- PDB entity, chain, method, resolution, coverage and identity.
- RCSB links and SIFTS/UniProt references when available.
- UniProt mappings for all polymer entities in the selected PDB entry. This separates the query entity from peptide partners, fusion partners or other chains in the same structure.
- UniProt-derived gene names, protein names, EC numbers, functional comments, catalytic activity, PTM comments, variants and selected residue features.
- BRENDA lookup links when EC numbers are available.
- AlphaFold DB links when a UniProt accession is available.
- PDB ligands/cofactors/inhibitors from non-polymer entities.
- Secondary-structure features and domain/fold annotations exposed by RCSB for the inspected chain, including CATH, ECOD, SCOP/SCOP2 or Pfam when mapped.
- Fusion/chimeric construct sections when RCSB/SIFTS maps a polymer entity to two or more UniProt components; each component is reported separately with coverage, function and EC/PTM cautions.
- A checklist for mapping active-site residues, variants and post-translational modifications onto the input-sequence numbering.

## Validating selected PDB entries

If PDB entries have already been selected, create a CSV file like this:

```csv
seq_id,pdb_id
A,8T5E
B,8YL8
```

Then run:

```bash
python3 validate_pdb_choice.py input_sequences.fasta chosen_pdbs.csv \
  --id-source auto \
  --output pdb_choice_validation.csv
```

The output reports the best matching polymer entity for each sequence/PDB pair, including chain identifiers, sequence identity, query coverage, entity coverage and flags such as partial match, fusion/chimera or designed construct.

## Interpreting the reports

Use the report as a structured starting point, not as a replacement for manual inspection. In particular:

- If the best PDB hit has low coverage or low identity, treat it as a homolog or scaffold, not as the exact sequence.
- If a PDB entity contains multiple UniProt references, treat it as a possible fusion/chimeric construct and discuss each component separately. Do not transfer EC numbers, active sites, variants or PTMs from one component to another.
- If a sequence is a designed or engineered construct, separate the natural scaffold function from the engineered construct function.
- If the selected PDB entry links to UniProt through another polymer entity, report that entity as a partner. Do not present the partner UniProt accession as the UniProt identity of the input sequence unless the input sequence itself maps to that entity.
- If UniProt annotations come from a related or non-recommended PDB hit, treat them as context until the alignment has been justified.
- Validate hydrogen bonds, van der Waals contacts, ligand interactions, biological assemblies and active-site geometry in ChimeraX or another structural viewer.
- Always map residues back to the input-sequence numbering before discussing active sites, variants or post-translational modifications.

## Limitations

- RCSB sequence search is not a full replacement for manual BLAST/UniProt searches in difficult cases.
- UniProt annotations retrieved through SIFTS may describe a fusion partner, peptide partner or another polymer entity in the same PDB entry. The reports now expose these mappings separately, but biological interpretation still requires checking entity, chain and sequence coverage.
- AlphaFold links are only reported when a UniProt accession is known.
- Secondary-structure and domain annotations depend on what RCSB exposes for the selected chain.
- The scripts do not run ChimeraX and do not compute structural contacts directly from coordinates.
