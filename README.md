# JanusReader

![Version](https://img.shields.io/badge/version-0.18.1-blue)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.13364878.svg)](https://doi.org/10.5281/zenodo.13364878)

**JanusReader** is the official Python library for reading data from the JANUS instrument on board ESA's JUICE mission. It loads image pixels and metadata from the accompanying PDS4 label.

**DOI:** [10.5281/zenodo.13364878](https://doi.org/10.5281/zenodo.13364878)

## Installation

The current source version is **0.18.1** and requires **Python >=3.14,<4**.

Install the published package:

```shell
python3 -m pip install JanusReader
```

To install the version in this checkout, first install [uv](https://docs.astral.sh/uv/getting-started/installation/):

```shell
uv sync --locked --no-default-groups
```

The published package may differ from the source version. Check the installed version with:

```shell
python3 -m JanusReader --version
```

For the uv-managed checkout, use `uv run --locked --no-default-groups python -m JanusReader --version` to query the project environment.

The CLI reads its version from installed package metadata. Run `uv sync` after changing the version in `pyproject.toml` to refresh the lockfile and installed metadata.

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
| `target`, `phaseName`, `phaseID` | Target and mission context. |
| `Exposure`, `Filter`, `subFrame`, `instrumentState` | Exposure, filter, subframe, and instrument temperature metadata. |
| `onBoardProcessing`, `onGroundProcessing`, `proceesingContext` | Processing metadata; `proceesingContext` retains its existing API spelling. |
| `spacecraftSolarDistance`, `targetSolarDistance` | Heliocentric distance values as stored in the label, without unit conversion. |
| `skippedCalibrationSteps` | Calibrated-product object with a `.steps` list; `None` for raw products. |

Since 0.18.0, `psa:stop_orbit_number` is no longer read, `endOrbit` is no longer created, and the information display omits End Orbit. Since 0.18.1, `psa:start_orbit_number`, `startOrbit`, and the Start Orbit display row are also removed.

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

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run:

```shell
uv sync --locked
uv run --locked pytest
uv run --locked python -m JanusReader --help
uv run --locked janusReader --version
uv lock --check
uv pip check
uv build
```

`.python-version` selects Python 3.14. `uv sync` creates `.venv` and installs the project in editable mode. The `devel` and `test` dependency groups are installed by default. For a runtime-only environment, use `uv sync --locked --no-default-groups`; add `--extra docs` to install Sphinx.

`uv.lock` is the authoritative dependency lockfile. Commit it alongside `pyproject.toml` when dependencies change. `--locked` prevents commands from silently updating it. The build uses `uv_build` with the case-sensitive `JanusReader` module under `src/`; pip installation remains supported. The release workflow installs locked dependencies, runs tests, and builds distributions with uv before publishing.

The repository's pytest configuration writes coverage reports under `coverage/`. Tests use synthetic products to check image loading, label compatibility, metadata helpers, and VICAR header parsing.

## Publishing

### Local publication with uv

Before each release, set the version with `uv version <version>` (or `uv version --bump patch`), and update the README version badge, changelog, and citation metadata to match. Commit the updated `pyproject.toml` and `uv.lock` together.

For version 0.18.1:

```shell
uv sync --locked
uv run --locked pytest
uv lock --check
uv pip check
uv build --no-sources
```

Set `UV_PUBLISH_TOKEN` to a PyPI API token through your shell or secret manager, then upload only the artifacts for the intended version:

```shell
uv publish dist/janusreader-0.18.1.tar.gz dist/janusreader-0.18.1-py3-none-any.whl
```

Avoid a bare `uv publish` when `dist/` contains artifacts from older releases: it defaults to uploading all files in that directory. PyPI does not allow replacing an existing distribution filename with different contents; publish changed code under a new version.

### GitHub release publication

The workflow [Upload Python Package](.github/workflows/python-publish.yml) starts on a GitHub release's `published` event.

1. Commit and push the release changes, including the workflow and `uv.lock`.
2. In the repository's **Settings → Secrets and variables → Actions**, create the repository secret `PYPI_API_TOKEN` with a PyPI token authorized to publish JanusReader, or verify that it is already configured.
3. In **Actions → Upload Python Package**, enable the workflow if it is disabled.
4. In **Releases → Draft a new release**, choose a tag matching the package version (for example, `v0.18.1`) and target the commit containing the release changes. Add release notes and select **Publish release**.
5. Follow the job in **Actions**. It installs Python 3.14 and locked dependencies, runs tests, builds the sdist and wheel with uv, and uploads them using `pypa/gh-action-pypi-publish` and the configured token.

A push, a tag alone, or a saved release draft does not trigger this workflow. It has no `workflow_dispatch` trigger, so there is no manual **Run workflow** button. GitHub Pages and environment configuration are not required for this PyPI publication.

See the [uv publishing guide](https://docs.astral.sh/uv/guides/package/) and [GitHub release guide](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository) for details.

See [CHNGELOG.md](CHNGELOG.md) for version history.
