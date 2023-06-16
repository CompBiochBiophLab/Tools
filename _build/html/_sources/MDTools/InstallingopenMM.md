# Some tips to install openMM for production

(work in progress)

## Preparing the conda environment

It is handy to leave openMM in a conda environment created to run simulations.
So, first of all be sure you have [installed anaconda](https://docs.anaconda.com/anaconda/install/index.html).

Next, create a environment with a name you can identify as being for openMM simulations. For example:
```
conda create -n openMM python
```

This will create a new environment called `openMM`. You need to activate it by running:
```
conda activate openMM
```
Check the [conda documentation](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) for more details on managing environments.

## Installing openMM

You are now ready to install openMM
``` 
conda install -c conda-forge openmm
```
