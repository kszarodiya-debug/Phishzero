from pathlib import Path

import pytest

from app.ml.train_url_model import train_url_model
from app.services.url_analyzer import (
    URLAnalysisError,
    URL_FEATURE_NAMES,
    analyze_url,
    extract_url_features,
)


FIXTURE_CSV = Path(__file__).parent / "fixtures" / "url_fixture.csv"


def test_normal_url() -> None:
    features = extract_url_features("https://www.example.com/account/settings")

    assert set(features) == set(URL_FEATURE_NAMES)
    assert features["url_length"] == len("https://www.example.com/account/settings")
    assert features["hostname_length"] == len("www.example.com")
    assert features["path_length"] == len("/account/settings")
    assert features["subdomain_count"] == 1
    assert features["has_ip_address"] == 0
    assert features["has_at_symbol"] == 0
    assert features["uses_https"] == 1
    assert features["suspicious_shortening_pattern"] == 0


def test_suspicious_url() -> None:
    features = extract_url_features("http://bit.ly/verify-account")

    assert features["uses_https"] == 0
    assert features["hyphen_count"] == 1
    assert features["suspicious_shortening_pattern"] == 1


def test_malformed_url() -> None:
    with pytest.raises(URLAnalysisError):
        extract_url_features("not a URL")


def test_ip_based_url() -> None:
    features = extract_url_features("http://198.51.100.42/login")

    assert features["has_ip_address"] == 1
    assert features["hostname_length"] == len("198.51.100.42")
    assert features["subdomain_count"] == 0


def test_url_with_at_symbol() -> None:
    features = extract_url_features("http://trusted.example@198.51.100.7/verify")

    assert features["has_at_symbol"] == 1
    assert features["has_ip_address"] == 1


def test_long_url() -> None:
    long_url = "https://example.com/" + ("a" * 500)

    features = extract_url_features(long_url)

    assert features["url_length"] == len(long_url)
    assert features["path_length"] == 501


def test_random_forest_training_and_analysis(tmp_path: Path) -> None:
    result = train_url_model(FIXTURE_CSV, tmp_path / "artifacts")

    prediction = analyze_url(
        "http://bit.ly/claim-prize",
        result["model_path"],
    )

    assert set(prediction) == {"features", "probability", "classification"}
    assert set(prediction["features"]) == set(URL_FEATURE_NAMES)
    assert prediction["features"]["suspicious_shortening_pattern"] == 1
    assert prediction["classification"] in {"benign", "phishing"}
    assert 0 <= prediction["probability"] <= 1
    assert Path(result["metrics_path"]).is_file()
    assert Path(result["confusion_matrix_path"]).is_file()

