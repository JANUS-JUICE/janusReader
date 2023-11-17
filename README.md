# JanusReader

![Version](https://img.shields.io/badge/version-0.9.2-blue)
![DOI:10.5281/zenodo.10051173](https://zenodo.org/badge/DOI/10.5281/zenodo.10051173.svg)

**JanusReader** is the offical Python library to read data coming from JANUS instrument on-board the ESA mission JUICE.

**DOI:** [10.5281/zenodo.10051173](https://zenodo.org/doi/10.5281/zenodo.10051172)

## Installation

```shell
$ python3 -m pip install JanusReader
```

## Usage

```python
from JanusReader import JanusReader as JR

dat = JR("datafile.vic")
```
