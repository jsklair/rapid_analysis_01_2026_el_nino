# Data sources

**Analysis snapshot date:** 4 September 2026

## NOAA Climate Prediction Center

### Relative Oceanic Niño Index (RONI)

https://cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/

Primary source for the historical quantitative comparison.

The analysis uses the current ERSSTv6 RONI history from 1950 onwards.

The repository preserves the exact HTML snapshot used for the published analysis:

`data/raw/noaa_roni_history_2026-09-04.html`

NOAA states that recent real-time RONI estimates can be revised for up to two months after their initial publication.

### Official RONI outlook

https://cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/outlook/

Primary source for the forecast percentile distribution.

Snapshot used:

`data/raw/noaa_roni_outlook_2026-09-04.html`

Observed and forecast values remain separate throughout the analysis.

### ENSO Diagnostics Discussion

https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_advisory/ensodisc.html

Used for current NOAA interpretation and forecast context.

The 13 August 2026 discussion reported a 69% probability that OND 2026 reaches at least +2.5°C RONI.

### RONI strength categories

https://cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/strengths/

NOAA's historical warm-episode criterion requires RONI to remain above +0.5°C for at least five consecutive overlapping seasons.

RA01 then applies a peak threshold of +1.5°C to select the major-event comparison cohort. The NOAA strength categories are used to anchor that threshold.

"Major" is an analytical shorthand used in this repository rather than an official NOAA category.

## World Meteorological Organization

### September 2026 El Niño update

https://wmo.int/news/media-centre/el-nino-set-become-very-strong-raising-risks-of-extreme-weather-2027

### August 2026 El Niño/La Niña Update

https://wmo.int/resources/publication-series/el-ninola-nina-updates/august-2026

These sources provide current-event context rather than the historical quantitative series.

## Comparability rules

- Historical quantitative comparisons use NOAA RONI consistently.
- Conventional Niño 3.4 or ONI values are not merged with RONI.
- Forecast values are not presented as observations.
- Regional impacts are not inferred directly from index strength.
- The latest real-time RONI values are treated as revisable estimates.

## Source provenance

`data/raw/source_metadata.json` records the retrieval timestamp, source URLs, local snapshot filenames and SHA-256 checksums.

This allows the exact source version behind the published results to be identified even if the live NOAA pages subsequently change.
