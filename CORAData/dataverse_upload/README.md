# Dataverse Upload Notebook

This folder contains a local Jupyter notebook for uploading files to a Dataverse dataset using file-level metadata stored in an Excel spreadsheet.

## Contents

- `upload_files_script.ipynb`: notebook that reads the Excel metadata file, checks that each referenced file exists, and uploads the files to Dataverse.
- `wtAcetLys.xlsx`: example metadata spreadsheet with one row per file to upload.

## What It Is For

The notebook is intended for dataset deposition workflows where many files must be uploaded with consistent metadata. It was adapted from a Google Colab-oriented workflow so it can run locally from a computer with Jupyter installed.

For each file, the notebook:

- reads the file name, description, local path, and Dataverse tags from the spreadsheet;
- verifies that the file exists before starting uploads;
- prints when each upload starts and finishes;
- uploads the file to the configured Dataverse dataset;
- optionally reports the total dataset size after upload.

## Spreadsheet Format

The Excel file must contain at least these first four columns:

1. `Nom del fitxer`: file name.
2. `Descripcio`: file description.
3. `Ruta del fitxer`: local folder containing the file. Relative paths are resolved from the directory where the notebook is executed.
4. `Etiqueta`: comma-separated Dataverse file categories.

Top-level bundle archives should not be listed if the intent is to upload the individual files contained in their corresponding folders.

## Configuration

Edit the configuration cell in `upload_files_script.ipynb` before running it:

```python
identifier = "DATASET_IDENTIFIER"
excel_file_name = "wtAcetLys.xlsx"
base_url = "https://dataverse.example.org/"
```

Do not commit a real Dataverse API token. Set it as an environment variable before launching Jupyter:

```bash
export DATAVERSE_API_TOKEN="your-token-here"
jupyter lab
```

The notebook reads the token with:

```python
token = os.environ.get("DATAVERSE_API_TOKEN", "YOUR_DATAVERSE_API_TOKEN")
```

## Requirements

The notebook installs missing Python packages automatically when needed:

- `pandas`
- `openpyxl`
- `pyDataverse`

## Usage

1. Place the notebook, the Excel file, and the files to upload in a consistent local folder structure.
2. Check that the paths in `Ruta del fitxer` point to folders containing the listed files.
3. Set `DATAVERSE_API_TOKEN` in the shell used to launch Jupyter.
4. Open `upload_files_script.ipynb`.
5. Run the upload cell.
6. Review the printed status messages for each file.

