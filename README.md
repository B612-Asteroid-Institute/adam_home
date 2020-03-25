#  ADAM: The Asteroid Detection, Analysis, and Mapping platform

![Python package](https://github.com/B612-Asteroid-Institute/adam_home/workflows/Python%20package/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/B612-Asteroid-Institute/adam/badge.svg?branch=master)](https://coveralls.io/github/B612-Asteroid-Institute/adam?branch=master)

## Quick Start (User)

Use the `adamctl` tool to configure your ADAM workspace before you run the notebooks that call the ADAM API. The configuration usually only needs to be done once per environment.

There are 2 required configuration IDs you'll need:

  * Your login token, which you can get using the commands below
  * A workspace id, for which you'll need to submit a request to either Carise or John

```bash
# grab the latest release of adam client
conda install -c asteroid-institute adam

# log in, defaults to prod
adamctl login

# set up your workspace
adamctl config envs.prod.workspace "uuid-received-from-@AstrogatorJohn"
```

To view your configured environments:

```bash
adamctl config
```


## Quick Start (Developer)

```bash
# grab the source code
git clone git@github.com:B612-Asteroid-Institute/adam_home
cd adam_home

# create a new conda environment with the necessary dev tools
conda create -n adam-dev --file conda-requirements.txt
conda activate adam-dev

# install ADAM in dev mode
python setup.py develop

# log in
adamctl login
# log into the 'dev' environment as well
adamctl login dev https://adam-dev-193118.appspot.com/_ah/api/adam/v1

# set up your workspaces
adamctl config envs.prod.workspace "uuid-received-from-@AstrogatorJohn"
adamctl config envs.dev.workspace "uuid-received-from-@AstrogatorJohn"
```

## Demos

Once you have the package installed, you should be able to run the demonstration
notebooks found in the [demos/](demos/) directory.

## Developing ADAM

The ADAM client is a pure-python package that follows the [standard
setuptools directory](https://python-packaging.readthedocs.io/en/latest/minimal.html) layout and installation mechanisms.
The source code is in the [adam/](adam/) subdirectory, the tests are in
[adam/tests/](adam/tests/). A number of demo notebooks are provided in [demos/](demos/). Conda
package recipe files are in [recipe/](recipe/). [`setup.py`](setup.py) in the root of the
repository handles the install, as well as the creation of the [`setupctl`
script via an
entrypoint](https://setuptools.readthedocs.io/en/latest/setuptools.html#automatic-script-creation).

A typical development loop will consist of:

  * Running `python setup.py develop`, to add the source code onto your
    `$PYTHONPATH`. This is needed only once.
  * Making some changes to the package in `adam/`
  * Testing with `pytest adam --cov=adam --ignore=adam/tests/integration_tests`
  * Commit, push, PR.

