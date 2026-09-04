from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"
VISUALS_DIR = PROJECT_ROOT / "visuals"

HISTORY_FILE = CLEANED_DIR / "roni_history_tidy.csv"
FORECAST_FILE = CLEANED_DIR / "roni_forecast_percentiles.csv"

# These are the historical comparison episodes frozen during the
# specification stage. "Development year" is the calendar year used for
# like-for-like seasonal comparison rather than necessarily the first year
# in which the wider multi-season El Niño episode began.
EXPECTED_HISTORICAL_EVENTS = [
    ("1957–58", 1957),
    ("1965–66", 1965),
    ("1972–73", 1972),
    ("1982–83", 1982),
    ("1986–87", 1986),
    ("1991–92", 1991),
    ("1997–98", 1997),
    ("2009–10", 2009),
    ("2015–16", 2015),
]

CURRENT_EVENT = ("2026–27", 2026)

TRAJECTORY_STAGES = [
    "MAM", "AMJ", "MJJ", "JJA", "JAS",
    "ASO", "SON", "OND", "NDJ", "DJF",
]

FORECAST_CHART_STAGES = [
    "MAM", "AMJ", "MJJ", "JJA",
    "JAS", "ASO", "SON", "OND", "NDJ",
    "DJF", "JFM", "FMA", "MAM",
]



def derive_major_events(history: pd.DataFrame) -> list[tuple[str, int]]:
    """
    Reconstruct the historical comparison cohort from the NOAA RONI series.

    NOAA identifies historical warm episodes using at least five consecutive
    overlapping seasons above +0.5?C. RA01 then applies its pre-agreed
    "major" threshold of a peak RONI of at least +1.5?C.

    The current 2026 event is excluded from this historical episode-selection
    step because its published sequence is still incomplete.
    """
    ordered = (
        history.loc[history["Year"] < 2026]
        .sort_values(["Year", "season_order"])
        .reset_index(drop=True)
        .copy()
    )

    ordered["is_warm"] = ordered["roni"].gt(0.5) & ordered["roni"].notna()

    # A change from warm to non-warm, or vice versa, starts a new run.
    ordered["run_id"] = (
        ordered["is_warm"]
        .ne(ordered["is_warm"].shift())
        .cumsum()
    )

    events = []

    for _, run in ordered.loc[ordered["is_warm"]].groupby("run_id"):
        if len(run) < 5:
            continue

        if run["roni"].max() < 1.5:
            continue

        start_year = int(run.iloc[0]["Year"])
        end_year = int(run.iloc[-1]["Year"])

        if start_year == end_year:
            label = str(start_year)
        else:
            label = f"{start_year}\u2013{str(end_year)[-2:]}"

        events.append((label, start_year))

    # This check protects the frozen analytical design while ensuring the
    # cohort itself is generated from source data rather than hard-coded.
    if events != EXPECTED_HISTORICAL_EVENTS:
        raise ValueError(
            "Source-derived major-event cohort has changed.\n"
            f"Expected: {EXPECTED_HISTORICAL_EVENTS}\n"
            f"Derived:  {events}\n"
            "Reassess the historical comparison before publication."
        )

    return events

def get_roni(
    history: pd.DataFrame,
    development_year: int,
    season: str,
) -> float:
    """
    Return a RONI value for a development-year trajectory.

    MAM through NDJ belong to the development year. DJF, JFM, FMA and
    the following MAM belong to the next calendar year when extending
    the event into the following winter/spring.
    """
    following_year_seasons = {"DJF", "JFM", "FMA"}

    year = (
        development_year + 1
        if season in following_year_seasons
        else development_year
    )

    rows = history.loc[
        (history["Year"] == year)
        & (history["season"] == season),
        "roni",
    ]

    if len(rows) != 1:
        raise ValueError(
            f"Expected one value for {year} {season}; found {len(rows)}."
        )

    return float(rows.iloc[0])


def get_extended_roni(
    history: pd.DataFrame,
    development_year: int,
    position: int,
    season: str,
) -> float:
    """
    Return values for the observation/forecast chart.

    The final MAM in the chart is MAM of the following calendar year,
    whereas the first MAM is from the development year.
    """
    if position >= 9:
        year = development_year + 1
    else:
        year = development_year

    rows = history.loc[
        (history["Year"] == year)
        & (history["season"] == season),
        "roni",
    ]

    if len(rows) != 1:
        raise ValueError(
            f"Expected one value for {year} {season}; found {len(rows)}."
        )

    return float(rows.iloc[0])


def build_event_comparison(history: pd.DataFrame) -> pd.DataFrame:
    """Create the like-for-like historical comparison table."""
    rows = []

    historical_events = derive_major_events(history)

    for event_label, development_year in [
        *historical_events,
        CURRENT_EVENT,
    ]:
        mam = get_roni(history, development_year, "MAM")
        jja = get_roni(history, development_year, "JJA")

        rows.append(
            {
                "event": event_label,
                "development_year": development_year,
                "mam_roni": mam,
                "jja_roni": jja,
                "mam_to_jja_change": jja - mam,
                "is_2026": development_year == 2026,
            }
        )

    comparison = pd.DataFrame(rows)

    comparison["jja_rank"] = (
        comparison["jja_roni"]
        .rank(method="min", ascending=False)
        .astype(int)
    )

    comparison["development_rank"] = (
        comparison["mam_to_jja_change"]
        .rank(method="min", ascending=False)
        .astype(int)
    )

    return comparison


def validate_analysis(
    history: pd.DataFrame,
    comparison: pd.DataFrame,
) -> None:
    """
    Fail loudly if the live extraction no longer supports the frozen
    analytical findings. This protects the published story if NOAA later
    revises recent real-time RONI estimates.
    """
    current = comparison.loc[comparison["is_2026"]].iloc[0]

    if current["jja_roni"] != 1.4:
        raise ValueError(
            "JJA 2026 no longer equals +1.4°C. "
            "Reassess the analysis before publication."
        )

    if current["jja_rank"] != 2:
        raise ValueError(
            f"2026 JJA rank is now {current['jja_rank']}, not 2. "
            "Reassess the analysis."
        )

    if round(current["mam_to_jja_change"], 1) != 1.4:
        raise ValueError(
            "2026 MAM-to-JJA change no longer equals +1.4°C."
        )

    previous = comparison.loc[~comparison["is_2026"]]

    if round(previous["mam_to_jja_change"].max(), 1) != 1.0:
        raise ValueError(
            "Historical maximum MAM-to-JJA change differs from "
            "the frozen +1.0°C comparison."
        )

    historical_max = history.loc[
        history["Year"] < 2026,
        "roni",
    ].max()

    if historical_max != 2.4:
        raise ValueError(
            f"Historical pre-2026 RONI maximum is now "
            f"{historical_max:+.1f}°C rather than +2.4°C."
        )


def create_trajectory_chart(
    history: pd.DataFrame,
) -> None:
    """Chart historical major-event trajectories against observed 2026."""
    fig, ax = plt.subplots(figsize=(11, 7))

    for event_label, development_year in derive_major_events(history):
        values = [
            get_roni(history, development_year, stage)
            for stage in TRAJECTORY_STAGES
        ]

        ax.plot(
            TRAJECTORY_STAGES,
            values,
            marker="o",
            linewidth=1.4,
            alpha=0.55,
            label=event_label,
        )

    current_values = []

    for stage in TRAJECTORY_STAGES:
        if stage in {"MAM", "AMJ", "MJJ", "JJA"}:
            current_values.append(
                get_roni(history, 2026, stage)
            )
        else:
            current_values.append(float("nan"))

    ax.plot(
        TRAJECTORY_STAGES,
        current_values,
        marker="o",
        linewidth=3,
        label="2026–27 observed",
        zorder=10,
    )

    ax.axhline(0, linewidth=0.8, alpha=0.4)

    ax.set_title(
        "The 2026 El Niño developed unusually quickly by mid-year",
        loc="left",
        fontsize=15,
        fontweight="bold",
    )
    ax.set_ylabel("Relative Oceanic Niño Index (°C)")
    ax.set_xlabel("Overlapping three-month season")
    ax.grid(axis="y", alpha=0.2)

    ax.legend(
        title="Development year",
        ncol=2,
        frameon=False,
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
    )

    fig.tight_layout()

    fig.savefig(
        VISUALS_DIR / "01_historical_trajectories.png",
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(fig)


def create_jja_ranking_chart(
    comparison: pd.DataFrame,
) -> None:
    """Show the like-for-like JJA ranking directly."""
    ranked = comparison.sort_values(
        ["jja_roni", "development_year"],
        ascending=[True, True],
    ).copy()

    fig, ax = plt.subplots(figsize=(9, 6.5))

    bars = ax.barh(
        ranked["event"],
        ranked["jja_roni"],
        alpha=0.8,
    )

    current_index = ranked.index[
        ranked["is_2026"]
    ][0]

    current_position = list(ranked.index).index(current_index)
    bars[current_position].set_alpha(1.0)
    bars[current_position].set_linewidth(2)

    for bar, value in zip(bars, ranked["jja_roni"]):
        ax.text(
            value + 0.025,
            bar.get_y() + bar.get_height() / 2,
            f"{value:+.1f}",
            va="center",
            fontsize=10,
        )

    ax.axvline(
        1.5,
        linestyle="--",
        linewidth=1,
        alpha=0.5,
    )

    ax.text(
        1.51,
        -0.75,
        "Strong threshold",
        fontsize=9,
        alpha=0.7,
    )

    ax.set_title(
        "JJA 2026 ranks second among previous major El Niño development years",
        loc="left",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xlabel("JJA Relative Oceanic Niño Index (°C)")
    ax.set_ylabel("")
    ax.grid(axis="x", alpha=0.2)

    fig.tight_layout()

    fig.savefig(
        VISUALS_DIR / "02_jja_same_stage_comparison.png",
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(fig)


def create_forecast_chart(
    history: pd.DataFrame,
    forecast: pd.DataFrame,
) -> None:
    """
    Keep observed 2026 values and NOAA forecast values visually distinct.

    Forecast uncertainty is shown using the published percentile ranges,
    rather than implying that the median forecast is a deterministic path.
    """
    fig, ax = plt.subplots(figsize=(11, 6.5))

    x = list(range(len(FORECAST_CHART_STAGES)))

    observed_x = [0, 1, 2, 3]
    observed_values = [
        get_extended_roni(history, 2026, i, stage)
        for i, stage in enumerate(
            FORECAST_CHART_STAGES[:4]
        )
    ]

    forecast_x = list(range(4, 13))

    if forecast["season"].tolist() != FORECAST_CHART_STAGES[4:]:
        raise ValueError(
            "Forecast season order does not match chart specification."
        )

    ax.plot(
        observed_x,
        observed_values,
        marker="o",
        linewidth=3,
        label="Observed RONI",
        zorder=5,
    )

    # Connect the last observation to the forecast median only as a visual
    # transition. The vertical separator makes the status change explicit.
    forecast_line_x = [3, *forecast_x]
    forecast_line_values = [
        observed_values[-1],
        *forecast["p50"].tolist(),
    ]

    ax.plot(
        forecast_line_x,
        forecast_line_values,
        marker="o",
        linewidth=2,
        linestyle="--",
        label="NOAA median forecast",
        zorder=4,
    )

    ax.fill_between(
        forecast_x,
        forecast["p05"],
        forecast["p95"],
        alpha=0.12,
        label="NOAA 5th–95th percentile",
    )

    ax.fill_between(
        forecast_x,
        forecast["p25"],
        forecast["p75"],
        alpha=0.22,
        label="NOAA 25th–75th percentile",
    )

    historical_max = history.loc[
        history["Year"] < 2026,
        "roni",
    ].max()

    ax.axhline(
        historical_max,
        linestyle=":",
        linewidth=1.5,
        alpha=0.8,
        label=f"Historical observed maximum ({historical_max:+.1f}°C)",
    )

    ax.axvline(
        3.5,
        linewidth=1,
        alpha=0.5,
    )

    ax.text(
        3.63,
        ax.get_ylim()[0] + 0.1,
        "Forecast",
        fontsize=9,
        alpha=0.7,
    )

    ax.set_xticks(x)
    ax.set_xticklabels(FORECAST_CHART_STAGES)

    ax.set_title(
        "NOAA forecasts a possible move beyond the historical RONI range",
        loc="left",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_ylabel("Relative Oceanic Niño Index (°C)")
    ax.set_xlabel("Overlapping three-month season")
    ax.grid(axis="y", alpha=0.2)

    ax.legend(
        frameon=False,
        loc="upper left",
    )

    fig.tight_layout()

    fig.savefig(
        VISUALS_DIR / "03_observed_vs_noaa_forecast.png",
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(fig)


def main() -> None:
    VISUALS_DIR.mkdir(parents=True, exist_ok=True)

    history = pd.read_csv(HISTORY_FILE)
    forecast = pd.read_csv(FORECAST_FILE)

    comparison = build_event_comparison(history)
    validate_analysis(history, comparison)

    comparison.to_csv(
        CLEANED_DIR / "major_event_comparison.csv",
        index=False,
    )

    create_trajectory_chart(history)
    create_jja_ranking_chart(comparison)
    create_forecast_chart(history, forecast)

    current = comparison.loc[comparison["is_2026"]].iloc[0]
    previous = comparison.loc[~comparison["is_2026"]]

    fastest_previous = previous.loc[
        previous["mam_to_jja_change"].idxmax()
    ]

    historical_max = history.loc[
        history["Year"] < 2026,
        "roni",
    ].max()

    print()
    print("Analysis complete")
    print("-----------------")
    print(
        f"JJA 2026 RONI: "
        f"{current['jja_roni']:+.1f} C"
    )
    print(
        f"JJA rank within comparison set: "
        f"{current['jja_rank']} of {len(comparison)}"
    )
    print(
        f"2026 MAM-to-JJA change: "
        f"{current['mam_to_jja_change']:+.1f} C"
    )
    print(
        f"Fastest previous MAM-to-JJA change: "
        f"{fastest_previous['event']} "
        f"{fastest_previous['mam_to_jja_change']:+.1f} C"
    )
    print(
        f"Historical observed RONI maximum before 2026: "
        f"{historical_max:+.1f} C"
    )
    print()
    print("Created:")
    print("  data\\cleaned\\major_event_comparison.csv")
    print("  visuals\\01_historical_trajectories.png")
    print("  visuals\\02_jja_same_stage_comparison.png")
    print("  visuals\\03_observed_vs_noaa_forecast.png")


if __name__ == "__main__":
    main()
