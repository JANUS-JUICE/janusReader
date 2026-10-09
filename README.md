# JanusReader

![Version](https://img.shields.io/badge/version-0.18.0-blue)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.13364878.svg)](https://doi.org/10.5281/zenodo.13364878)

**JanusReader** is the official Python library for reading data from the JANUS instrument on board ESA's JUICE mission. It loads image pixels and metadata from the accompanying PDS4 label.

**DOI:** [10.5281/zenodo.13364878](https://doi.org/10.5281/zenodo.13364878)

## Installation

The current source version is **0.18.0** and requires **Python >=3.14,<4**.

Install the published package:

```shell
python3 -m pip install JanusReader
```

To install the version in this checkout:

```shell
python3 -m pip install -e .
```

The published package may differ from the source version. Check the installed version with:

```shell
python3 -m JanusReader --version
```

The CLI reads its version from installed package metadata. Reinstall the checkout after changing the version in `pyproject.toml` to refresh that metadata.

## Input products

Keep the image file and its matching `.lblx` label in the same directory, with the same basename.

| Input | Behavior |
| --- | --- |
| `.vic` | Reads raw pixels as a NumPy `uint16` array, using the offset and dimensions in the label. |
| `.dat` | Reads calibrated pixels as a NumPy `float32` array. The file must contain exactly the image pixels; this read does not apply the label offset. |
| `.lblx` or `.xml` | Resolves to `.vic` when the filename contains `raw`, or to `.dat` when it contains `cal`. It then loads the matching `.lblx` label, even when the supplied suffix is `.xml`. |

Pixel interpretation follows the label's `processing_level`: `raw` uses the raw reader; other levels use the calibrated reader. Both readers use NumPy's native byte order.

For calibrated products, the filename must follow the JANUS naming convention: the fourth underscore-separated component from the end contains a leading character followed by the hexadecimal skipped-calibration bit mask (for example, `a_b_c_c03_d_e_tail.dat`). Arbitrary calibrated filenames are not supported.

## Python usage

```python
from JanusReader import JanusReader

product = JanusReader("datafile.vic")
image = product.image  # NumPy array with shape (Lines, Samples)

print(product.target, product.level)
print(product.startDT, product.endDT)
product.Show()          # General product information
product.Show(all=True)  # Includes processing and instrument metadata

# Each distance is None when its XML field is unavailable.
spacecraft_solar_distance = product.spacecraftSolarDistance
target_solar_distance = product.targetSolarDistance
```

The constructor accepts a string or `pathlib.Path`, an optional Rich `console`, and the boolean options `debug` and `vicar` (both default to `False`). Set `vicar=True` to parse the embedded raw VICAR header into `product.vicar`; calibrated `.dat` products ignore this option with a warning.

### Common attributes

Attribute names are case-sensitive.

| Attribute | Contents |
| --- | --- |
| `image`, `Lines`, `Samples` | Image array and dimensions. |
| `fileName`, `labelFile` | Resolved image and label paths. |
| `title`, `prodVersion`, `level`, `dataDesc` | Product identification, last modification version, processing level, and optional observation comment. |
| `startDT`, `endDT`, `creationDate` | Python `datetime` values without timezone information. |
| `startSC`, `endSC` | Spacecraft clock counts from the label. |
| `target`, `phaseName`, `phaseID`, `startOrbit` | Target and mission context. |
| `Exposure`, `Filter`, `subFrame`, `instrumentState` | Exposure, filter, subframe, and instrument temperature metadata. |
| `onBoardProcessing`, `onGroundProcessing`, `proceesingContext` | Processing metadata; `proceesingContext` retains its existing API spelling. |
| `spacecraftSolarDistance`, `targetSolarDistance` | Heliocentric distance values as stored in the label, without unit conversion. |
| `skippedCalibrationSteps` | Calibrated-product object with a `.steps` list; `None` for raw products. |

Since 0.18.0, `psa:stop_orbit_number` is no longer read, `endOrbit` is no longer created, and the information display omits End Orbit. Use `startOrbit` for the available orbit metadata.

Missing scalar label values generally produce a warning and return `None`; missing required XML structures can raise `IndexError`. Missing files raise `FileNotFoundError`, and malformed XML raises a parser error. With `vicar=True`, an invalid raw VICAR header raises `JanusReader.exceptions.NOT_VALID_VICAR_FILE`.

## Command line

```shell
janusReader datafile.vic
janusReader --all datafile.vic
janusReader --debug datafile.vic
janusReader --show-skipped-process a_b_c_c03_d_e_tail.dat
janusReader --version
janusReader --help
```

The default output shows general product information. `--all` (`-a`) adds instrument and processing tables; `--show-skipped-process` (`-s`) displays skipped calibration steps instead. `--debug` (`-d`) prints input-type diagnostics, and `--help` (`-h`) lists the options.

The same CLI is available through the active Python interpreter:

```shell
python3 -m JanusReader --help
```

## Development

Install the checkout and test tools in a virtual environment:

```shell
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e . pytest pytest-cov ruff
python -m pytest
```

The repository's pytest configuration writes coverage reports under `coverage/`. Tests use synthetic products to check image loading, label compatibility, metadata helpers, and VICAR header parsing.

See [CHNGELOG.md](CHNGELOG.md) for version history.
