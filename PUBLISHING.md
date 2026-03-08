# Publishing Guide

This project uses `setuptools-scm` and Git tags for versioning and publishing.

## How versioning works

- No version file is edited manually.
- Package version is derived from the Git tag.
- Tag format:
  - Pre-release (TestPyPI): `vX.Y.ZbN` or `vX.Y.ZrcN`
    - Example: `v1.0.3b1`
  - Stable release (PyPI): `vX.Y.Z`
    - Example: `v1.0.3`

## Workflows

- `publish-testpypi.yml`
  - Trigger: push tag `v*`
  - Runs only for prerelease tags (`a`, `b`, `rc`)
  - Publishes to TestPyPI

- `publish-pypi.yml`
  - Trigger: push tag `v*`
  - Runs only for stable tags (no `a`, `b`, `rc`)
  - Publishes to PyPI

- `build.yml`
  - Shared build workflow used by both publish workflows

## One-time setup

1. Configure PyPI trusted publisher for this repo/workflow/environment.
2. Configure TestPyPI trusted publisher for this repo/workflow/environment.
3. In GitHub repo environments:
   - `testpypi`: set required reviewer(s)
   - `pypi`: set required reviewer(s)

This ensures publishing requires approval before deployment.

## Release commands

### TestPyPI (pre-release)

```bash
git tag v1.0.3b1
git push origin v1.0.3b1
```

### PyPI (stable)

```bash
git tag v1.0.3
git push origin v1.0.3
```

After pushing the tag, approve the environment gate in GitHub Actions when prompted.

## Verify published version

```bash
python -c "from importlib.metadata import version; print(version('drf-commons'))"
```

## Troubleshooting

- `400 Bad Request` about classifier:
  - Ensure classifiers in `pyproject.toml` are valid Trove classifiers.

- Trusted publishing/auth errors:
  - Re-check trusted publisher config on PyPI/TestPyPI.
  - Confirm workflow filename, repo, and environment names match exactly.

- Version collision:
  - If a version already exists on the target index, publish a new tag/version.
