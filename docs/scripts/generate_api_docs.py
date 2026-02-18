"""Generate exhaustive API reference pages for all Python modules."""

from __future__ import annotations

from pathlib import Path


def _iter_modules(package_dir: Path, root_dir: Path) -> list[str]:
    modules: list[str] = []
    for py_file in package_dir.rglob("*.py"):
        if "__pycache__" in py_file.parts:
            continue
        rel = py_file.relative_to(root_dir).with_suffix("")
        parts = list(rel.parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        modules.append(".".join(parts))
    return sorted(set(modules))


def _module_page(module: str) -> str:
    title = module
    underline = "=" * len(title)
    return (
        f"{title}\n"
        f"{underline}\n\n"
        f".. automodule:: {module}\n"
        "   :members:\n"
        "   :undoc-members:\n"
        "   :show-inheritance:\n"
        "   :inherited-members:\n"
    )


def generate_api_docs(package_dir: Path, docs_dir: Path) -> None:
    api_dir = docs_dir / "api"
    generated_dir = api_dir / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    for stale_page in generated_dir.glob("*.rst"):
        stale_page.unlink()

    modules = _iter_modules(package_dir=package_dir, root_dir=package_dir.parent)

    for module in modules:
        out_file = generated_dir / f"{module}.rst"
        out_file.write_text(_module_page(module), encoding="utf-8")

    modules_index = api_dir / "modules.rst"
    lines = [
        "API Module Pages",
        "================",
        "",
        ".. toctree::",
        "   :maxdepth: 1",
        "",
    ]
    lines.extend(f"   generated/{module}" for module in modules)
    lines.append("")

    modules_index.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    generate_api_docs(package_dir=root / "drf_commons", docs_dir=root / "docs")
