from setuptools import setup, find_packages

setup(
    name="arc-sdk",
    version="0.1.0",
    description="Agent Runtime Core (ARC) Python SDK for Claude AI Agents",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="ARC Team",
    packages=find_packages(),
    install_requires=[
        "anthropic>=0.19.0",
        "httpx>=0.27.0",
        "nest-asyncio>=1.6.0",
    ],
    python_requires=">=3.9",
)
