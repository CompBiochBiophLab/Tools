# Sequence tools

This folder contains several notebook-based workflows to compare and visualize sequences starting from the same FASTA inputs.

Files:

- `ternary_alignment_substitution.ipynb`: ternary similarity map from normalized protein alignment distance using `Biopython PairwiseAligner`, `BLOSUM62`, and affine gaps.
- `kras_msa_publication.ipynb`: publication-quality multiple sequence alignment visualization for ten K-RAS homologs, built in Python with Biopython.
- `sequence_similarity_network.ipynb`: sequence similarity network (SSN) from a protein FASTA file using pairwise normalized alignment similarity and a graph threshold.
- `ternary_hamming.ipynb`: ternary similarity map using normalized Hamming distance.
- `ternary_levenshtein.ipynb`: ternary similarity map using normalized Levenshtein distance.
- `trilateration_hamming.ipynb`: distance-based trilateration using the three references as geometric anchors.
- `mds_levenshtein.ipynb`: classical multidimensional scaling from the full pairwise normalized Levenshtein distance matrix.
- `kmer_pca.ipynb`: PCA of clr-transformed 2-mer compositions.
- `report.tex`: LaTeX report with the mathematics, assumptions, and limitations of all these modalities.
- `example_vertices.fasta`: minimal example with three vertex sequences.
- `example_queries.fasta`: example sequences to project into the triangle.
- `kras_homologs_10.fasta`: ten homologous K-RAS protein sequences from UniProt for MSA visualization.
- `kras_triangle_references.fasta`: three K-RAS protein references for the alignment-based ternary notebook.
- `kras_triangle_queries.fasta`: seven K-RAS protein queries for the alignment-based ternary notebook.

Shared inputs:

- `example_vertices.fasta` contains exactly three references interpreted as `A`, `B`, and `C`.
- `example_queries.fasta` contains the additional sequences to compare with them.

Suggested use:

- Open each notebook in Jupyter and run all cells.
- Each notebook is mathematically self-contained: the key definitions, formulas, assumptions, and interpretation notes are included as Markdown cells with LaTeX.
- Change `REFERENCES_FASTA`, `QUERIES_FASTA`, and `OUTPUT_PREFIX` in the first code cell if you want to use your own FASTA files.
- The alignment-based ternary notebook now assumes protein input and uses the bundled K-RAS FASTA pair by default.
- For the K-RAS MSA notebook, use `kras_homologs_10.fasta` as the input FASTA; the figure is written to the root `figures/` directory.
- The SSN notebook also uses `kras_homologs_10.fasta` by default and writes the network figure to the root `figures/` directory.

Important interpretation:

- The triangle is a relative similarity map with respect to three chosen references.
- It is not an exact metric embedding of the original sequence distances.
- For proteins, the alignment-based ternary notebook is the default reference-based option in this folder.
- The K-RAS MSA notebook is complementary: it is a direct alignment-and-visualization workflow rather than an ordination method.
- The SSN notebook is complementary too: it represents thresholded neighborhoods in sequence space as a graph rather than as a 2D embedding.
- The report explains in detail when alignment-based ternary mapping, SSN analysis, edit-distance ternary mapping, trilateration, MDS, `k`-mer PCA, or MSA visualization are more appropriate.
