import os

from setuptools import find_packages, setup

this_directory = os.path.abspath(os.path.dirname(__file__))


def get_long_description():
    readme_path = os.path.join(this_directory, "README.md")
    with open(readme_path, encoding="utf-8") as f:
        return f.read()


def get_version():
    version_path = os.path.join(this_directory, ".VERSION")
    with open(version_path, encoding="utf-8") as f:
        return f.read().strip()


setup(
    name="drf-commons",
    version=get_version(),
    author="Victoire HABAMUNGU",
    author_email="contact@htvictoire.me",
    description="Production-grade utilities, base classes, and architectural abstractions for Django REST Framework",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/htvictoire/drf-commons",
    project_urls={
        "Documentation": "https://drf-commons.readthedocs.io/",
        "Source": "https://github.com/htvictoire/drf-commons",
        "Issues": "https://github.com/htvictoire/drf-commons/issues",
        "Changelog": "https://drf-commons.readthedocs.io/en/latest/changelog.html",
    },
    packages=find_packages(include=["drf_commons*"], exclude=["tests*", "venv*", "htmlcov*"]),
    include_package_data=True,
    install_requires=[
        "Django>=3.2",
        "djangorestframework>=3.12",
    ],
    extras_require={
        "export": ["openpyxl>=3.0", "weasyprint>=60.0"],
        "import": ["openpyxl>=3.0", "pandas>=1.3"],
        "debug": ["psutil>=5.9"],
        "dev": ["black==25.1.0", "flake8==7.3.0", "isort==6.0.1", "mypy==1.18.1"],
        "test": ["pytest==8.4.2", "pytest-cov==7.0.0", "pytest-django==4.11.1", "factory-boy>=3.3"],
        "build": ["build>=1.0", "twine>=6.0"],
        "docs": ["sphinx>=8.1", "furo>=2024.8.6", "myst-parser>=3.0"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
        "Framework :: Django :: 5.1",
        "Framework :: Django :: 5.2",
        "Framework :: Django :: 6.0",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Typing :: Typed",
    ],
    keywords=[
        "django",
        "rest-framework",
        "drf",
        "api",
        "utilities",
        "mixins",
        "bulk-operations",
        "serializers",
        "viewsets",
        "audit-trail",
        "soft-delete",
    ],
    python_requires=">=3.8",
    zip_safe=False,
)
