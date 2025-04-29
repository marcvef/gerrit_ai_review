#!/usr/bin/env python3
"""
Setup script for gerrit_ai_review package.
"""

from setuptools import setup, find_packages

setup(
    name="gerrit_ai_review",
    version="0.1.0",
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
)
