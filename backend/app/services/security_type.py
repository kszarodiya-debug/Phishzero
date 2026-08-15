"""Human-readable security type derived from the configured risk classification."""

from typing import Literal


SecurityType = Literal["SECURE", "LESS_SECURE", "SUSPICIOUS", "UNSAFE"]

_SECURITY_TYPES: dict[str, SecurityType] = {
    "SAFE": "SECURE",
    "LOW_RISK": "LESS_SECURE",
    "SUSPICIOUS": "SUSPICIOUS",
    "PHISHING": "UNSAFE",
}


def security_type_for(classification: str) -> SecurityType:
    """Return the user-facing security type without changing risk classification."""
    return _SECURITY_TYPES.get(str(classification).upper(), "SUSPICIOUS")

