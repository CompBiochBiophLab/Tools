#!/usr/bin/env python3
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
FOLDERS = [
    'MDTools','MLtools','PDBTools','RNATools','chemoinformaticsTools','genomeTools',
    'mathTools','miscellanea','productivityTools','pythonPrimer','sequenceTols','statsTools','teachingTools'
]


def run(command, cwd):
    print(f"[run] {' '.join(command)} (cwd={cwd})")
    subprocess.run(command, cwd=cwd, check=True)


for folder in FOLDERS:
    folder_path = ROOT / folder
    report_tex = folder_path / 'report.tex'
    if report_tex.exists():
        run(['latexmk', '-r', '../.latexmkrc', '-lualatex', report_tex.name], folder_path)

print('All reports generated successfully.')
