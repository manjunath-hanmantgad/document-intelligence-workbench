# Security Policy

## Supported Versions

This project currently supports the latest `main` branch for security fixes.

## Reporting A Vulnerability

1. Do not open public issues for suspected vulnerabilities.
2. Report vulnerabilities privately to the maintainer with:
   - affected component and version/commit
   - reproduction steps
   - impact assessment
   - suggested remediation, if available
3. You will receive acknowledgement and triage status updates.

## Security Baseline

1. No secrets in source control.
2. `.env.example` must contain placeholders only.
3. Reviewer and admin auth paths must be enabled for non-local deployments.
4. Public release artifacts are validated with `scripts/prepare_public_release.py`.

## Disclosure Process

After a fix is prepared and validated, disclosure timing and release notes are coordinated to reduce downstream risk.
