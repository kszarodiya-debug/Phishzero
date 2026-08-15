"""Load and run the saved email text classifier."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib

from app.ml.preprocess import combine_subject_body


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "email_text_model.joblib"


class ModelNotFoundError(FileNotFoundError):
    """Raised when a trained text model artifact is unavailable."""


class ModelFormatError(ValueError):
    """Raised when an artifact does not contain the expected model contract."""


def load_text_model(model_path: str | Path = MODEL_PATH) -> dict[str, Any]:
    """Load and minimally validate a persisted model artifact."""
    path = Path(model_path)
    if not path.is_file():
        raise ModelNotFoundError(
            f"No trained email text model found at {path}. Train one with --csv first."
        )
    try:
        artifact = joblib.load(path)
    except (OSError, ValueError, EOFError) as exc:
        raise ModelFormatError("The email text model artifact could not be loaded") from exc
    if not isinstance(artifact, dict) or not all(
        key in artifact for key in ("pipeline", "model_version", "classes")
    ):
        raise ModelFormatError("The email text model artifact has an invalid format")
    if not hasattr(artifact["pipeline"], "predict_proba"):
        raise ModelFormatError("The email text model does not support probabilities")
    return artifact


def predict_email_text(
    subject: str | None,
    body: str | None,
    model_path: str | Path = MODEL_PATH,
) -> dict[str, str | float]:
    """Return the predicted class, probability, confidence, and model version."""
    artifact = load_text_model(model_path)
    pipeline = artifact["pipeline"]
    text = combine_subject_body(subject, body)
    predicted_class = str(pipeline.predict([text])[0])
    probabilities = pipeline.predict_proba([text])[0]
    classes = [str(label) for label in pipeline.classes_]
    class_index = classes.index(predicted_class)
    probability = float(probabilities[class_index])
    return {
        "class": predicted_class,
        "probability": probability,
        "confidence": probability,
        "model_version": str(artifact["model_version"]),
    }

