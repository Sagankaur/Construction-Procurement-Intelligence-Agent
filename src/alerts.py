from typing import Dict, List

import pandas as pd

from .delay_model import get_delivery_risk_table, load_procurement_data
from .vendor_risk import get_vendor_risk_table

SEVERITY_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}


def _delivery_alert(row: pd.Series) -> Dict[str, object]:
    severity = "Critical" if row["risk_score"] >= 82 else "High"
    return {
        "severity": severity,
        "type": "Delivery Risk",
        "title": f"{row['material_name']} may miss ROJ date",
        "detail": (
            f"{row['po_number']} from {row['vendor_name']} has {row['risk_score']}% "
            f"delay risk and expected ROJ {row['expected_roj_date']}."
        ),
        "action": row["recommendation"],
        "due_date": row["promised_delivery_date"],
    }


def _follow_up_alert(row: pd.Series) -> Dict[str, object]:
    return {
        "severity": "Medium",
        "type": "Follow Up",
        "title": f"Follow up {row['po_number']}",
        "detail": (
            f"{row['material_name']} is due on {row['promised_delivery_date']} "
            f"with {row['risk_level']} risk."
        ),
        "action": "Request dispatch status, transport booking, and revised delivery confirmation.",
        "due_date": row["promised_delivery_date"],
    }


def generate_alerts() -> List[Dict[str, object]]:
    delivery_risk = get_delivery_risk_table()
    vendor_risk = get_vendor_risk_table()
    raw = load_procurement_data()
    alerts: List[Dict[str, object]] = []

    for _, row in delivery_risk[delivery_risk["risk_score"] >= 68].iterrows():
        alerts.append(_delivery_alert(row))

    due_soon = delivery_risk[
        (
            pd.to_datetime(delivery_risk["promised_delivery_date"])
            - pd.Timestamp.today().normalize()
        ).dt.days
        <= 7
    ]
    for _, row in due_soon.iterrows():
        alerts.append(_follow_up_alert(row))

    for _, row in vendor_risk[vendor_risk["risk_level"].eq("High")].iterrows():
        alerts.append(
            {
                "severity": "High",
                "type": "Vendor Risk",
                "title": f"{row['vendor_name']} is high risk",
                "detail": (
                    f"On-time rate is {row['on_time_rate']}% with average delay "
                    f"{row['avg_delay_days']} days across {row['orders']} orders."
                ),
                "action": row["recommendation"],
                "due_date": "",
            }
        )

    critical_delayed = raw[
        raw["criticality"].str.lower().eq("high")
        & raw["current_status"].str.lower().isin(["at risk", "delayed"])
    ]
    for _, row in critical_delayed.iterrows():
        alerts.append(
            {
                "severity": "Critical",
                "type": "Schedule Impact",
                "title": f"Critical material: {row['material_name']}",
                "detail": (
                    f"{row['material_name']} supports {row['project_phase']} and is "
                    f"currently {row['current_status']}."
                ),
                "action": "Review project lookahead and confirm mitigation with site planning.",
                "due_date": str(row["promised_delivery_date"].date()),
            }
        )

    alerts.sort(key=lambda item: SEVERITY_ORDER.get(str(item["severity"]), 99))
    return alerts


def alert_counts() -> Dict[str, int]:
    counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for alert in generate_alerts():
        severity = str(alert["severity"])
        counts[severity] = counts.get(severity, 0) + 1
    return counts
