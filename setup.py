#!/usr/bin/env python3
"""
Setup script for gerrit_ai_review package. TODO
"""

from setuptools import setup, find_packages

setup(
    name="gerrit_ai_review",
    version="0.1.0",
    description="A tool for AI-assisted code review of Gerrit patches",
    author="Marc-André Vef",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "aider",
        "requests",
        "pyyaml",
    ],
    entry_points={
        "console_scripts": [
            "gerrit-review=gerrit_review_patch:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Quality Assurance",
    ],
)
