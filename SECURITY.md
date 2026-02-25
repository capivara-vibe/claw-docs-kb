# Security Policy

## Supported Versions

This project is a single-script utility. Only the latest version on `main` is actively maintained.

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Please report security issues privately via [GitHub's private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability) (Security → Report a vulnerability).

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact

You can expect an acknowledgement within **72 hours** and a resolution or status update within **7 days**.

## Scope

This tool makes outbound HTTP requests to `docs.openclaw.ai` and `raw.githubusercontent.com` only. It does not expose any network services, store credentials, or process user-supplied untrusted input by default.
