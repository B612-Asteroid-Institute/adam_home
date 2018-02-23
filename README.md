# Asteroid Decision and Analysis Machine

[![Build Status](https://www.travis-ci.org/B612-Asteroid-Institute/adam.svg?branch=master)](https://www.travis-ci.org/B612-Asteroid-Institute/adam)
[![Coverage Status](https://coveralls.io/repos/github/B612-Asteroid-Institute/adam/badge.svg?branch=master)](https://coveralls.io/github/B612-Asteroid-Institute/adam?branch=master)

## Installing Dependencies

Clone this repository using git (using SSH in this example):

```git clone git@github.com:B612-Asteroid-Institute/adam.git```

Then `cd` into the cloned repository and do one of the following depending on how you prefer your packages to be installed.

To install pre-requisite software using anaconda: 

```conda install -c defaults -c conda-forge --file requirements.txt```

To install pre-requisite software using pip:

```pip install -r requirements.txt```

Note that to use the `adam.stk` submodule you will need to have STK installed on your system. 

## Installation for Developers

To to add `adam` to your Python path: 

```export PYTHONPATH=/path/to/adam/:$PYTHONPATH```

## Installation for Users

To be added soon.

## Testing Installation

Using pytest (with coverage):

```pytest adam --cov=adam```