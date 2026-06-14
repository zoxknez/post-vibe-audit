"""
Tests for VAF redaction module.
"""

from vaf.redaction import RedactionReport, has_secrets, redact_content


class TestOpenAIKey:
    def test_redacts_openai_key(self):
        content = 'OPENAI_API_KEY=sk-proj-abc123XYZsecretKey456789longEnough'
        result = redact_content(content)
        assert "sk-proj-abc123" not in result
        assert "REDACTED" in result

    def test_preserves_key_name(self):
        content = 'OPENAI_API_KEY=sk-proj-abc123XYZsecretKey456789longEnough'
        result = redact_content(content)
        assert "OPENAI_API_KEY" in result


class TestGitHubToken:
    def test_redacts_github_pat(self):
        content = "Authorization: ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456"
        result = redact_content(content)
        assert "ghp_aBcD" not in result
        assert "REDACTED" in result


class TestAWSKey:
    def test_redacts_aws_access_key(self):
        content = "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE"
        result = redact_content(content)
        assert "AKIAIOSFODNN7EXAMPLE" not in result
        assert "REDACTED" in result


class TestDatabaseURL:
    def test_redacts_postgres_url(self):
        content = "DATABASE_URL=postgresql://user:s3cr3tP@ss@localhost:5432/mydb"
        result = redact_content(content)
        assert "s3cr3tP@ss" not in result
        assert "REDACTED" in result

    def test_redacts_mongodb_url(self):
        content = 'uri = "mongodb://admin:hunter2@cluster.example.com/prod"'
        result = redact_content(content)
        assert "hunter2" not in result


class TestStripeKey:
    def test_redacts_stripe_live_key(self):
        content = "STRIPE_SECRET_KEY=sk_test_thisIsAMockStripeKeyThatIsLongEnough"
        result = redact_content(content)
        assert "sk_test_thisIsAMockStripeKeyThatIsLongEnough" not in result
        assert "REDACTED" in result


class TestJWT:
    def test_redacts_jwt_in_bearer(self):
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4"
        content = f"Authorization: Bearer {jwt}"
        result = redact_content(content)
        assert jwt not in result

    def test_redacts_raw_jwt(self):
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4"
        result = redact_content(jwt)
        assert jwt not in result


class TestHasSecrets:
    def test_detects_openai_key(self):
        assert has_secrets("sk-proj-abc123XYZsecretKey456789longEnough")

    def test_clean_content_passes(self):
        assert not has_secrets("This is a clean file with no secrets.")

    def test_env_example_with_placeholder(self):
        # Placeholders should not be flagged
        content = "OPENAI_API_KEY=your-key-here"
        # "your-key-here" is low entropy — should not be flagged as secret
        assert not has_secrets(content)


class TestRedactionReport:
    def test_report_never_stores_secret_value(self):
        content = "sk-proj-abc123XYZsecretKey456789longEnough"
        report = RedactionReport()
        redact_content(content, "test.py", report)

        # Report exists
        assert report.total_secrets_found > 0
        assert len(report.findings) > 0

        # Report does NOT contain the secret value
        report_dict = report.as_dict()
        report_str = str(report_dict)
        assert "sk-proj-abc123" not in report_str
        assert "REDACTED" in report_dict["findings"][0]["value"]

    def test_report_records_file_path(self):
        report = RedactionReport()
        redact_content("AKIAIOSFODNN7EXAMPLE", "src/config.ts", report)
        assert report.findings[0].file_path == "src/config.ts"

    def test_report_records_line_number(self):
        content = "line 1\nAKIAIOSFODNN7EXAMPLE\nline 3"
        report = RedactionReport()
        redact_content(content, "test.py", report)
        assert report.findings[0].line_number == 2

    def test_multiple_secrets_counted(self):
        content = (
            "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\n"
            "STRIPE_KEY=sk_test_thisIsAMockStripeKeyThatIsLongEnough\n"
        )
        report = RedactionReport()
        redact_content(content, "test.py", report)
        assert report.total_secrets_found >= 2


class TestNothingLeaks:
    """Paranoid check: redacted output must never contain actual secret values."""

    def test_comprehensive_no_leak(self):
        secrets = [
            "sk-proj-abc123XYZsecretKey456789longEnough",
            "ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456",
            "AKIAIOSFODNN7EXAMPLE",
            "sk_test_thisIsAMockStripeKeyThatIsLongEnough",
        ]
        content = "\n".join(f"KEY={s}" for s in secrets)
        result = redact_content(content)
        for secret in secrets:
            # Only check the secret value part (after =), not the key name
            assert secret not in result, f"Secret leaked: {secret[:10]}..."
