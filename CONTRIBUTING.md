# Contributing to drf-commons

Thank you for your interest in contributing. Please read this guide before
opening issues or pull requests.

---

## Reporting Issues

Before opening an issue:

1. Search existing issues to avoid duplicates.
2. Verify the issue reproduces with the latest release.
3. Provide a minimal, reproducible example.
4. Include: drf-commons version, Python version, Django version, DRF version.

---

## Feature Requests

Feature requests are evaluated based on:

- **General utility** — Is this useful beyond a single specific use case?
- **Composability** — Can it be implemented as a mixin without breaking existing compositions?
- **API consistency** — Does it follow the existing naming and interface conventions?
- **Maintenance burden** — Does it introduce optional dependencies?

---

## Development Setup

```bash
git clone https://github.com/htvictoire/drf-commons
cd drf-commons
python -m venv .venv
source .venv/bin/activate
pip install -e ".[export,import,debug,dev,test,docs]"
```

Run the full check before any commit:

```bash
make quality  # black, isort, flake8, mypy
make test     # pytest
```

---

## Commit Conventions

This project uses [Conventional Commits](https://www.conventionalcommits.org/).

```
<type>(<optional scope>): <short description in imperative mood>

<optional body explaining why, not what>
```

**Allowed types:**

| Type | When to use |
|------|-------------|
| `feat` | New feature or behavior |
| `fix` | Bug fix |
| `test` | Adding or updating tests only |
| `docs` | Documentation only |
| `ci` | CI/CD configuration |
| `chore` | Build scripts, tooling, non-production code |
| `refactor` | Code restructure without behavior change |
| `perf` | Performance improvement |
| `release` | Version bump commit before tagging |

**Rules:**

- One concern per commit. If you need "and" in the message, split it into two commits.
- Keep commits small and focused — a reviewer should be able to understand the
  full change without switching context.
- Use the imperative mood: "add" not "added", "fix" not "fixing".
- No typos in commit messages. Spell-check before committing.
- The commit body should explain *why*, not *what* — the diff already shows what changed.

---

## Test Requirements

- Every new feature must include tests.
- Every bug fix must include a regression test.
- Tests live in the top-level `tests/` directory, mirroring the package structure.
- Run the full suite before opening a PR: `make test`
- Coverage must not drop below 85%: `make coverage`

---

## Pull Request Checklist

Before opening a PR, verify:

- [ ] `make quality` passes (black, isort, flake8, mypy)
- [ ] `make test` passes with no failures
- [ ] `make coverage` shows ≥ 85% total coverage
- [ ] New public API has type annotations
- [ ] `docs/changelog.rst` and `CHANGELOG.md` updated under `Unreleased`
- [ ] Commit messages follow the conventions above
- [ ] Each commit addresses a single concern

---

## Code of Conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/).
All contributors are expected to maintain professional, respectful communication.

---

## License

By contributing, you agree that your contributions will be licensed under the
MIT License, the same license that covers drf-commons.
