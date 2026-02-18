Publishing and Platform Integration
===================================

Read the Docs
-------------

- Keep documentation in ``docs/`` with Sphinx.
- Use ``docs/requirements.txt`` for build dependencies.
- Set build command to run Sphinx HTML build.

GitHub Pages
------------

- Build ``docs/_build/html`` in CI.
- Publish artifact to Pages branch or GitHub Pages deployment action.

PyPI
----

- Add a documentation URL in ``[project.urls]`` in ``pyproject.toml``.
- Keep ``README.md`` concise and link to full hosted docs.

Versioning strategy
-------------------

- Publish docs per tag/release to keep behavior aligned with installed versions.
- Keep a ``latest`` channel for main branch and a ``stable`` channel for most recent release.

API compatibility for external tooling
--------------------------------------

This docs set is plain Sphinx/reStructuredText and does not depend on proprietary tooling, so it can be:

- hosted directly,
- embedded as part of a monorepo docs site,
- or consumed by standard Python doc pipelines.
