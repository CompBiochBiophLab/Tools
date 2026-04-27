# TCR structure tools

Notebooks to inspect T cell receptor (TCR) structures from a selected clonotype.

The notebooks use conventional packages directly (`pandas`, `requests`, `biopython`, `nglview` and PyMOL) and do not depend on a custom local Python module.

The intended workflow is:

1. Optionally search the best available PDB structure for a protein from a gene name.
2. Read the TCR unit names, chain type, sequence, abundance and HMMER logo associated with a clonotype.
3. Select the most abundant alpha and beta TCR sequences.
4. Search RCSB PDB for the best matching structures for each selected TCR chain.
5. Download the selected structures and visualize them with `nglview`.
6. Display the clonotype/CDR3 residues in van der Waals representation and the rest of the protein as ribbons.
7. Prepare optional PyMOL scripts for publication-quality figures.

The main example input file is `data/tcr_units_example.csv`. Replace it with the project-specific clonotype table when available. The older `data/clonotypes_example.csv` file is kept only as a minimal compatibility example.

## Environment

Create the conda environment before running the notebooks:

```bash
conda env create -f TCRTools/environment.yml
conda activate tcrtools
python -m ipykernel install --user --name tcrtools --display-name "Python (tcrtools)"
```

The environment includes `pandas`, `requests`, `biopython`, `nglview`, `hmmer` and `pymol-open-source`.

## PyMOL

Run PyMOL from the `tcrtools` conda environment:

```bash
conda activate tcrtools
which -a pymol
"$CONDA_PREFIX/bin/pymol" tcr_complex.pml
```

If `which pymol` points to a local installation outside conda, for example `/home/jordivilla/Software/pymol`, that binary may fail with errors such as `Qt not available` or `NotImplementedError: compile with --glut`. In that case, use the conda binary explicitly with `"$CONDA_PREFIX/bin/pymol"` or remove the external PyMOL path from `PATH`.

If `which pymol` points to conda but the traceback still imports `/home/jordivilla/Software/pymol`, then Python is probably seeing an external PyMOL through `PYTHONPATH`, `PYTHONHOME` or `PYMOL_*` variables. Check it with:

```bash
python -c "import pymol; print(pymol.__file__)"
env | grep -E 'PYTHON|PYMOL'
```

The imported `pymol` module should live inside `$CONDA_PREFIX`. If it does not, run PyMOL with the clean wrapper:

```bash
./run_pymol_clean.sh tcr_complex.pml
```

or manually:

```bash
unset PYTHONPATH PYTHONHOME PYMOL_PATH PYMOL_DATA
PYTHONNOUSERSITE=1 "$CONDA_PREFIX/bin/pymol" tcr_complex.pml
```

When the environment is no longer needed, remove it with:

```bash
conda deactivate
conda env remove -n tcrtools
```
