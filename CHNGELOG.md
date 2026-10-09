# JanusReader

## 0.18.0 09-10-2026

- Stop reading `psa:stop_orbit_number` from the product label.
- Remove the `JanusReader.endOrbit` attribute and the End Orbit row from the information display. `startOrbit` remains available.

## 0.17.0 14-09-2026

- Restore XML value conversion and namespace-aware PDS tag lookup.
- Preserve version identifiers as strings and select the last modification entry for the product version.
- Support both mission-phase label layouts and creation timestamps with or without a trailing `Z`.
- Allow observation labels without a comment.
- Fix Rich markup rendering in CLI headers and footers.

## 0.16.3 06-07-2026

- replaced `solarDistance` with `spacecraftSolarDistance`
- introduced `targetSolarDistance`
- set both attributes to `None` when the XML `Distances` element is missing

## 0.16.2 01-07-2026

- set solarDistance to None when the XML field is missing

## 0.16.1 30-06-2026

- fix typo

## 0.16.0 30-06-2026

- introduced the attribute solarDistance

## 0.15.0 25-06-2026

- removed from the tags the pds dictionary name
- introduced the cli module
- fixed the type of integer values read from the xml file

## 0.14.0 22-02-2026

- fix the bug from [issue #5](https://github.com/JANUS-JUICE/janusReader/issues/5)
- ported the project to poetry
- added to the project the optional dipendences *test*
- written test to obtain a coverage of 91%
- introduced the optional dependences *devel*

## 0.13.0 09-06-2025

- changed the label suffix from xml to lblx

## 0.12.2 23-08-2024

- fix some bugs in the definition of the skipped calibration process
- add --show-skipped-process option in the command line front-end

## 0.12.1 21-08-2024

- fix bug for compatibility with python 3.10

## 0.12.0 21-08-2024

- load calibrated file
- implement OnGround Processing
- implement Processing Context
- implement Skipped Calibrated Steps
- add command line option for info

## 0.11.1 14-08-2024

- fix some bugs

## 0.11.0

- convert from string to datetime some fields...

## 0.10.1

- fix bug in product version field

## Version 0.10.0

- implement datamodel version 1.19

## Version 0.9.2

- fix bug in Show method

## Version 0.9.1

- fix some bug in the requirements
 
## Version 0.9.0

- fix exposure keyword

## Version 0.8.0

- read modified datamodels with warnings
- add uato identification of types

## Version 0.7.0

- add product version number 
- add InstrumentState class (HK)

## Version 0.6.1

- disabled debug options

## Version 0.6.0

- fix the binary read of raw file (oversize issue)
- introduced SubFrame Class

## Version 0.5.0

- Changed some keyword to adatp to the datamodel version 1.14

## Version 0.4.1

- fixed filter number type (str->int)

## Version 0.4.0

- add exposure field

## Version 0.3.0

- Add onboard processing object
