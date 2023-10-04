# JanusReader

![Version](https://img.shields.io/badge/version-0.9.0-blue)

**JanusReader** is the offical Python library to read data coming from JANUS instrument on-board the ESA mission JUICE.

## Installation

```shell
$ python3 -m pip install JanusReader
```

## Usage

```python
from JanusReader import JanusReader as JR

dat = JR("datafile.vic")
```
