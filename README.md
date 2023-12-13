# The CBBL tools repository

The [CBBL tools github repo](https://github.com/CompBiochBiophLab/Tools) is a collection of tools that the [CBBL](https://mon.uvic.cat/cbbl) members have developed to help dealing with usual tasks. The repository is not perfect, nor nicely updated... It represents a starting point to face some typical tasks when dealing with bioinformatics, computational chemistry, molecular simulations, etc...

This is a live repository, always to be improved. Either if you are a member of the [CBBL](https://mon.uvic.cat/cbbl) or not, you contribution is more than welcome.

## Instructions to build the HTML site

The repo contains an HTML site that can be accessed through [this link](https://compbiochbiophlab.gihub.io/Tools/intro.html). To build the site when updating the material of the repo, you should install [jupyter book](https://jupyterbook.org/en/stable/intro.html) and [ghp-import](https://pypi.org/project/ghp-import/), to make the handling of the `gh-pages` branch easier. In short, once installed and assuming that your local repo copy is `<local_github>/Tools` do the following:

```
cd <local_github>
jb build Tools; cd Tools; git add .; git commit -m "update"; git push; ghp-import -n -p -f _build/html
```
