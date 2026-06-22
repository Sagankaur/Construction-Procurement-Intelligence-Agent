"""Generate joblib model artifacts from the processed procurement CSV.

This script trains a RandomForestClassifier (risk level) and
RandomForestRegressor (delay days) on ``data/processed/procurement_master.csv``
and saves the serialised artefacts that the SiteSage delay-prediction UI loads
at runtime.

Run from the repository root:
    python scripts/generate_models.py
"""

import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

PROCESSED_DIR = os.path.join("data", "processed")
MODELS_DIR = "models"

os.makedirs(MODELS_DIR, exist_ok=True)

csv_path = os.path.join(PROCESSED_DIR, "procurement_master.csv")
if not os.path.exists(csv_path):
    print(f"ERROR: {csv_path} not found. Run the data pipeline first.")
    sys.exit(1)

print("Loading processed procurement data …")
df = pd.read_csv(csv_path)

# --- Feature engineering (mirrors scripts/process.py) ---
numeric_features = [
    "quantity",
    "contract_value",
    "historical_on_time_rate",
    "communication_score",
    "lead_time",
    "days_until_promised_delivery",
]
categorical_features = ["material", "category", "priority", "project_phase", "criticality"]

X = df[numeric_features].copy()

encoders: dict[str, LabelEncoder] = {}
for col in categorical_features:
    le = LabelEncoder()
    X[col] = le.fit_transform(df[col].astype(str))
    encoders[col] = le

y_class = df["risk_level"].astype(str)
y_reg = df["actual_delay_days"]

# --- Train / test split ---
X_train, X_test, y_train_c, y_test_c = train_test_split(
    X, y_class, test_size=0.2, random_state=42, stratify=y_class,
)
X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(
    X, y_reg, test_size=0.2, random_state=42,
)

# --- Oversample minority classes in training set ---
train_df = X_train.copy()
train_df["target"] = y_train_c.values
max_size = train_df["target"].value_counts().max()
parts = [train_df]
for _, group in train_df.groupby("target"):
    if len(group) < max_size:
        parts.append(group.sample(max_size - len(group), replace=True, random_state=42))
train_balanced = pd.concat(parts)
X_train_balanced = train_balanced.drop(columns=["target"])
y_train_balanced = train_balanced["target"]

# --- Train models ---
print("Training classifier …")
clf = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10, min_samples_leaf=2)
clf.fit(X_train_balanced, y_train_balanced)

print("Training regressor …")
reg = RandomForestRegressor(n_estimators=100, random_state=42)
reg.fit(X_train_r, y_train_r)

# --- Save artefacts ---
joblib.dump(clf, os.path.join(MODELS_DIR, "delay_risk_classifier.joblib"))
joblib.dump(reg, os.path.join(MODELS_DIR, "delay_risk_regressor.joblib"))
joblib.dump(encoders, os.path.join(MODELS_DIR, "feature_encoders.joblib"))

print("✓ Saved delay_risk_classifier.joblib")
print("✓ Saved delay_risk_regressor.joblib")
print("✓ Saved feature_encoders.joblib")
print("Model generation complete.")
