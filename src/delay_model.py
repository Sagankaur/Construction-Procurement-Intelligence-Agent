from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .database import get_project_root

DATE_COLUMNS = [
    "order_date",
    "promised_delivery_date",
    "expected_roj_date",
    "actual_delivery_date",
]

NUMERIC_FEATURES = [
    "quantity",
    "contract_value",
    "historical_on_time_rate",
    "communication_score",
    "quality_issues",
    "lead_time_days",
    "days_until_promised",
]

CATEGORICAL_FEATURES = [
    "material_name",
    "category",
    "vendor_name",
    "priority",
    "project_phase",
    "criticality",
]


def sample_data_path() -> Path:
    return get_project_root() / "data" / "sample_procurement_data.csv"


def processed_procurement_path() -> Path:
    return get_project_root() / "data" / "processed" / "procurement_master.csv"


def _today() -> pd.Timestamp:
    return pd.Timestamp.today().normalize()


def _risk_level(score: float) -> str:
    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def _make_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


# ---------------------------------------------------------------------------
# Data loading – prefers processed CSV, falls back to old sample
# ---------------------------------------------------------------------------

def _load_processed_procurement() -> pd.DataFrame:
    """Load and remap the processed procurement_master.csv so downstream code
    sees the same column names it expects from the old sample CSV."""
    path = processed_procurement_path()
    df = pd.read_csv(path)

    # --- Column remapping ---
    rename_map = {
        "material": "material_name",
        "vendor": "vendor_name",
        "lead_time": "lead_time_days",
        "days_until_promised_delivery": "days_until_promised",
    }
    df.rename(columns=rename_map, inplace=True)

    # --- Synthesise missing columns that the UI / downstream expects ---
    # PO numbers
    df["po_number"] = [f"PO-{2000 + i}" for i in range(len(df))]

    # Date columns – derive from today and lead time / delay info
    today = _today()
    df["order_date"] = today - pd.to_timedelta(df["lead_time_days"].clip(lower=1), unit="D")
    df["promised_delivery_date"] = today + pd.to_timedelta(
        df["days_until_promised"].clip(lower=0), unit="D"
    )
    df["expected_roj_date"] = df["promised_delivery_date"] + pd.to_timedelta(
        df["actual_delay_days"].clip(lower=0), unit="D"
    )
    # Mark ~30% of rows as delivered (those with low delay)
    delivered_mask = df["actual_delay_days"] <= 1
    df["actual_delivery_date"] = pd.NaT
    df.loc[delivered_mask, "actual_delivery_date"] = (
        df.loc[delivered_mask, "promised_delivery_date"]
        + pd.to_timedelta(df.loc[delivered_mask, "actual_delay_days"], unit="D")
    )

    # current_status derived from risk_level
    status_map = {"High": "At Risk", "Medium": "On Track", "Low": "On Track"}
    df["current_status"] = df["risk_level"].map(status_map)
    # Override items with actual_delay_days > 6 as Delayed
    df.loc[df["actual_delay_days"] > 6, "current_status"] = "At Risk"

    # unit column
    df["unit"] = "unit"

    # quality_issues (if missing, fill with 0)
    if "quality_issues" not in df.columns:
        df["quality_issues"] = 0

    return df


def _load_legacy_sample(path: Path) -> pd.DataFrame:
    """Load old sample_procurement_data.csv with original enrichment logic."""
    df = pd.read_csv(path)
    for column in DATE_COLUMNS:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce")

    df["lead_time_days"] = (
        df["promised_delivery_date"] - df["order_date"]
    ).dt.days.fillna(0)
    df["days_until_promised"] = (
        df["promised_delivery_date"] - _today()
    ).dt.days.fillna(0)
    df["actual_delay_days"] = (
        df["actual_delivery_date"] - df["promised_delivery_date"]
    ).dt.days
    df["open_delay_days"] = np.where(
        df["actual_delivery_date"].isna(),
        np.maximum((_today() - df["promised_delivery_date"]).dt.days.fillna(0), 0),
        0,
    )
    df["observed_delay_days"] = (
        df["actual_delay_days"].fillna(0).clip(lower=0) + df["open_delay_days"]
    )
    df["target_delay_days"] = np.where(
        df["current_status"].str.lower().eq("at risk"),
        np.maximum(df["observed_delay_days"], 6),
        df["observed_delay_days"],
    )
    df["target_risk"] = pd.cut(
        df["target_delay_days"],
        bins=[-1, 2, 7, 999],
        labels=["Low", "Medium", "High"],
    ).astype(str)
    df.loc[
        df["priority"].str.lower().eq("critical")
        & df["current_status"].str.lower().isin(["at risk", "delayed"]),
        "target_risk",
    ] = "High"
    return df


def load_procurement_data(path: Optional[Path] = None) -> pd.DataFrame:
    """Load procurement data, preferring the processed master CSV.

    Falls back to the old sample CSV if the processed file is absent or
    if an explicit *path* is provided.
    """
    if path is not None:
        return _load_legacy_sample(Path(path))

    proc_path = processed_procurement_path()
    if proc_path.exists():
        df = _load_processed_procurement()
    else:
        df = _load_legacy_sample(sample_data_path())

    # Ensure derived delay columns exist for downstream consumers
    if "observed_delay_days" not in df.columns:
        df["open_delay_days"] = np.where(
            df["actual_delivery_date"].isna(),
            np.maximum((_today() - df["promised_delivery_date"]).dt.days.fillna(0), 0),
            0,
        )
        df["observed_delay_days"] = (
            df["actual_delay_days"].fillna(0).clip(lower=0) + df.get("open_delay_days", 0)
        )
    if "target_delay_days" not in df.columns:
        df["target_delay_days"] = df["actual_delay_days"].fillna(0).clip(lower=0)
    if "target_risk" not in df.columns:
        df["target_risk"] = df.get("risk_level", "Low")

    return df


@lru_cache(maxsize=1)
def _trained_models() -> tuple[Pipeline, Pipeline]:
    df = load_procurement_data()
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", _make_encoder(), CATEGORICAL_FEATURES),
            ("num", StandardScaler(), NUMERIC_FEATURES),
        ]
    )
    classifier = Pipeline(
        steps=[
            ("pre", preprocessor),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=80,
                    max_depth=5,
                    random_state=42,
                    class_weight="balanced",
                ),
            ),
        ]
    )
    regressor = Pipeline(
        steps=[
            ("pre", preprocessor),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=80,
                    max_depth=5,
                    random_state=42,
                ),
            ),
        ]
    )
    classifier.fit(df[CATEGORICAL_FEATURES + NUMERIC_FEATURES], df["target_risk"])
    regressor.fit(df[CATEGORICAL_FEATURES + NUMERIC_FEATURES], df["target_delay_days"])
    return classifier, regressor


def _vendor_defaults(vendor_name: str, material_name: str) -> Dict[str, Any]:
    df = load_procurement_data()
    vendor_rows = df[df["vendor_name"].str.lower() == vendor_name.lower()]
    material_rows = df[df["material_name"].str.lower() == material_name.lower()]
    source = vendor_rows if not vendor_rows.empty else material_rows
    if source.empty:
        source = df
    return {
        "category": source["category"].mode().iat[0],
        "criticality": source["criticality"].mode().iat[0],
        "contract_value": float(source["contract_value"].median()),
        "historical_on_time_rate": float(source["historical_on_time_rate"].median()),
        "communication_score": float(source["communication_score"].median()),
        "quality_issues": float(source["quality_issues"].median()),
    }


def _row_for_prediction(
    material_name: str,
    vendor_name: str,
    order_date: str,
    promised_delivery_date: str,
    quantity: float,
    priority: str,
    project_phase: str,
    category: Optional[str] = None,
    criticality: Optional[str] = None,
    contract_value: Optional[float] = None,
    historical_on_time_rate: Optional[float] = None,
    communication_score: Optional[float] = None,
    quality_issues: Optional[float] = None,
) -> pd.DataFrame:
    defaults = _vendor_defaults(vendor_name, material_name)
    order_ts = pd.to_datetime(order_date)
    promised_ts = pd.to_datetime(promised_delivery_date)
    row = {
        "material_name": material_name,
        "category": category or defaults["category"],
        "vendor_name": vendor_name,
        "priority": priority,
        "project_phase": project_phase,
        "criticality": criticality or defaults["criticality"],
        "quantity": float(quantity),
        "contract_value": float(contract_value or defaults["contract_value"]),
        "historical_on_time_rate": float(
            historical_on_time_rate
            if historical_on_time_rate is not None
            else defaults["historical_on_time_rate"]
        ),
        "communication_score": float(
            communication_score
            if communication_score is not None
            else defaults["communication_score"]
        ),
        "quality_issues": float(
            quality_issues if quality_issues is not None else defaults["quality_issues"]
        ),
        "lead_time_days": float((promised_ts - order_ts).days),
        "days_until_promised": float((promised_ts - _today()).days),
    }
    return pd.DataFrame([row])


def predict_delay_risk(
    material_name: str,
    vendor_name: str,
    order_date: str,
    promised_delivery_date: str,
    quantity: float,
    priority: str = "Medium",
    project_phase: str = "Procurement",
    category: Optional[str] = None,
    criticality: Optional[str] = None,
    contract_value: Optional[float] = None,
    historical_on_time_rate: Optional[float] = None,
    communication_score: Optional[float] = None,
    quality_issues: Optional[float] = None,
) -> Dict[str, Any]:
    row = _row_for_prediction(
        material_name,
        vendor_name,
        order_date,
        promised_delivery_date,
        quantity,
        priority,
        project_phase,
        category,
        criticality,
        contract_value,
        historical_on_time_rate,
        communication_score,
        quality_issues,
    )
    classifier, regressor = _trained_models()
    probabilities = classifier.predict_proba(row)[0]
    class_probs = dict(zip(classifier.classes_, probabilities))
    ml_score = (
        class_probs.get("High", 0) * 100
        + class_probs.get("Medium", 0) * 58
        + class_probs.get("Low", 0) * 18
    )

    promised = pd.to_datetime(promised_delivery_date)
    days_until = int((promised - _today()).days)
    urgency_penalty = 18 if days_until <= 7 else 0
    vendor_penalty = max(0.0, (0.82 - float(row["historical_on_time_rate"].iat[0])) * 100)
    quality_penalty = min(float(row["quality_issues"].iat[0]) * 4, 14)
    critical_penalty = 10 if str(row["criticality"].iat[0]).lower() == "high" else 0
    risk_score = float(
        np.clip(
            0.62 * ml_score
            + urgency_penalty
            + vendor_penalty
            + quality_penalty
            + critical_penalty,
            0,
            100,
        )
    )

    expected_delay_days = float(max(0, regressor.predict(row)[0], risk_score / 12 - 2))
    expected_roj_date = (promised + pd.Timedelta(days=round(expected_delay_days))).date()
    risk_level = _risk_level(risk_score)
    recommendation = {
        "High": "Escalate with vendor, confirm dispatch evidence, and prepare alternate sourcing.",
        "Medium": "Schedule follow-up and verify logistics milestones within 48 hours.",
        "Low": "Continue routine tracking through the procurement dashboard.",
    }[risk_level]
    return {
        "material_name": material_name,
        "vendor_name": vendor_name,
        "order_date": str(pd.to_datetime(order_date).date()),
        "promised_delivery_date": str(promised.date()),
        "expected_roj_date": str(expected_roj_date),
        "risk_score": round(risk_score, 1),
        "risk_level": risk_level,
        "expected_delay_days": round(expected_delay_days, 1),
        "recommendation": recommendation,
    }


def get_delivery_risk_table() -> pd.DataFrame:
    df = load_procurement_data()
    rows = []
    open_rows = df[df["actual_delivery_date"].isna()].copy()
    for _, row in open_rows.iterrows():
        prediction = predict_delay_risk(
            material_name=row["material_name"],
            vendor_name=row["vendor_name"],
            order_date=str(row["order_date"].date()) if hasattr(row["order_date"], "date") else str(row["order_date"]),
            promised_delivery_date=str(row["promised_delivery_date"].date()) if hasattr(row["promised_delivery_date"], "date") else str(row["promised_delivery_date"]),
            quantity=float(row["quantity"]),
            priority=row["priority"],
            project_phase=row["project_phase"],
            category=row["category"],
            criticality=row["criticality"],
            contract_value=float(row["contract_value"]),
            historical_on_time_rate=float(row["historical_on_time_rate"]),
            communication_score=float(row["communication_score"]),
            quality_issues=float(row["quality_issues"]),
        )
        prediction.update(
            {
                "po_number": row["po_number"],
                "current_status": row["current_status"],
                "priority": row["priority"],
                "criticality": row["criticality"],
                "quantity": row["quantity"],
                "unit": row.get("unit", "unit"),
                "contract_value": row["contract_value"],
            }
        )
        rows.append(prediction)
    return pd.DataFrame(rows).sort_values("risk_score", ascending=False)
