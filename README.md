# The CBBL tools repository

The [CBBL tools github repo](https://github.com/CompBiochBiophLab/Tools) is a collection of tools that the [CBBL](https://mon.uvic.cat/cbbl) members have developed to help dealing with usual tasks. The repository is not perfect, nor nicely updated... It represents a starting point to face some typical tasks when dealing with bioinformatics, computational chemistry, molecular simulations, etc...

This is a live repository, always to be improved. Either if you are a member of the [CBBL](https://mon.uvic.cat/cbbl) or not, you contribution is more than welcome.

## How to use the repository

Most folders contain either notebooks, small scripts, or both. The intended workflow is:

1. Enter the folder that matches your topic.
2. Read its local `Readme.md` or `README.md`.
3. Run the notebooks for interactive examples or the scripts for lightweight command-line tasks.

The `sequenceTools` folder combines notebook-based workflows with command-line scripts for focused sequence analyses. The rest of the folders keep their existing scripts and notebooks, and each active tools folder also includes:

- `report_<folder>.tex`: a LaTeX summary of the methods used in that folder.

The reports now use pure LaTeX/TikZ for conceptual schemes. Notebooks in the repo should only exist when they perform the actual computational or teaching work of the folder.


## Installing requirements

Most folders include a local `environment.yml` with the Python packages needed for that workflow. Use the environment closest to the material you want to run. For example:

```bash
conda env create -f sequenceTools/environment.yml
conda activate tools-sequencetools
```

Some subfolders also provide a more specific `environment.yml` for command-line tools or focused workflows:

```bash
conda env create -f sequenceTools/proteinSequenceTools/environment.yml
conda activate tools-protein-sequence-tools
```

For non-conda workflows, some folders may also include a `requirements.txt` file:

```bash
python3 -m pip install -r path/to/requirements.txt
```

Folder-specific setup notes, external software requirements and known limitations are documented in each folder README. Graphical applications or research codes such as ChimeraX or ProteinMPNN may require separate installation steps.

## How to generate the reports

The repository uses a common root [`.latexmkrc`](/Users/jordivilla/GitHub/TEACHING/Tools/.latexmkrc) so that every report is compiled with `latexmk` using `lualatex`.

Prerequisites:

- `jupyter`
- `latexmk`
- a TeX distribution with `lualatex`
- Python packages from `requirements.txt`

To build every report from the root of the repo:

```bash
python build_reports.py
```

This runs `latexmk` in each top-level tools folder with the shared root `.latexmkrc`, using `lualatex`.

To build a single report manually, go to the target folder and run:

```bash
latexmk -r ../.latexmkrc -lualatex report_<folder>.tex
```

For example, in `sequenceTools` the report file is `report_sequenceTools.tex`.

## Instructions to build the HTML site

The repo contains an HTML site that can be accessed through [this link](https://compbiochbiophlab.gihub.io/Tools/intro.html). To build the site when updating the material of the repo, you should install [jupyter book](https://jupyterbook.org/en/stable/intro.html) and [ghp-import](https://pypi.org/project/ghp-import/), to make the handling of the `gh-pages` branch easier. In short, once installed and assuming that your local repo copy is `<local_github>/Tools` do the following:

```
cd <local_github>
jb build Tools; cd Tools; git add .; git commit -m "update"; git push; ghp-import -n -p -f _build/html
```
