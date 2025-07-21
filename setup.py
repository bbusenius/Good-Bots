#!/usr/bin/env python3
"""Setup script for good-bots package."""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]

setup(
    name="good-bots",
    version="1.0.0",
    author="Bradley Busenius",
    description="Fetch bot IP addresses for django-turnstile-site-protect exclusion lists",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bbusenius/Good-Bots",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "good-bots=good_bots.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "good_bots": ["additional_bots.json"],
    },
    extras_require={
        'test': [
            'pytest>=6.0.0',
            'pytest-cov>=2.8.1',
            'pytest-mock>=3.3.1',
        ],
    }
)
