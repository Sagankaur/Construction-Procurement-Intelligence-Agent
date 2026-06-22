from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from .database import get_project_root
from .delay_model import load_procurement_data


def _level(score: float) -> str:
    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def _recommendation(level: str) -> str:
    if level == "High":
        return "Escalate commercial review and identify backup vendors."
    if level == "Medium":
        return "Increase delivery milestone checks and request weekly updates."
    return "Continue normal vendor management cadence."


def vendor_master_path() -> Path:
    return get_project_root() / "data" / "processed" / "vendor_master.csv"


def load_vendor_master() -> Optional[pd.DataFrame]:
    """Load the processed vendor_master.csv if it exists."""
    path = vendor_master_path()
    if not path.exists():
        return None
    df = pd.read_csv(path)
    # Remap column names to SiteSage standard
    rename_map = {"Supplier_Name": "vendor_name"}
    df.rename(columns=rename_map, inplace=True)
    # Fill missing communication_score values
    if "communication_score" in df.columns:
        df["communication_score"] = pd.to_numeric(
            df["communication_score"], errors="coerce"
        ).fillna(5.0)
    return df


def get_vendor_risk_table(data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Build the vendor risk table.

    First checks for the processed vendor_master.csv for pre-computed vendor
    scores.  Falls back to computing from the raw procurement data.
    """
    vendor_master = load_vendor_master()
    if vendor_master is not None and data is None:
        # Use pre-computed vendor master from processed data
        procurement_df = load_procurement_data()
        rows = []
        for _, vrow in vendor_master.iterrows():
            vendor = vrow["vendor_name"]
            # Get procurement records for this vendor
            vdata = procurement_df[
                procurement_df["vendor_name"].str.lower() == vendor.lower()
            ]
            orders = len(vdata) if not vdata.empty else 0
            open_orders = (
                int(vdata["actual_delivery_date"].isna().sum())
                if not vdata.empty
                else 0
            )
            materials = (
                ", ".join(sorted(vdata["material_name"].unique())[:3])
                if not vdata.empty
                else ""
            )
            risk_score = float(vrow.get("vendor_risk_score", 0))
            level = str(vrow.get("risk_level", _level(risk_score)))
            rows.append(
                {
                    "vendor_name": vendor,
                    "orders": orders,
                    "open_orders": open_orders,
                    "on_time_rate": round(
                        float(vrow.get("historical_on_time_rate", 0)) * 100, 1
                    ),
                    "avg_delay_days": round(
                        float(vrow.get("average_delay_days", 0)), 1
                    ),
                    "quality_issues": int(vrow.get("quality_issues", 0)),
                    "communication_score": round(
                        float(vrow.get("communication_score", 5.0)), 1
                    ),
                    "risk_score": round(risk_score, 1),
                    "risk_level": level,
                    "materials": materials,
                    "recommendation": _recommendation(level),
                }
            )
        return pd.DataFrame(rows).sort_values("risk_score", ascending=False)

    # Fallback: compute from procurement data
    df = data.copy() if data is not None else load_procurement_data()
    rows = []
    for vendor, group in df.groupby("vendor_name"):
        delivered = group[group["actual_delivery_date"].notna()]
        delayed_deliveries = delivered[delivered["observed_delay_days"] > 0]
        open_risky = group[
            group["actual_delivery_date"].isna()
            & group["current_status"].str.lower().isin(["at risk", "delayed"])
        ]
        on_time_rate = (
            1 - len(delayed_deliveries) / len(delivered)
            if len(delivered)
            else group["historical_on_time_rate"].mean()
        )
        avg_delay = float(group["observed_delay_days"].mean())
        communication_score = float(group["communication_score"].mean())
        quality_issues = float(group["quality_issues"].sum())
        risk_score = float(
            np.clip(
                (1 - on_time_rate) * 42
                + min(avg_delay * 4, 24)
                + len(open_risky) * 14
                + max(0, 8 - communication_score) * 5
                + min(quality_issues * 3, 12),
                0,
                100,
            )
        )
        materials = ", ".join(sorted(group["material_name"].unique())[:3])
        level = _level(risk_score)
        rows.append(
            {
                "vendor_name": vendor,
                "orders": int(len(group)),
                "open_orders": int(group["actual_delivery_date"].isna().sum()),
                "on_time_rate": round(on_time_rate * 100, 1),
                "avg_delay_days": round(avg_delay, 1),
                "quality_issues": int(quality_issues),
                "communication_score": round(communication_score, 1),
                "risk_score": round(risk_score, 1),
                "risk_level": level,
                "materials": materials,
                "recommendation": _recommendation(level),
            }
        )
    return pd.DataFrame(rows).sort_values("risk_score", ascending=False)


def high_risk_vendors(limit: int = 5) -> pd.DataFrame:
    table = get_vendor_risk_table()
    return table[table["risk_level"].eq("High")].head(limit)
