#  ADAM Python SDK and Jupyter notebooks

[![Python package](https://github.com/B612-Asteroid-Institute/adam_home/workflows/Python%20package/badge.svg)](https://github.com/B612-Asteroid-Institute/adam_home/actions?query=workflow%3A%22Python+package%22)
[![Coverage Status](https://codecov.io/gh/B612-Asteroid-Institute/adam_home/branch/master/graph/badge.svg?token=3oTxQRvdID)](https://codecov.io/gh/B612-Asteroid-Institute/adam_home)

# What is ADAM?

ADAM is a cloud-based software platform that performs astrodynamics algorithms (e.g. orbit propagation). You can find whitepapers, presentations, etc. [here](https://adam.b612foundation.org).

This repo contains the Python SDK (software development kit) and demo Jupyter notebooks for interacting with ADAM (Asteroid Decision, Analysis, and Mapping) API programmatically.

## Onboarding

The ADAM API is currently in private beta. If you'd like to write Python workflows that use ADAM, reach out to carise@ to request a project ID.

## Mac/Linux/WSL Configuration

The following configuration steps have been tested on Mac OS (Catalina and Big Sur), Linux (Debian-like), and WSL (Debian, Ubuntu). There's also been some limited testing on the Windows Anaconda Powershell command prompt.

1. Install [anaconda](https://www.anaconda.com/). The individual edition is sufficient if you don't already have anaconda.

2. Install `adamctl`. This command line utility helps you configure your ADAM Python client. (More on that below.)

```bash
# get latest release of ADAM sdk
# add the -c conda-forge for some of the adam dependencies
conda install -c conda-forge -c asteroid-institute adam
```

3. Login to ADAM. This authenticates you with the ADAM server so that you can access the ADAM APIs. You will need a Google account. (e.g. gmail or a Google Workspace email).

```bash
adamctl login dev https://adam-dev-193118.appspot.com/_ah/api/adam/v1
```

4. Set your ADAM project ID. The project is like a folder for jobs you run on ADAM.

```bash
adamctl config envs.dev.workspace "YOUR_WORKSPACE_ID"
```

5. To view your ADAM server configurations:

```bash
adamctl config
```

## Demos

Once you have the package installed, you should be able to run the demonstration
notebooks found in the [demos/](demos/) directory. The [single_run_demo](demos/single_run_demo.ipynb)
is a good place to start.

Before invoking code from the ADAM SDK, you'll want to include the following code at the top of your notebook (after the imports):

```python
# The default configuration is prod
cm = ConfigManager()

# If you need to use a different server than the default e.g. dev:
# cm.set_default_env('dev')
# You can also set your default environment using the adamctl command-line tool, e.g.
# adamctl config default_env dev

# Configure the REST API server endpoint and user token
auth_rest = AuthenticatingRestProxy(RestRequests())

# If you need to use properties in the config, e.g. your workspace ID:
config = cm.get_config()
print(config[workspace])
```

See the [single_run_demo](demos/single_run_demo.ipynb) notebook for an example.

## SDK documentation

https://b612-asteroid-institute.github.io/adam_home/index.html

## Developing ADAM SDK

The ADAM SDK is a pure-python package that follows the [standard
setuptools directory](https://python-packaging.readthedocs.io/en/latest/minimal.html) layout and installation mechanisms.
The source code is in the [adam/](adam/) subdirectory, the tests are in
[tests/](tests/). A number of demo notebooks are provided in [demos/](demos/). Conda
package recipe files are in [recipe/](recipe/). [`setup.py`](setup.py) in the root of the
repository handles the install, as well as the creation of the [`setupctl`
script via an
entrypoint](https://setuptools.readthedocs.io/en/latest/setuptools.html#automatic-script-creation).

A typical development loop will consist of:

  * Create a separate Anaconda environment.
  * Running `python setup.py develop`, to add the source code onto your
    `$PYTHONPATH`. This is needed only once.
  * Making some changes to the package in `adam/`
  * Testing with `pytest ./tests --cov=adam --ignore=tests/integration_tests`
  * Commit, push, PR.

### Installing ADAM SDK from source

Installing `adamctl` from source, instead of Anaconda. Do this if you're developing the ADAM SDK.

```bash
# grab the source code
git clone git@github.com:B612-Asteroid-Institute/adam_home
cd adam_home

# create a new conda environment with the necessary dev tools
conda create -n adam-dev --file conda-requirements.txt
conda activate adam-dev

# install ADAM in dev mode
python setup.py develop
```

### Developer configurations

Sometimes you might need to use an ADAM development server (e.g. for experimental APIs or developing ADAM client/server). 
Create a separate ADAM configuration for that workspace.

```bash
# Set up a configuration e.g. "experimental_dev"
# The URL points to the ADAM server you specify, plus the path to the API.
# This will also set the default_env property of your configuration to "experimental_dev".
adamctl login experimental_dev https://example-adam-server.com/_ah/api/adam/v1

# Set your workspace ID. Whoever owns the development server should be
# able to create a workspace ID for you.
adamctl config envs.experimental_dev.workspace "YOUR_WORKSPACE_ID"
```

## Updating documentation

### Initial setup

You probably don't have to do the initial setup.

```bash
# In the same conda environment where you've installed ADAM:
cd adam_home
conda install sphinx sphinx_rtd_theme

# Bootstrap sphinx
sphinx-quickstart

#  Edit Makefile and change name of the source directory to doc_source.

#  Edit conf.py
 
# Auto-generate the API docs
sphinx-apidoc -o doc_source adam

# Edit index.rst to include the modules document.

# Remove doc_source/adam.tests*.rst and any references to the adam.tests package.
# This step will go away when tests get moved out of the adam package.

# Build the html documentation
make html
```

### Re-generate documentation

```bash
cd adam_home
sphinx-apidoc --force -o doc_source adam
make html
rm -rf docs
mv build/html docs
```

Eventually this should be part of CI/CD.
