# Security Policy

## Scope

This policy covers the CLAIRE pipeline codebase. It does not cover
Anthropic's API, GitHub Actions infrastructure, Pushover, or Reddit/
HackerNews/dev.to as upstream data sources. Vulnerabilities in those
services should be reported directly to their respective owners.

CLAIRE is a personal automation tool. It has no user accounts, no
web-facing endpoints, and no database. The attack surface is limited
to secrets management, the GitHub Actions workflow, and the ingest
pipeline's handling of untrusted external content.

---

## Reporting a Vulnerability

Use GitHub's private security advisory mechanism:

1. Go to the Security tab of this repository
2. Select "Report a vulnerability"
3. Describe the issue, affected component, and reproduction steps

Do not open a public issue for security vulnerabilities. Response
target is 7 days for acknowledgment.

---

## Known Risks and Mitigations

### ANTHROPIC_API_KEY

The pipeline requires an Anthropic API key with access to Haiku,
Sonnet, and Opus tiers. A leaked or compromised key incurs API
charges and potentially exposes pipeline outputs.

**Mitigations:**
- Store only in GitHub Secrets -- never in code or committed files
- Scope to the minimum required API access if Anthropic adds
  key-level scoping in future
- Rotate immediately if a fork is compromised or a workflow is
  modified by an unauthorized party
- Monitor API usage for unexpected spikes

### GH_PAT (Commit-Back Token)

The workflow uses a fine-grained Personal Access Token to commit
digest outputs back to the repository after each pipeline run. A
compromised PAT with write scope could be used to modify repository
contents, including the workflow file itself.

**Mitigations:**
- Scope the PAT to Contents read+write on this repository only --
  no other repositories, no other permission scopes
- Set the shortest practical expiration on the PAT and rotate on
  schedule
- Review any PRs that modify .github/workflows/ carefully before
  merging -- a modified workflow file runs with the same secrets
  access as the original

### Prompt Injection via Ingest

CLAIRE ingests posts from Reddit, HackerNews, and dev.to and feeds
them into Claude synthesis prompts. A maliciously crafted post could
attempt to influence synthesis output -- for example, by embedding
instruction-like text designed to generate a specific configuration
candidate or override pipeline behavior.

This is a known, accepted risk in the current architecture. The
pipeline does not execute configuration candidates automatically.
Every applied change requires a human-written hypothesis and manual
application. The human review step is the primary mitigation.

**Mitigations:**
- Never wire CLAIRE-A output directly to live configuration --
  human review is required for every applied change by design
- The evidence threshold (3 corroborating posts minimum) limits
  the impact of isolated injection attempts
- Review synthesis output for anomalous or out-of-character
  candidates before applying anything

### claire_session_context.txt

This file contains a snapshot of your live Claude memory
configuration. If committed to a public repository, it exposes
your personal AI configuration state to anyone who views the repo.

**Mitigations:**
- Add `data/claire_session_context.txt` to `.gitignore` before
  pushing to a public repository
- Review `git status` before any push to confirm the file is not
  staged
- The provided `.gitignore` excludes `data/` by default -- verify
  this exclusion is intact if you modify the ignore rules

---

## Dependency Notes

CLAIRE's Python dependencies are minimal: `anthropic`, `requests`,
and `python-dotenv`. Keep `requirements.txt` pinned to reviewed
versions and audit dependency updates before applying.

The workflow uses `actions/checkout@v4` and `actions/setup-python@v5`.
Pin to specific commit SHAs rather than tags in high-trust
environments, as tags are mutable.

---

## What CLAIRE Does Not Do

- It has no web server, API, or publicly accessible endpoint
- It does not store credentials anywhere except `.env` (local) and
  GitHub Secrets (GHA)
- It does not transmit data outside of the Anthropic API,
  GitHub Actions, and Pushover
- CLAIRE-A makes no autonomous changes to any configuration --
  it is shadow-only by design
