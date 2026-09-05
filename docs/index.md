---
title: Rapid Analysis 01
---

# The Developing 2026 El Niño in Historical Context

**Rapid analysis published 4 September 2026**

NOAA, the US National Oceanic and Atmospheric Administration, estimates that the 2026 El Niño is developing unusually quickly. This analysis uses NOAA's Relative Oceanic Niño Index (RONI) to compare it with previous major events at the same seasonal stage, while keeping observed conditions separate from the forecast.

## Reading the analysis

- **El Niño** is the warm phase of the **El Niño–Southern Oscillation (ENSO)**, a recurring ocean–atmosphere pattern in the tropical Pacific.
- **Niño 3.4** is an area of the central equatorial Pacific commonly used to monitor ENSO.
- **RONI** is NOAA's **Relative Oceanic Niño Index**: a three-month running measure of relative sea-surface-temperature anomalies in the Niño 3.4 region.
- **Season codes** represent overlapping three-month periods, with each letter standing for a month. For example, **MAM** is March–April–May, **JJA** is June–July–August and **OND** is October–November–December.

## How exceptional is 2026 so far?

For June–August (**JJA**) 2026, RONI reached **+1.4°C**.

Among nine previous El Niño episodes that eventually reached strong or very strong RONI intensity, only **1997–98** was higher at the same calendar stage.

![JJA historical comparison](assets/02_jja_same_stage_comparison.png)

## An unusually fast rise

RONI rose from **0.0°C in March–May (MAM) to +1.4°C in June–August (JJA)**.

That is the largest MAM-to-JJA rise in this historical comparison set. The previous maximum was +1.0°C during 1997–98.

![Historical trajectories](assets/01_historical_trajectories.png)

The distinction matters: 2026's **rate of development** has been exceptional, but its observed strength has not yet exceeded the historical record.

## What happens next is still uncertain

The pre-2026 historical RONI maximum is **+2.4°C**.

NOAA's August 2026 median forecast rises above that level during the northern-hemisphere autumn, reaching +2.66°C in October–December (OND). The forecast distribution remains broad, however, and these values are not observations.

![Observed versus forecast](assets/03_observed_vs_noaa_forecast.png)

NOAA's 13 August Diagnostics Discussion estimated a **69% chance of October–December (OND) reaching at least +2.5°C RONI**.

That makes a record-strength event a credible possibility, not an observed result.

## What the analysis can and cannot say

The evidence supports three conclusions:

- 2026 is already near the top of the historical distribution at the same seasonal stage.
- Its March–May to June–August development was faster than any previous major event in this comparison.
- NOAA currently sees a substantial possibility of the event moving beyond the historical RONI range later in 2026.

It does **not** follow that a particular country will experience a specific extreme-weather outcome. ENSO strength and regional impacts are related, but they are not interchangeable.

The latest RONI observations are also real-time estimates and may be revised.

## Method

Historical comparisons use RONI calculated from NOAA's **Extended Reconstructed Sea Surface Temperature version 6 (ERSSTv6)** dataset.

NOAA's historical warm-episode criterion requires RONI to remain above **+0.5°C for at least five consecutive overlapping seasons**. RA01 then retains episodes reaching a peak of at least **+1.5°C**.

RONI adjusts the Niño 3.4 sea-surface-temperature anomaly for the average tropical sea-surface-temperature anomaly.

"Major" is shorthand used for this analysis rather than an official NOAA category.

Historical events were selected using this reproducible rule rather than by choosing famous El Niño years retrospectively, and their development years are aligned by overlapping three-month season.

Historical comparisons use RONI consistently. The related **Oceanic Niño Index (ONI)** and conventional Niño 3.4 anomalies quoted by other sources are not merged into the series.

## Technical details

The project is reproducible in Python using pandas and Matplotlib. Dated NOAA source snapshots and checksums are retained with the analysis.

[View the full repository](https://github.com/jsklair/rapid_analysis_01_2026_el_nino)

[Read the detailed README](https://github.com/jsklair/rapid_analysis_01_2026_el_nino#readme)
