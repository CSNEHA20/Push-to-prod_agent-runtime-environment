from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))

readme_path = os.path.join(here, "README.md")
long_description = ""
if os.path.exists(readme_path):
    with open(readme_path, encoding="utf-8") as f:
        long_description = f.read()

setup(
    name="arc-sdk",
    version="0.1.0",
    description="Agent Runtime Core (ARC) Python SDK for Claude AI Agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="ARC Team",
    packages=find_packages(),
    install_requires=[
        "anthropic>=0.19.0",
        "httpx>=0.27.0",
        "nest-asyncio>=1.6.0",
    ],
    entry_points={
        "console_scripts": [
            "arc=arc.cli:main",
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
