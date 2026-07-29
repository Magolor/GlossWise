# Security Policy

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability.

Use GitHub's private vulnerability reporting page:

<https://github.com/Magolor/GlossWise/security/advisories/new>

Include the affected version, a minimal reproduction, the expected impact, and
any suggested mitigation. You should receive an acknowledgment within seven
days. Please allow a reasonable remediation window before public disclosure.

## Supported versions

GlossWise is alpha software. Security fixes are applied to the current `master`
branch until formal releases and a version-support policy are established.

## Scope

GlossWise manages local terminology data and can expose MCP over stdio or HTTP.
The HTTP transport does not add authentication; bind it to loopback unless a
trusted external layer provides authentication and transport security. Never
submit real credentials or sensitive source text in a vulnerability report.
