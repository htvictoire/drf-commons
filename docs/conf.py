"""Sphinx configuration for drf-commons documentation."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = DOCS_DIR / "scripts"

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(DOCS_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_settings")

try:
    import django

    django.setup()
except Exception:
    # Keep docs importable even when Django dependencies are missing.
    pass

from generate_api_docs import generate_api_docs

generate_api_docs(package_dir=ROOT / "drf_commons", docs_dir=DOCS_DIR)

project = "drf-commons"
author = "Victoire HABAMUNGU"
copyright = "2026, Victoire HABAMUNGU"

try:
    from drf_commons import __version__ as release
except Exception:
    release = "0.0.0"
version = release

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "furo"
html_static_path = ["_static"]
html_title = "drf-commons documentation"

autodoc_member_order = "bysource"
autodoc_typehints = "description"
autosummary_generate = False

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "inherited-members": True,
}

napoleon_google_docstring = True
napoleon_numpy_docstring = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "django": ("https://docs.djangoproject.com/en/stable/", None),
    "drf": ("https://www.django-rest-framework.org/", None),
}
