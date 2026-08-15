"""Static URL feature extraction and local Random Forest prediction.

Every operation in this module uses only the supplied URL string. It never
resolves, visits, crawls, scans, downloads, or executes anything.
"""

from __future__ import annotations

from ipaddress import ip_address
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit

import joblib


URL_FEATURE_NAMES = (
    "url_length",
    "hostname_length",
    "path_length",
    "subdomain_count",
    "has_ip_address",
    "has_at_symbol",
    "hyphen_count",
    "digit_count",
    "special_character_count",
    "uses_https",
    "suspicious_shortening_pattern",
)

SHORTENING_HOSTNAMES = frozenset(
    {
        "bit.ly",
        "buff.ly",
        "cutt.ly",
        "goo.gl",
        "is.gd",
        "lnkd.in",
        "ow.ly",
        "rb.gy",
        "rebrand.ly",
        "shorturl.at",
        "s.id",
        "soo.gd",
        "t.co",
        "tiny.cc",
        "tinyurl.com",
        "trib.al",
    }
)

ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "ml" / "artifacts"
URL_MODEL_PATH = ARTIFACT_DIR / "url_model.joblib"
_CONTROL_CHARACTER_PATTERN = re.compile(r"[\x00-\x1f\x7f]")


class URLAnalysisError(ValueError):
    """Raised when a URL string cannot be safely analyzed."""


class URLModelNotFoundError(FileNotFoundError):
    """Raised when the URL model has not been trained or is unavailable."""


class URLModelFormatError(ValueError):
    """Raised when a URL model artifact does not match the feature contract."""


def extract_url_features(url: str) -> dict[str, int]:
    """Extract static URL features without performing any network operation."""
    normalized_url = _validate_url(url)
    parsed = urlsplit(normalized_url)
    hostname = (parsed.hostname or "").lower().rstrip(".")
    is_ip_address = _is_ip_address(hostname)
    hostname_parts = [part for part in hostname.split(".") if part]
    subdomain_count = max(len(hostname_parts) - 2, 0) if hostname and not is_ip_address else 0

    return {
        "url_length": len(normalized_url),
        "hostname_length": len(hostname),
        "path_length": len(parsed.path),
        "subdomain_count": subdomain_count,
        "has_ip_address": int(is_ip_address),
        "has_at_symbol": int("@" in normalized_url),
        "hyphen_count": normalized_url.count("-"),
        "digit_count": sum(character.isdigit() for character in normalized_url),
        "special_character_count": sum(not character.isalnum() for character in normalized_url),
        "uses_https": int(parsed.scheme.lower() == "https"),
        "suspicious_shortening_pattern": int(hostname in SHORTENING_HOSTNAMES),
    }


def load_url_model(model_path: str | Path = URL_MODEL_PATH) -> dict[str, Any]:
    """Load and validate a persisted URL Random Forest artifact."""
    path = Path(model_path)
    if not path.is_file():
        raise URLModelNotFoundError(
            f"No trained URL model found at {path}. Train one with --csv first."
        )
    try:
        artifact = joblib.load(path)
    except (OSError, ValueError, EOFError) as exc:
        raise URLModelFormatError("The URL model artifact could not be loaded") from exc
    if not isinstance(artifact, dict) or not all(
        key in artifact for key in ("model", "model_version", "feature_names", "classes")
    ):
        raise URLModelFormatError("The URL model artifact has an invalid format")
    if tuple(artifact["feature_names"]) != URL_FEATURE_NAMES:
        raise URLModelFormatError("The URL model feature contract does not match the analyzer")
    if not hasattr(artifact["model"], "predict_proba"):
        raise URLModelFormatError("The URL model does not support probabilities")
    return artifact


def analyze_url(url: str, model_path: str | Path = URL_MODEL_PATH) -> dict[str, object]:
    """Return static features and a model classification for a URL string."""
    features = extract_url_features(url)
    artifact = load_url_model(model_path)
    model = artifact["model"]
    vector = [[features[name] for name in URL_FEATURE_NAMES]]
    classification = str(model.predict(vector)[0])
    probabilities = model.predict_proba(vector)[0]
    classes = [str(label) for label in model.classes_]
    probability = float(probabilities[classes.index(classification)])
    return {
        "features": features,
        "probability": probability,
        "classification": classification,
    }


def _validate_url(url: str) -> str:
    if not isinstance(url, str):
        raise URLAnalysisError("URL must be a string")
    normalized_url = url.strip()
    if not normalized_url or len(normalized_url) > 8_192:
        raise URLAnalysisError("URL must be between 1 and 8192 characters")
    if _CONTROL_CHARACTER_PATTERN.search(normalized_url) or any(character.isspace() for character in normalized_url):
        raise URLAnalysisError("URL cannot contain whitespace or control characters")
    try:
        parsed = urlsplit(normalized_url)
        hostname = parsed.hostname
    except ValueError as exc:
        raise URLAnalysisError("URL is malformed") from exc
    if parsed.scheme.lower() not in {"http", "https"} or not hostname:
        raise URLAnalysisError("URL must use http or https and include a hostname")
    return normalized_url


def _is_ip_address(hostname: str) -> bool:
    try:
        ip_address(hostname)
    except ValueError:
        return False
    return True

