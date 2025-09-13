from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))

# Get version from __init__.py
def get_version():
    version = {}
    with open(os.path.join(this_directory, "drf_common", "__init__.py")) as f:
        exec(f.read(), version)
    return version.get("__version__", "1.0.0")

setup(
    name="drf-common",
    version=get_version(),
    author="Victoire HABAMUNGU",
    description="Django REST Framework Common Utilities - Modular apps for enhanced DRF functionality",
    long_description="A collection of reusable Django REST Framework utilities that can be used as standalone apps or as a complete package.",
    long_description_content_type="text/plain",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Django>=3.2",
        "djangorestframework>=3.12",
    ],
    extras_require={
        "current_user": [],
        "debug": [],
        "filters": [],
        "pagination": [],
        "response": [],
        "serializers": [],
        "views": [],
        "export": ["openpyxl", "reportlab"],
        "import": ["openpyxl", "pandas"],
        "all": ["openpyxl", "reportlab", "pandas"],
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