"""Defensive, offline analysis of security-relevant email headers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from enum import Enum
from email.utils import getaddresses
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuthenticationState(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    NOT_PRESENT = "NOT_PRESENT"


class AuthenticationResult(BaseModel):
    state: AuthenticationState
    evidence: list[str] = Field(default_factory=list)


class HeaderFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    severity: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class HeaderAnalysisResult(BaseModel):
    headers_present: dict[str, bool]
    authentication: dict[str, AuthenticationResult]
    findings: list[HeaderFinding]


SUPPORTED_HEADERS = (
    "from",
    "reply-to",
    "return-path",
    "received",
    "authentication-results",
)
AUTHENTICATION_METHODS = ("spf", "dkim", "dmarc")
_AUTH_RESULT_PATTERN = re.compile(
    r"(?<![a-z0-9_-])(spf|dkim|dmarc)\s*=\s*"
    r"(pass|fail|neutral|none|softfail|temperror|permerror|unknown)\b",
    re.IGNORECASE,
)
_AUTH_IDENTITY_PATTERN = re.compile(
    r"(?:smtp\.mailfrom|header\.from|header\.d)\s*=\s*([^;\s]+)",
    re.IGNORECASE,
)

def analyze_headers(
    headers: Mapping[str, str | Sequence[str]] | Iterable[Mapping[str, str] | Any],
) -> HeaderAnalysisResult:
    """Analyze available headers without contacting any external service.

    ``headers`` may be a mapping of header names to values or an iterable of
    ``{"name": ..., "value": ...}`` records such as the parsed email schema.
    """
    normalized = _normalize_headers(headers)
    findings: list[HeaderFinding] = []
    authentication = _analyze_authentication(normalized, findings)

    from_addresses = _extract_addresses(normalized.get("from", []))
    reply_to_addresses = _extract_addresses(normalized.get("reply-to", []))
    return_path_addresses = _extract_addresses(normalized.get("return-path", []))
    from_domains = _domains(from_addresses)

    if len(from_addresses) != 1:
        findings.append(
            HeaderFinding(
                code="from_address_count",
                severity="medium",
                message="The From header does not contain exactly one mailbox.",
                details={"addresses": from_addresses},
            )
        )

    if reply_to_addresses and from_addresses and set(reply_to_addresses) != set(from_addresses):
        findings.append(
            HeaderFinding(
                code="reply_to_mismatch",
                severity="medium",
                message="Reply-To does not match the From mailbox.",
                details={"from": from_addresses, "reply_to": reply_to_addresses},
            )
        )

    if return_path_addresses and from_domains:
        return_path_domains = _domains(return_path_addresses)
        if return_path_domains and not return_path_domains.intersection(from_domains):
            findings.append(
                HeaderFinding(
                    code="return_path_mismatch",
                    severity="low",
                    message="Return-Path domain differs from the From domain.",
                    details={"from_domains": sorted(from_domains), "return_path_domains": sorted(return_path_domains)},
                )
            )

    _add_authentication_identity_findings(normalized, from_domains, findings)

    if normalized.get("received") and len(normalized["received"]) > 1:
        findings.append(
            HeaderFinding(
                code="received_chain_present",
                severity="info",
                message="Multiple Received headers are present for review.",
                details={"count": len(normalized["received"])},
            )
        )

    return HeaderAnalysisResult(
        headers_present={
            header_name.title(): bool(normalized.get(header_name))
            for header_name in SUPPORTED_HEADERS
        },
        authentication=authentication,
        findings=findings,
    )


def _normalize_headers(
    headers: Mapping[str, str | Sequence[str]] | Iterable[Mapping[str, str] | Any],
) -> dict[str, list[str]]:
    normalized: dict[str, list[str]] = {header_name: [] for header_name in SUPPORTED_HEADERS}
    if isinstance(headers, Mapping):
        items = headers.items()
        for name, values in items:
            key = str(name).strip().casefold()
            if key not in normalized:
                continue
            if isinstance(values, Sequence) and not isinstance(values, str):
                normalized[key].extend(_clean_header_value(value) for value in values)
            else:
                normalized[key].append(_clean_header_value(values))
        return normalized

    for header in headers:
        if isinstance(header, Mapping):
            name = header.get("name")
            value = header.get("value", "")
        else:
            name = getattr(header, "name", None)
            value = getattr(header, "value", "")
        key = str(name or "").strip().casefold()
        if key in normalized:
            normalized[key].append(_clean_header_value(value))
    return normalized


def _clean_header_value(value: Any) -> str:
    return " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())


def _analyze_authentication(
    headers: dict[str, list[str]],
    findings: list[HeaderFinding],
) -> dict[str, AuthenticationResult]:
    auth_headers = headers.get("authentication-results", [])
    results: dict[str, AuthenticationResult] = {}
    for method in AUTHENTICATION_METHODS:
        matches = [
            (status.casefold(), evidence)
            for header in auth_headers
            for matched_method, status, evidence in _auth_matches(header)
            if matched_method == method
        ]
        if not auth_headers:
            results[method.upper()] = AuthenticationResult(state=AuthenticationState.NOT_PRESENT)
            continue
        if not matches:
            results[method.upper()] = AuthenticationResult(state=AuthenticationState.UNKNOWN)
            continue

        statuses = {status for status, _ in matches}
        if "pass" in statuses and "fail" in statuses:
            state = AuthenticationState.UNKNOWN
            findings.append(
                HeaderFinding(
                    code=f"{method}_result_conflict",
                    severity="medium",
                    message=f"Authentication-Results contains conflicting {method.upper()} outcomes.",
                    details={"outcomes": sorted(statuses)},
                )
            )
        elif "pass" in statuses:
            state = AuthenticationState.PASS
        elif "fail" in statuses:
            state = AuthenticationState.FAIL
        else:
            state = AuthenticationState.UNKNOWN
        results[method.upper()] = AuthenticationResult(
            state=state,
            evidence=[evidence for _, evidence in matches],
        )
    return results


def _auth_matches(value: str) -> list[tuple[str, str, str]]:
    return [
        (method.casefold(), status.casefold(), match.group(0))
        for match in _AUTH_RESULT_PATTERN.finditer(value)
        for method, status in [(match.group(1), match.group(2))]
    ]


def _add_authentication_identity_findings(
    headers: dict[str, list[str]],
    from_domains: set[str],
    findings: list[HeaderFinding],
) -> None:
    if not from_domains or not headers.get("authentication-results"):
        return
    for header in headers["authentication-results"]:
        for identity_match in _AUTH_IDENTITY_PATTERN.finditer(header):
            identity = identity_match.group(1).strip("<>")
            identity_domain = _domain_from_identity(identity)
            if not identity_domain or identity_domain in from_domains:
                continue
            identity_name = identity_match.group(0).split("=", 1)[0].strip().lower()
            findings.append(
                HeaderFinding(
                    code="authentication_identity_mismatch",
                    severity="medium",
                    message="An authentication identity differs from the From domain.",
                    details={
                        "identity_type": identity_name,
                        "identity_domain": identity_domain,
                        "from_domains": sorted(from_domains),
                    },
                )
            )


def _extract_addresses(values: list[str]) -> list[str]:
    addresses: list[str] = []
    seen: set[str] = set()
    for _, address in getaddresses(values):
        normalized = address.strip().casefold()
        if normalized and normalized not in seen:
            seen.add(normalized)
            addresses.append(normalized)
    return addresses


def _domains(addresses: list[str]) -> set[str]:
    return {domain for address in addresses if (domain := _domain_from_identity(address))}


def _domain_from_identity(identity: str) -> str | None:
    address = identity.strip().casefold()
    if "@" in address:
        return address.rsplit("@", 1)[1].strip(".") or None
    if "." in address and " " not in address:
        return address.strip(".") or None
    return None
