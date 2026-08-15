"""Train and evaluate the URL static-feature Random Forest model.

Training never downloads data. A local CSV path must be provided explicitly.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import json
from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

from app.services.url_analyzer import URL_FEATURE_NAMES, URLAnalysisError, extract_url_features


MODEL_VERSION = "url-static-random-forest-v1"
ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_FILENAME = "url_model.joblib"
METRICS_FILENAME = "url_model_metrics.json"
CONFUSION_MATRIX_FILENAME = "url_model_confusion_matrix.csv"
REQUIRED_COLUMNS = {"url", "label"}


class URLDatasetValidationError(ValueError):
    """Raised when the explicit URL training CSV is invalid."""


def load_url_training_data(csv_path: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load a local URL CSV and derive the exact analyzer feature matrix."""
    path = Path(csv_path)
    if not path.is_file():
        raise URLDatasetValidationError(f"URL training CSV does not exist: {path}")
    try:
        frame = pd.read_csv(path)
    except (OSError, ValueError) as exc:
        raise URLDatasetValidationError(f"URL training CSV could not be read: {path}") from exc

    missing_columns = REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise URLDatasetValidationError(f"URL training CSV is missing required columns: {missing}")
    if frame.empty:
        raise URLDatasetValidationError("URL training CSV must contain at least one row")

    frame = frame[["url", "label"]].copy()
    frame["url"] = frame["url"].fillna("").astype(str)
    frame["label"] = frame["label"].fillna("").astype(str).str.strip().str.casefold()
    if (frame["url"].str.strip() == "").any():
        raise URLDatasetValidationError("Every URL training row must contain a URL")
    if (frame["label"] == "").any():
        raise URLDatasetValidationError("Every URL training row must have a non-empty label")
    if frame["label"].nunique() < 2:
        raise URLDatasetValidationError("URL training CSV must contain at least two classes")
    if frame["label"].value_counts().min() < 2:
        raise URLDatasetValidationError("Each URL class must contain at least two rows")

    feature_rows: list[dict[str, int]] = []
    for row_number, url in enumerate(frame["url"], start=2):
        try:
            feature_rows.append(extract_url_features(url))
        except URLAnalysisError as exc:
            raise URLDatasetValidationError(f"Invalid URL on CSV row {row_number}: {exc}") from exc
    features = pd.DataFrame(feature_rows, columns=URL_FEATURE_NAMES)
    return frame, features


def train_url_model(
    csv_path: str | Path,
    output_dir: str | Path = ARTIFACT_DIR,
    model_version: str = MODEL_VERSION,
) -> dict[str, Any]:
    """Train, evaluate, and save the URL Random Forest model artifacts."""
    frame, features = load_url_training_data(csv_path)
    labels = frame["label"].tolist()
    feature_matrix = features.to_numpy()
    try:
        x_train, x_test, y_train, y_test = train_test_split(
            feature_matrix,
            labels,
            test_size=0.25,
            random_state=42,
            stratify=labels,
        )
    except ValueError as exc:
        raise URLDatasetValidationError(f"URL training data cannot be split safely: {exc}") from exc

    model = RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    class_labels = [str(label) for label in model.classes_]
    matrix = confusion_matrix(y_test, predictions, labels=class_labels)
    metrics = {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "precision": float(precision_score(y_test, predictions, average="weighted", zero_division=0)),
        "recall": float(recall_score(y_test, predictions, average="weighted", zero_division=0)),
        "f1": float(f1_score(y_test, predictions, average="weighted", zero_division=0)),
        "confusion_matrix": matrix.tolist(),
        "confusion_matrix_labels": class_labels,
    }

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    artifact = {
        "model": model,
        "model_version": model_version,
        "feature_names": list(URL_FEATURE_NAMES),
        "classes": class_labels,
        "metrics": metrics,
        "training_rows": len(frame),
    }
    model_path = destination / MODEL_FILENAME
    metrics_path = destination / METRICS_FILENAME
    matrix_path = destination / CONFUSION_MATRIX_FILENAME
    joblib.dump(artifact, model_path)
    metrics_path.write_text(
        json.dumps(
            {
                "model_version": model_version,
                "training_rows": len(frame),
                **metrics,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    pd.DataFrame(matrix, index=class_labels, columns=class_labels).to_csv(matrix_path, index_label="actual/predicted")

    return {
        "model_version": model_version,
        "training_rows": len(frame),
        "model_path": str(model_path),
        "metrics_path": str(metrics_path),
        "confusion_matrix_path": str(matrix_path),
        **metrics,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the PhishZero URL model")
    parser.add_argument("--csv", required=True, type=Path, help="Path to a local URL training CSV")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ARTIFACT_DIR,
        help="Directory for trained artifacts (default: backend/app/ml/artifacts)",
    )
    args = parser.parse_args()
    try:
        result = train_url_model(args.csv, args.output_dir)
    except URLDatasetValidationError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
