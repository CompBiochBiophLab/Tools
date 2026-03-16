# Sequence tools

This folder contains several notebook-based workflows to compare and visualize sequences starting from the same FASTA inputs.

Files:

- `ternary_alignment_substitution.ipynb`: ternary similarity map from normalized protein alignment distance using `Biopython PairwiseAligner`, `BLOSUM62`, and affine gaps.
- `kras_msa_publication.ipynb`: publication-quality multiple sequence alignment visualization for ten K-RAS homologs, built in Python with Biopython.
- `sequence_similarity_network.ipynb`: sequence similarity network (SSN) from a protein FASTA file using pairwise normalized alignment similarity and a graph threshold. It also produces a ranked pairwise distance table and a distance-matrix heatmap to guide the choice of the SSN cutoff.
- `proteinmpnn_homologous_pdbs.ipynb`: structure-conditioned sequence design workflow that searches homologous protein structures in the PDB and runs `ProteinMPNN` on representative backbones.
- `setup_proteinmpnn_bioinformatics.sh`: optional helper that installs the official ProteinMPNN code and configures `PROTEINMPNN_HOME`.
- `ternary_hamming.ipynb`: ternary similarity map using normalized Hamming distance.
- `ternary_levenshtein.ipynb`: ternary similarity map using normalized Levenshtein distance.
- `trilateration_hamming.ipynb`: distance-based trilateration using the three references as geometric anchors.
- `mds_levenshtein.ipynb`: classical multidimensional scaling from the full pairwise normalized Levenshtein distance matrix.
- `kmer_pca.ipynb`: PCA of clr-transformed 2-mer compositions.
- `report.tex`: LaTeX report with the mathematics, assumptions, and limitations of all these modalities.
- `inputs/example_vertices.fa`: minimal example with three vertex sequences.
- `inputs/example_queries.fa`: example sequences to project into the triangle.
- `inputs/kras_homologs_10.fa`: ten homologous K-RAS protein sequences from UniProt for MSA visualization.
- `inputs/kras_triangle_references.fa`: three K-RAS protein references for the alignment-based ternary notebook.
- `inputs/kras_triangle_queries.fa`: seven K-RAS protein queries for the alignment-based ternary notebook.

Shared inputs:

- `inputs/example_vertices.fa` contains exactly three references interpreted as `A`, `B`, and `C`.
- `inputs/example_queries.fa` contains the additional sequences to compare with them.

Suggested use:

- Open each notebook in Jupyter and run all cells.
- Each notebook is mathematically self-contained: the key definitions, formulas, assumptions, and interpretation notes are included as Markdown cells with LaTeX.
- Change `REFERENCES_FASTA`, `QUERIES_FASTA`, and `OUTPUT_PREFIX` in the first code cell if you want to use your own FASTA files.
- The alignment-based ternary notebook now assumes protein input and uses the bundled K-RAS FASTA pair by default.
- For the K-RAS MSA notebook, use `inputs/kras_homologs_10.fa` as the input FASTA; the figure is written to the `results/figures/`.
- The SSN notebook also uses `inputs/kras_homologs_10.fa` by default and writes the network figure to the `results/figures/`.
- The `ProteinMPNN` notebook uses `inputs/kras_homologs_10.fa` as a seed sequence source, queries homologous PDB structures, and writes designs and summary figures under `sequenceTools/results/proteinmpnn/` and the `results/figures/`. If `PROTEINMPNN_HOME` is not defined, the notebook can clone the official repository locally into `sequenceTools/ProteinMPNN`, which is ignored by Git. If you prefer an explicit environment setup, run `bash sequenceTools/setup_proteinmpnn_bioinformatics.sh` and reactivate the `bioinformatics` conda environment first.

Important interpretation:

- The triangle is a relative similarity map with respect to three chosen references.
- It is not an exact metric embedding of the original sequence distances.
- For proteins, the alignment-based ternary notebook is the default reference-based option in this folder.
- The K-RAS MSA notebook is complementary: it is a direct alignment-and-visualization workflow rather than an ordination method.
- The SSN notebook is complementary too: it represents thresholded neighborhoods in sequence space as a graph rather than as a 2D embedding.
- The `ProteinMPNN` notebook is different again: it is a backbone-conditioned generative design workflow rather than a comparison-only method.
- The report explains in detail when alignment-based ternary mapping, SSN analysis, structure-conditioned design, edit-distance ternary mapping, trilateration, MDS, `k`-mer PCA, or MSA visualization are more appropriate.
