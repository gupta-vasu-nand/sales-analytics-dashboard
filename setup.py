"""
Setup script for sales-analytics-dashboard.
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="sales-analytics-dashboard",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A production-ready sales analytics dashboard with comprehensive data pipeline and interactive visualizations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gupta-vasu-nand/sales-analytics-dashboard",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial :: Accounting",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Database"
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "run-pipeline=src.pipeline.run_pipeline:main",
            "run-dashboard=dashboard.app:main",
        ],
    },
)