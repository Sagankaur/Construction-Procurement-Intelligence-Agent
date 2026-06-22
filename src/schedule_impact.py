"""Schedule Impact Mapping — determines whether delayed materials consume
schedule float or block the critical path.

Float budgets are assigned per project phase.  When a material delay exceeds
the available float, the item is classified as *Critical Path Blocked*.
"""

from typing import Dict, List

import pandas as pd

from .delay_model import load_procurement_data

# Realistic float budgets (calendar days) per construction phase
PHASE_FLOAT: Dict[str, int] = {
    "Foundation": 5,
    "Superstructure": 3,
    "MEP Rough-In": 2,
    "MEP Fitouts": 2,
    "Finishes": 7,
    "Procurement": 4,
}

DEFAULT_FLOAT = 4  # Fallback for unlisted phases


def _impact_status(delay_days: float, float_days: int) -> str:
    if delay_days <= 0:
        return "🟢 On Track"
    if delay_days <= float_days:
        return "🟡 Float Consumed"
    return "🔴 Critical Path Blocked"


def _severity(status: str) -> int:
    """Numeric severity for sorting (lower = more severe)."""
    if "Blocked" in status:
        return 0
    if "Consumed" in status:
        return 1
    return 2


def get_schedule_impact_table(data: pd.DataFrame | None = None) -> pd.DataFrame:
    """Build the schedule impact mapping table.

    Returns a DataFrame with columns:
        material_name, vendor_name, project_phase, delay_days,
        phase_float, float_remaining, impact_status, severity
    """
    df = data.copy() if data is not None else load_procurement_data()

    # Focus on open (undelivered) or recently delayed items
    mask = df["actual_delivery_date"].isna() | (df["actual_delay_days"].fillna(0) > 0)
    subset = df[mask].copy()

    if subset.empty:
        return pd.DataFrame(
            columns=[
                "material_name",
                "vendor_name",
                "po_number",
                "project_phase",
                "delay_days",
                "phase_float",
                "float_remaining",
                "impact_status",
            ]
        )

    rows: List[Dict] = []
    for _, row in subset.iterrows():
        delay = float(row.get("actual_delay_days", 0) or 0)
        if delay <= 0:
            # For open items, estimate from risk
            delay = float(row.get("observed_delay_days", 0) or 0)

        phase = str(row.get("project_phase", ""))
        phase_float = PHASE_FLOAT.get(phase, DEFAULT_FLOAT)
        remaining = max(0, phase_float - delay)
        status = _impact_status(delay, phase_float)

        rows.append(
            {
                "material_name": row["material_name"],
                "vendor_name": row["vendor_name"],
                "po_number": row.get("po_number", ""),
                "project_phase": phase,
                "delay_days": round(delay, 1),
                "phase_float": phase_float,
                "float_remaining": round(remaining, 1),
                "impact_status": status,
            }
        )

    result = pd.DataFrame(rows)
    result["_severity"] = result["impact_status"].apply(_severity)
    result = result.sort_values(["_severity", "delay_days"], ascending=[True, False])
    result.drop(columns=["_severity"], inplace=True)
    return result.reset_index(drop=True)


def schedule_impact_summary(data: pd.DataFrame | None = None) -> Dict[str, int]:
    """Return counts of each impact status."""
    table = get_schedule_impact_table(data)
    counts = {
        "critical_path_blocked": 0,
        "float_consumed": 0,
        "on_track": 0,
    }
    for status in table["impact_status"]:
        if "Blocked" in status:
            counts["critical_path_blocked"] += 1
        elif "Consumed" in status:
            counts["float_consumed"] += 1
        else:
            counts["on_track"] += 1
    return counts
