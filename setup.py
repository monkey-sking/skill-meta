"""Compatibility for build environments with pre-PEP-621 setuptools."""
from setuptools import setup, find_packages

setup(
    name="skill-meta",
    version="0.1.0",
    description="Discover and load local Agent Skills through CLI or MCP",
    python_requires=">=3.9",
    package_dir={"": "src"},
    packages=find_packages("src"),
    entry_points={"console_scripts": ["skill-meta=skill_meta.cli:main"]},
)
