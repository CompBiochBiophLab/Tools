# Scripts for mathematical plots

Plots of math content are run with either python or matlab.

## Environment

Use the folder environment file before running the Python notebooks:

```bash
conda env create -f mathTools/environment.yml
conda activate tools-mathtools
```

When the environment is no longer needed, remove it with:

```bash
conda deactivate
conda env remove -n tools-mathtools
```

The MATLAB files require a local MATLAB installation.

* MATLAB:
  * Beziers polinomials ([.m](polinomisBeziers.m), [.mlx](polinomisBeziers.mlx))
  * Defining a 2D plane with its quadtants ([.m](Pla2D.m))
* smcpython:
  * Plotting functions ([.ipynb](Functions_plots.ipynb))
  * Plotting vectors ([.ipynb](PlotVectors.ipynb))
