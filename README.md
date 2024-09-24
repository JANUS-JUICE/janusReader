# JanusReader

![Version](https://img.shields.io/badge/version-0.12.2-blue)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.13364878.svg)](https://doi.org/10.5281/zenodo.13364878)

**JanusReader** is the official Python library to read data coming from the JANUS instrument on board the ESA mission JUICE.

**DOI:** [10.5281/zenodo.13364878](https://zenodo.org/doi/10.5281/zenodo.13364878)

## Installation

```shell
$ python3 -m pip install JanusReader
```

## Usage

```python
from JanusReader import JanusReader as JR

dat = JR("datafile.vic")
```

### Command line

```console
janusReader datafile.dat
```

it will show the info about the data file. use *--help* for all the options.
