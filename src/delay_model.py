from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler

from .database import get_project_root

DATE_COLUMNS = [
    "order_date",
    "promised_delivery_date",
    "expected_roj_date",
    "actual_delivery_date",
]

# Standardized to align perfectly with scripts/process.py
NUMERIC_FEATURES = [
    "quantity",
    "contract_value",
    "historical_on_time_rate",
    "communication_score",
    "quality_issues",
    "lead_time",
    "days_until_promised_delivery",
]

# Standardized to align perfectly with scripts/process.py
CATEGORICAL_FEATURES = [
    "material",
    "category",
    "vendor",
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

# Module-level cache: avoids re-reading the CSV on every call (~720 times
# per page load).  The cache is keyed by source so legacy and processed
# data can coexist.
_procurement_data_cache: Dict[str, pd.DataFrame] = {}


def _load_processed_procurement() -> pd.DataFrame:
    """Load and format the processed procurement_master.csv so downstream code
    and fallback ML pipelines see uniform columns."""
    if "processed" in _procurement_data_cache:
        return _procurement_data_cache["processed"].copy()

    path = processed_procurement_path()
    df = pd.read_csv(path)

    # --- Synthesise missing columns that the UI expects ---
    df["po_number"] = [f"PO-{2000 + i}" for i in range(len(df))]

    # Date columns – derive from today and lead time / delay info
    today = _today()
    df["order_date"] = today - pd.to_timedelta(df["lead_time"].clip(lower=1), unit="D")
    df["promised_delivery_date"] = today + pd.to_timedelta(
        df["days_until_promised_delivery"].clip(lower=0), unit="D"
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
    df.loc[df["actual_delay_days"] > 6, "current_status"] = "At Risk"

    df["unit"] = "unit"

    if "quality_issues" not in df.columns:
        df["quality_issues"] = 0

    # Retain UI expected display mappings without breaking the uniform ML features
    df["material_name"] = df["material"]
    df["vendor_name"] = df["vendor"]

    _procurement_data_cache["processed"] = df
    return df.copy()


def _load_legacy_sample(path: Path) -> pd.DataFrame:
    """Load old sample_procurement_data.csv and map columns to uniform schema."""
    df = pd.read_csv(path)
    
    # Structural column normalization to match process.py format
    rename_map = {
        "material_name": "material",
        "vendor_name": "vendor",
        "lead_time_days": "lead_time",
        "days_until_promised": "days_until_promised_delivery",
    }
    df.rename(columns=rename_map, inplace=True)

    for column in DATE_COLUMNS:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce")

    df["lead_time"] = (
        df["promised_delivery_date"] - df["order_date"]
    ).dt.days.fillna(0)
    df["days_until_promised_delivery"] = (
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

    df["material_name"] = df["material"]
    df["vendor_name"] = df["vendor"]
    return df


def load_procurement_data(path: Optional[Path] = None) -> pd.DataFrame:
    """Load procurement data, preferring the processed master CSV."""
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


# ---------------------------------------------------------------------------
# Joblib model paths
# ---------------------------------------------------------------------------

def _joblib_classifier_path() -> Path:
    return get_project_root() / "models" / "delay_risk_classifier.joblib"


def _joblib_regressor_path() -> Path:
    return get_project_root() / "models" / "delay_risk_regressor.joblib"


def _joblib_encoders_path() -> Path:
    return get_project_root() / "models" / "feature_encoders.joblib"


@lru_cache(maxsize=1)
def _joblib_models_available() -> bool:
    return (
        _joblib_classifier_path().exists()
        and _joblib_regressor_path().exists()
        and _joblib_encoders_path().exists()
    )


@lru_cache(maxsize=1)
def _load_joblib_models() -> Tuple[Any, Any, Dict[str, LabelEncoder]]:
    """Load serialized joblib models and label encoders."""
    classifier = joblib.load(_joblib_classifier_path())
    regressor = joblib.load(_joblib_regressor_path())
    encoders = joblib.load(_joblib_encoders_path())
    return classifier, regressor, encoders


# Joblib model feature order (must match scripts/process.py training)
JOBLIB_NUMERIC = [
    "quantity",
    "contract_value",
    "historical_on_time_rate",
    "communication_score",
    "lead_time",
    "days_until_promised_delivery",
]
JOBLIB_CATEGORICAL = ["material", "category", "priority", "project_phase", "criticality"]


def _build_joblib_row(
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
) -> pd.DataFrame:
    """Build a feature row matching the joblib model training schema."""
    defaults = _vendor_defaults(vendor_name, material_name)
    order_ts = pd.to_datetime(order_date)
    promised_ts = pd.to_datetime(promised_delivery_date)
    _, _, encoders = _load_joblib_models()

    raw = {
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
        "lead_time": float((promised_ts - order_ts).days),
        "days_until_promised_delivery": float((promised_ts - _today()).days),
        "material": material_name,
        "category": category or defaults["category"],
        "priority": priority,
        "project_phase": project_phase,
        "criticality": criticality or defaults["criticality"],
    }
    row_df = pd.DataFrame([raw])

    for col in JOBLIB_CATEGORICAL:
        le = encoders.get(col)
        if le is not None:
            val = row_df[col].iloc[0]
            if val in le.classes_:
                row_df[col] = le.transform([val])[0]
            else:
                row_df[col] = 0
        else:
            row_df[col] = 0

    return row_df[JOBLIB_NUMERIC + JOBLIB_CATEGORICAL]


@lru_cache(maxsize=1)
def _trained_models() -> tuple[Pipeline, Pipeline]:
    """Fallback: train sklearn pipelines on the fly from procurement data."""
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


@lru_cache(maxsize=256)
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
        "material": material_name,
        "category": category or defaults["category"],
        "vendor": vendor_name,
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
        "lead_time": float((promised_ts - order_ts).days),
        "days_until_promised_delivery": float((promised_ts - _today()).days),
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
    
    if _joblib_models_available():
        jbl_clf, jbl_reg, _ = _load_joblib_models()
        jbl_row = _build_joblib_row(
            material_name, vendor_name, order_date, promised_delivery_date,
            quantity, priority, project_phase, category, criticality,
            contract_value, historical_on_time_rate, communication_score,
        )
        probabilities = jbl_clf.predict_proba(jbl_row)[0]
        class_probs = dict(zip(jbl_clf.classes_, probabilities))
        jbl_delay = float(max(0, jbl_reg.predict(jbl_row)[0]))
    else:
        classifier, regressor = _trained_models()
        probabilities = classifier.predict_proba(row)[0]
        class_probs = dict(zip(classifier.classes_, probabilities))
        jbl_delay = None

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

    if jbl_delay is not None:
        expected_delay_days = float(max(0, jbl_delay, risk_score / 12 - 2))
    else:
        _, regressor_fb = _trained_models()
        expected_delay_days = float(max(0, regressor_fb.predict(row)[0], risk_score / 12 - 2))
        
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
    """Build delivery risk table using batch vectorized inference.

    Instead of calling predict_delay_risk() 360 times in a loop (each call
    re-reads CSV + runs single-row sklearn), this builds the full feature
    matrix once and runs a single batch predict.  Reduces load from ~5 min
    to ~2 seconds.
    """
    df = load_procurement_data()
    open_rows = df[df["actual_delivery_date"].isna()].copy()

    if open_rows.empty:
        return pd.DataFrame()

    # --- Prepare date strings ------------------------------------------------
    open_rows["_order_date_str"] = open_rows["order_date"].apply(
        lambda x: str(x.date()) if hasattr(x, "date") else str(x)
    )
    open_rows["_promised_date_str"] = open_rows["promised_delivery_date"].apply(
        lambda x: str(x.date()) if hasattr(x, "date") else str(x)
    )

    # --- Build feature matrix for ALL rows at once ----------------------------
    today = _today()
    order_ts = pd.to_datetime(open_rows["_order_date_str"])
    promised_ts = pd.to_datetime(open_rows["_promised_date_str"])

    batch_df = pd.DataFrame({
        "material": open_rows["material_name"].values,
        "category": open_rows["category"].values,
        "vendor": open_rows["vendor_name"].values,
        "priority": open_rows["priority"].values,
        "project_phase": open_rows["project_phase"].values,
        "criticality": open_rows["criticality"].values,
        "quantity": open_rows["quantity"].astype(float).values,
        "contract_value": open_rows["contract_value"].astype(float).values,
        "historical_on_time_rate": open_rows["historical_on_time_rate"].astype(float).values,
        "communication_score": open_rows["communication_score"].astype(float).values,
        "quality_issues": open_rows["quality_issues"].astype(float).values,
        "lead_time": (promised_ts - order_ts).dt.days.astype(float).values,
        "days_until_promised_delivery": (promised_ts - today).dt.days.astype(float).values,
    })

    # --- Single batch ML inference instead of 360 individual calls ------------
    if _joblib_models_available():
        jbl_clf, jbl_reg, encoders = _load_joblib_models()

        # Encode categorical features for joblib models
        jbl_batch = batch_df[JOBLIB_NUMERIC + JOBLIB_CATEGORICAL].copy()
        for col in JOBLIB_CATEGORICAL:
            le = encoders.get(col)
            if le is not None:
                jbl_batch[col] = jbl_batch[col].apply(
                    lambda v, _le=le: _le.transform([v])[0] if v in _le.classes_ else 0
                )
            else:
                jbl_batch[col] = 0

        # ONE call instead of 360
        all_probas = jbl_clf.predict_proba(jbl_batch)
        classes = list(jbl_clf.classes_)
        jbl_delays = np.maximum(0, jbl_reg.predict(jbl_batch))
    else:
        classifier, regressor = _trained_models()
        all_probas = classifier.predict_proba(
            batch_df[CATEGORICAL_FEATURES + NUMERIC_FEATURES]
        )
        classes = list(classifier.classes_)
        jbl_delays = None

    # --- Vectorized risk score (replaces per-row arithmetic) -----------------
    high_idx = classes.index("High") if "High" in classes else None
    med_idx = classes.index("Medium") if "Medium" in classes else None
    low_idx = classes.index("Low") if "Low" in classes else None

    ml_scores = np.zeros(len(all_probas))
    if high_idx is not None:
        ml_scores += all_probas[:, high_idx] * 100
    if med_idx is not None:
        ml_scores += all_probas[:, med_idx] * 58
    if low_idx is not None:
        ml_scores += all_probas[:, low_idx] * 18

    days_until = (promised_ts - today).dt.days.values.astype(float)
    urgency_penalty = np.where(days_until <= 7, 18.0, 0.0)
    vendor_penalty = np.maximum(0.0, (0.82 - batch_df["historical_on_time_rate"].values) * 100)
    quality_penalty = np.minimum(batch_df["quality_issues"].values * 4, 14.0)
    critical_penalty = np.where(
        batch_df["criticality"].str.lower().values == "high", 10.0, 0.0
    )

    risk_scores = np.clip(
        0.62 * ml_scores + urgency_penalty + vendor_penalty + quality_penalty + critical_penalty,
        0, 100,
    )

    # --- Expected delay days -------------------------------------------------
    if jbl_delays is not None:
        expected_delays = np.maximum(0, np.maximum(jbl_delays, risk_scores / 12 - 2))
    else:
        _, regressor_fb = _trained_models()
        fb_delays = np.maximum(0, regressor_fb.predict(
            batch_df[CATEGORICAL_FEATURES + NUMERIC_FEATURES]
        ))
        expected_delays = np.maximum(0, np.maximum(fb_delays, risk_scores / 12 - 2))

    # --- Derive labels -------------------------------------------------------
    risk_levels = np.array([_risk_level(s) for s in risk_scores])
    recommendations = np.array([
        {
            "High": "Escalate with vendor, confirm dispatch evidence, and prepare alternate sourcing.",
            "Medium": "Schedule follow-up and verify logistics milestones within 48 hours.",
            "Low": "Continue routine tracking through the procurement dashboard.",
        }[lvl]
        for lvl in risk_levels
    ])
    expected_roj_dates = [
        str((p + pd.Timedelta(days=round(d))).date())
        for p, d in zip(promised_ts, expected_delays)
    ]

    # --- Assemble output DataFrame -------------------------------------------
    result = pd.DataFrame({
        "material_name": open_rows["material_name"].values,
        "vendor_name": open_rows["vendor_name"].values,
        "order_date": open_rows["_order_date_str"].values,
        "promised_delivery_date": open_rows["_promised_date_str"].values,
        "expected_roj_date": expected_roj_dates,
        "risk_score": np.round(risk_scores, 1),
        "risk_level": risk_levels,
        "expected_delay_days": np.round(expected_delays, 1),
        "recommendation": recommendations,
        "po_number": open_rows["po_number"].values,
        "current_status": open_rows["current_status"].values,
        "priority": open_rows["priority"].values,
        "criticality": open_rows["criticality"].values,
        "quantity": open_rows["quantity"].values,
        "unit": open_rows["unit"].values if "unit" in open_rows.columns else "unit",
        "contract_value": open_rows["contract_value"].values,
    })

    return result.sort_values("risk_score", ascending=False).reset_index(drop=True)