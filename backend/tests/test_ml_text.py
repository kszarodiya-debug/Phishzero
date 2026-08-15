from pathlib import Path

import pytest

from app.ml.predict import ModelNotFoundError, load_text_model, predict_email_text
from app.ml.preprocess import combine_subject_body, normalize_text
from app.ml.train_text_model import train_text_model


FIXTURE_CSV = Path(__file__).parent / "fixtures" / "email_text_fixture.csv"


def test_preprocessing_removes_markup_and_normalizes_text() -> None:
    normalized = normalize_text(
        "<script>alert('do not run')</script><b>Visit HTTPS://Example.com/A</b>"
    )

    assert "alert" not in normalized
    assert "visit" in normalized
    assert "url" in normalized
    assert combine_subject_body("Subject line", "Body text") == "subject subject line body body text"


def test_training_saves_model_and_evaluation_artifacts(tmp_path: Path) -> None:
    output_dir = tmp_path / "artifacts"

    result = train_text_model(FIXTURE_CSV, output_dir)

    assert result["model_version"] == "email-text-tfidf-logreg-v1"
    assert set(("accuracy", "precision", "recall", "f1")).issubset(result)
    assert Path(result["model_path"]).is_file()
    assert Path(result["metrics_path"]).is_file()
    assert Path(result["confusion_matrix_path"]).is_file()
    assert 0 <= result["accuracy"] <= 1


def test_model_loading(tmp_path: Path) -> None:
    result = train_text_model(FIXTURE_CSV, tmp_path / "artifacts")

    artifact = load_text_model(result["model_path"])

    assert artifact["model_version"] == "email-text-tfidf-logreg-v1"
    assert artifact["classes"] == ["ham", "spam"]


def test_prediction_returns_required_fields(tmp_path: Path) -> None:
    result = train_text_model(FIXTURE_CSV, tmp_path / "artifacts")

    prediction = predict_email_text(
        "You won a cash prize",
        "Claim your reward immediately.",
        result["model_path"],
    )

    assert set(prediction) == {"class", "probability", "confidence", "model_version"}
    assert prediction["class"] in {"ham", "spam"}
    assert 0 <= prediction["probability"] <= 1
    assert prediction["confidence"] == prediction["probability"]
    assert prediction["model_version"] == "email-text-tfidf-logreg-v1"


def test_missing_model_handling(tmp_path: Path) -> None:
    with pytest.raises(ModelNotFoundError):
        load_text_model(tmp_path / "missing-model.joblib")

