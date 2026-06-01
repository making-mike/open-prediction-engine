# CI Release Gate

Status: implemented as a GitHub Actions workflow.

The CI release gate mirrors the local release check. It does not deploy, publish, push, upload packages, access secrets, or run live network fetches for OPE data.

## Workflow

```text
.github/workflows/release-check.yml
```

The workflow runs on pull requests and pushes to `main`.

It performs:

```bash
python3 --version
python3 -m pip install "ruff>=0.8,<1" "mypy>=1.13,<2"
python3 scripts/release_check.py
python3 -m py_compile scripts/*.py
```

## Local Guard

The workflow is checked by:

```bash
python3 scripts/check_ci_workflow.py
```

That checker verifies the expected release commands, dev-only static analysis installation, read-only repository permissions, Python version setup, and the absence of deployment, publishing, secret, or arbitrary network command snippets.

## Boundary

This is a release-readiness gate for the local fixture-ready repository. It is not a hosted service deployment workflow, and the `ruff`/`mypy` installation is not a runtime dependency.
