from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

import pandas as pd
import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"

HISTORY_URL = "https://cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/"
FORECAST_URL = "https://cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/outlook/"

SEASONS = [
    "DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ",
    "JJA", "JAS", "ASO", "SON", "OND", "NDJ",
]

FORECAST_PERCENTILES = {
    "5%": "p05",
    "15%": "p15",
    "25%": "p25",
    "50%": "p50",
    "75%": "p75",
    "85%": "p85",
    "95%": "p95",
}


def fetch_html(url: str) -> str:
    """Download an authoritative NOAA page and return its HTML."""
    response = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "RA01-El-Nino-Analysis/1.0"},
    )
    response.raise_for_status()
    return response.text


def normalise_column_name(column: object) -> str:
    """Reduce NOAA's descriptive HTML headers to stable analytical names."""
    if isinstance(column, tuple):
        text = " ".join(
            str(part)
            for part in column
            if str(part).lower() != "nan" and not str(part).startswith("Unnamed")
        )
    else:
        text = str(column)

    text = re.sub(r"\s+", " ", text).strip()

    if text.lower().startswith("year"):
        return "Year"

    for season in SEASONS:
        if text.upper().startswith(season):
            return season

    for percentile in FORECAST_PERCENTILES:
        if text.startswith(percentile):
            return percentile

    if text.lower().startswith("season"):
        return "Season"

    return text


def parse_history(html: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Extract NOAA's year-by-season RONI history and reshape it to tidy form."""
    tables = pd.read_html(StringIO(html))

    history_table = None

    for candidate in tables:
        candidate = candidate.copy()
        candidate.columns = [
            normalise_column_name(column) for column in candidate.columns
        ]

        if (
            "Year" in candidate.columns
            and sum(season in candidate.columns for season in SEASONS) == 12
        ):
            history_table = candidate
            break

    if history_table is None:
        raise ValueError("Could not identify the NOAA historical RONI table.")

    history_wide = history_table[["Year", *SEASONS]].copy()

    # NOAA repeats the table headings between decades. Converting Year to
    # numeric removes those presentation-only rows without relying on position.
    history_wide["Year"] = pd.to_numeric(history_wide["Year"], errors="coerce")
    history_wide = history_wide.dropna(subset=["Year"]).copy()
    history_wide["Year"] = history_wide["Year"].astype(int)

    for season in SEASONS:
        history_wide[season] = pd.to_numeric(
            history_wide[season],
            errors="coerce",
        )

    history_wide = (
        history_wide
        .drop_duplicates(subset="Year")
        .sort_values("Year")
        .reset_index(drop=True)
    )

    if history_wide["Year"].min() != 1950:
        raise ValueError(
            f"Unexpected first historical year: {history_wide['Year'].min()}"
        )

    if history_wide["Year"].max() < 2026:
        raise ValueError(
            f"Historical table does not contain 2026; latest year is "
            f"{history_wide['Year'].max()}."
        )

    history_tidy = history_wide.melt(
        id_vars="Year",
        value_vars=SEASONS,
        var_name="season",
        value_name="roni",
    )

    season_order = {season: position for position, season in enumerate(SEASONS)}
    history_tidy["season_order"] = history_tidy["season"].map(season_order)

    history_tidy = (
        history_tidy
        .sort_values(["Year", "season_order"])
        .reset_index(drop=True)
    )

    return history_wide, history_tidy


def parse_forecast(html: str) -> pd.DataFrame:
    """Extract the official NOAA RONI forecast percentile table."""
    tables = pd.read_html(StringIO(html))

    forecast_table = None

    for candidate in tables:
        candidate = candidate.copy()
        candidate.columns = [
            normalise_column_name(column) for column in candidate.columns
        ]

        required = {"Season", *FORECAST_PERCENTILES.keys()}

        if required.issubset(candidate.columns):
            forecast_table = candidate
            break

    if forecast_table is None:
        raise ValueError("Could not identify the NOAA RONI forecast table.")

    forecast = forecast_table[
        ["Season", *FORECAST_PERCENTILES.keys()]
    ].copy()

    # NOAA's first column includes both the three-letter season code and the
    # component month names. Only the season code is required for alignment.
    forecast["season"] = (
        forecast["Season"]
        .astype(str)
        .str.extract(r"^([A-Z]{3})", expand=False)
    )

    forecast = forecast.dropna(subset=["season"]).copy()

    forecast = forecast[
        forecast["season"].isin(SEASONS)
    ].copy()

    forecast = forecast.drop(columns="Season")
    forecast = forecast.rename(columns=FORECAST_PERCENTILES)

    for column in FORECAST_PERCENTILES.values():
        forecast[column] = pd.to_numeric(
            forecast[column],
            errors="coerce",
        )

    expected_forecast_seasons = [
        "JAS", "ASO", "SON", "OND", "NDJ",
        "DJF", "JFM", "FMA", "MAM",
    ]

    if forecast["season"].tolist() != expected_forecast_seasons:
        raise ValueError(
            "Unexpected NOAA forecast seasons: "
            f"{forecast['season'].tolist()}"
        )

    if forecast[list(FORECAST_PERCENTILES.values())].isna().any().any():
        raise ValueError("Missing numeric values found in NOAA forecast table.")

    return forecast.reset_index(drop=True)


def sha256_text(text: str) -> str:
    """Return a checksum so the exact downloaded source snapshot is identifiable."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)

    retrieved_at = datetime.now(timezone.utc)
    snapshot_date = retrieved_at.date().isoformat()

    print("Downloading NOAA RONI history...")
    history_html = fetch_html(HISTORY_URL)

    print("Downloading NOAA official RONI outlook...")
    forecast_html = fetch_html(FORECAST_URL)

    history_raw_path = RAW_DIR / f"noaa_roni_history_{snapshot_date}.html"
    forecast_raw_path = RAW_DIR / f"noaa_roni_outlook_{snapshot_date}.html"

    history_raw_path.write_text(history_html, encoding="utf-8")
    forecast_raw_path.write_text(forecast_html, encoding="utf-8")

    history_wide, history_tidy = parse_history(history_html)
    forecast = parse_forecast(forecast_html)

    history_wide.to_csv(
        CLEANED_DIR / "roni_history_wide.csv",
        index=False,
    )
    history_tidy.to_csv(
        CLEANED_DIR / "roni_history_tidy.csv",
        index=False,
    )
    forecast.to_csv(
        CLEANED_DIR / "roni_forecast_percentiles.csv",
        index=False,
    )

    metadata = {
        "retrieved_at_utc": retrieved_at.isoformat(),
        "history": {
            "url": HISTORY_URL,
            "snapshot_file": history_raw_path.name,
            "sha256": sha256_text(history_html),
        },
        "forecast": {
            "url": FORECAST_URL,
            "snapshot_file": forecast_raw_path.name,
            "sha256": sha256_text(forecast_html),
        },
    }

    with (RAW_DIR / "source_metadata.json").open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(metadata, file, indent=2)

    # Identify the latest genuinely populated observed RONI value rather than
    # assuming that the current calendar year has all twelve seasons available.
    latest_year = history_wide["Year"].max()
    latest_row = history_wide.loc[
        history_wide["Year"] == latest_year,
        SEASONS,
    ].iloc[0]

    available_seasons = latest_row.dropna()

    if available_seasons.empty:
        raise ValueError(f"No observed RONI values found for {latest_year}.")

    latest_season = available_seasons.index[-1]
    latest_value = available_seasons.iloc[-1]

    print()
    print("Preparation complete")
    print("--------------------")
    print(
        f"Historical coverage: "
        f"{history_wide['Year'].min()}-{history_wide['Year'].max()}"
    )
    print(f"Historical year rows: {len(history_wide):,}")
    print(f"Tidy year-season rows: {len(history_tidy):,}")
    print(
        f"Latest observed value: "
        f"{latest_year} {latest_season} = {latest_value:+.1f} C"
    )
    print(
        f"Forecast seasons: "
        f"{forecast['season'].iloc[0]} to {forecast['season'].iloc[-1]}"
    )
    print()
    print("Created:")
    print(f"  {history_raw_path.relative_to(PROJECT_ROOT)}")
    print(f"  {forecast_raw_path.relative_to(PROJECT_ROOT)}")
    print("  data\\raw\\source_metadata.json")
    print("  data\\cleaned\\roni_history_wide.csv")
    print("  data\\cleaned\\roni_history_tidy.csv")
    print("  data\\cleaned\\roni_forecast_percentiles.csv")


if __name__ == "__main__":
    main()
