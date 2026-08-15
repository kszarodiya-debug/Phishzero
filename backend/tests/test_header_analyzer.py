from app.services.header_analyzer import AuthenticationState, analyze_headers


def test_spf_pass() -> None:
    result = analyze_headers(
        {
            "From": "sender@example.com",
            "Authentication-Results": "mx.example; spf=pass smtp.mailfrom=example.com",
        }
    )

    assert result.authentication["SPF"].state is AuthenticationState.PASS


def test_spf_fail() -> None:
    result = analyze_headers(
        {
            "From": "sender@example.com",
            "Authentication-Results": "mx.example; spf=fail smtp.mailfrom=bad.example",
        }
    )

    assert result.authentication["SPF"].state is AuthenticationState.FAIL


def test_dkim_pass() -> None:
    result = analyze_headers(
        {
            "From": "sender@example.com",
            "Authentication-Results": "mx.example; dkim=pass header.d=example.com",
        }
    )

    assert result.authentication["DKIM"].state is AuthenticationState.PASS


def test_dkim_fail() -> None:
    result = analyze_headers(
        {
            "From": "sender@example.com",
            "Authentication-Results": "mx.example; dkim=fail header.d=bad.example",
        }
    )

    assert result.authentication["DKIM"].state is AuthenticationState.FAIL


def test_dmarc_pass() -> None:
    result = analyze_headers(
        {
            "From": "sender@example.com",
            "Authentication-Results": "mx.example; dmarc=pass header.from=example.com",
        }
    )

    assert result.authentication["DMARC"].state is AuthenticationState.PASS


def test_dmarc_fail() -> None:
    result = analyze_headers(
        {
            "From": "sender@example.com",
            "Authentication-Results": "mx.example; dmarc=fail header.from=bad.example",
        }
    )

    assert result.authentication["DMARC"].state is AuthenticationState.FAIL


def test_missing_authentication_headers_are_not_present() -> None:
    result = analyze_headers({"From": "sender@example.com"})

    assert all(
        authentication.state is AuthenticationState.NOT_PRESENT
        for authentication in result.authentication.values()
    )
    assert result.headers_present["Authentication-Results"] is False


def test_unrecognized_authentication_outcome_is_unknown() -> None:
    result = analyze_headers(
        {
            "From": "sender@example.com",
            "Authentication-Results": "mx.example; spf=neutral",
        }
    )

    assert result.authentication["SPF"].state is AuthenticationState.UNKNOWN


def test_conflicting_authentication_outcomes_are_reported() -> None:
    result = analyze_headers(
        {
            "From": "sender@example.com",
            "Authentication-Results": (
                "mx.example; spf=pass; Authentication-Results: other; spf=fail"
            ),
        }
    )

    assert result.authentication["SPF"].state is AuthenticationState.UNKNOWN
    assert any(finding.code == "spf_result_conflict" for finding in result.findings)


def test_reply_to_mismatch_is_reported() -> None:
    result = analyze_headers(
        {
            "From": "sender@example.com",
            "Reply-To": "different@example.net",
        }
    )

    mismatch = next(finding for finding in result.findings if finding.code == "reply_to_mismatch")
    assert mismatch.severity == "medium"
    assert mismatch.details == {
        "from": ["sender@example.com"],
        "reply_to": ["different@example.net"],
    }


def test_raw_header_records_are_supported_and_identity_mismatch_is_reported() -> None:
    result = analyze_headers(
        [
            {"name": "From", "value": "sender@example.com"},
            {
                "name": "Authentication-Results",
                "value": "mx.example; spf=pass smtp.mailfrom=other.example",
            },
        ]
    )

    assert result.authentication["SPF"].state is AuthenticationState.PASS
    assert any(
        finding.code == "authentication_identity_mismatch" for finding in result.findings
    )
