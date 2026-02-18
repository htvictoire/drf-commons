import os

from setuptools import find_packages, setup

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))


# Get version from __init__.py
def get_version():
    version = {}
    with open(os.path.join(this_directory, "drf_commons", "__init__.py")) as f:
        exec(f.read(), version)
    return version.get("__version__", "1.0.1")


setup(
    name="drf-commons",
    version=get_version(),
    author="Victoire HABAMUNGU",
    description="Django REST Framework Common Utilities for production APIs",
    long_description="A collection of reusable Django REST Framework utilities with a single Django app entrypoint.",
    long_description_content_type="text/plain",
    packages=find_packages(),
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
        "docs": ["sphinx>=8.1", "furo>=2024.8.6"],
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
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Framework :: Django :: 4.2",
    ],
    python_requires=">=3.8",
    zip_safe=False,
)
