from typing import Optional

import numpy as np
import pandas as pd

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


def get_vendor_risk_table(data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
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
