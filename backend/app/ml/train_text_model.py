"""Train and evaluate the email text TF-IDF + Logistic Regression model.

Training never downloads data. A local CSV path must be provided explicitly.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import json
from typing import Any

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.ml.preprocess import combine_subject_body, normalize_text


MODEL_VERSION = "email-text-tfidf-logreg-v1"
ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_FILENAME = "email_text_model.joblib"
METRICS_FILENAME = "email_text_metrics.json"
CONFUSION_MATRIX_FILENAME = "email_text_confusion_matrix.csv"
REQUIRED_COLUMNS = {"subject", "body", "label"}


class DatasetValidationError(ValueError):
    """Raised when the explicit training CSV does not match the contract."""


def load_training_data(csv_path: str | Path) -> pd.DataFrame:
    """Load and validate a local training CSV."""
    path = Path(csv_path)
    if not path.is_file():
        raise DatasetValidationError(f"Training CSV does not exist: {path}")

    try:
        frame = pd.read_csv(path)
    except (OSError, ValueError) as exc:
        raise DatasetValidationError(f"Training CSV could not be read: {path}") from exc

    missing_columns = REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise DatasetValidationError(f"Training CSV is missing required columns: {missing}")
    if frame.empty:
        raise DatasetValidationError("Training CSV must contain at least one row")

    frame = frame[["subject", "body", "label"]].copy()
    frame["subject"] = frame["subject"].fillna("").astype(str)
    frame["body"] = frame["body"].fillna("").astype(str)
    frame["label"] = frame["label"].fillna("").astype(str).map(normalize_text)
    if (frame["label"] == "").any():
        raise DatasetValidationError("Every training row must have a non-empty label")
    if frame["label"].nunique() < 2:
        raise DatasetValidationError("Training CSV must contain at least two classes")
    if frame["label"].value_counts().min() < 2:
        raise DatasetValidationError("Each class must contain at least two rows")
    if ((frame["subject"] == "") & (frame["body"] == "")).any():
        raise DatasetValidationError("Each training row must contain subject or body text")
    return frame


def build_pipeline() -> Pipeline:
    """Build the text preprocessing, TF-IDF, and Logistic Regression pipeline."""
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    preprocessor=normalize_text,
                    lowercase=False,
                    ngram_range=(1, 2),
                    min_df=1,
                    sublinear_tf=True,
                ),
            ),
            (
                "classifier",
                LogisticRegression(max_iter=1000, random_state=42, solver="liblinear"),
            ),
        ]
    )


def train_text_model(
    csv_path: str | Path,
    output_dir: str | Path = ARTIFACT_DIR,
    model_version: str = MODEL_VERSION,
) -> dict[str, Any]:
    """Train, evaluate, and save the model and evaluation artifacts."""
    frame = load_training_data(csv_path)
    texts = [combine_subject_body(subject, body) for subject, body in zip(frame["subject"], frame["body"])]
    labels = frame["label"].tolist()

    try:
        x_train, x_test, y_train, y_test = train_test_split(
            texts,
            labels,
            test_size=0.25,
            random_state=42,
            stratify=labels,
        )
    except ValueError as exc:
        raise DatasetValidationError(f"Training data cannot be split safely: {exc}") from exc

    pipeline = build_pipeline()
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    class_labels = [str(label) for label in pipeline.classes_]
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
        "model_version": model_version,
        "pipeline": pipeline,
        "classes": class_labels,
        "input_columns": ["subject", "body"],
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
    parser = argparse.ArgumentParser(description="Train the PhishZero email text model")
    parser.add_argument("--csv", required=True, type=Path, help="Path to a local training CSV")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ARTIFACT_DIR,
        help="Directory for trained artifacts (default: backend/app/ml/artifacts)",
    )
    args = parser.parse_args()
    try:
        result = train_text_model(args.csv, args.output_dir)
    except DatasetValidationError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
