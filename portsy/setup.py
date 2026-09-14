#!/usr/bin/env python3
"""
Setup script for Portsy - Port Scanner and Route Analyzer
"""

from setuptools import setup, find_packages
import os

# Read README content
readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
if os.path.exists(readme_path):
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()
else:
    long_description = "Portsy - A highly optimized port scanner and route analyzer for development servers"

setup(
    name="portsy",
    version="1.0.0",
    description="A highly optimized port scanner and route analyzer for development servers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Portsy Team",
    author_email="portsy@example.com",
    url="https://github.com/portsy/portsy",
    py_modules=["portsy"],
    install_requires=[
        "psutil>=5.9.0",
        "requests>=2.28.0",
    ],
    extras_require={
        "gui": ["tkinter"],
    },
    entry_points={
        "console_scripts": [
            "portsy=portsy:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Tools",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.8",
    keywords="port scanner development server route analyzer network tools",
    project_urls={
        "Bug Reports": "https://github.com/portsy/portsy/issues",
        "Source": "https://github.com/portsy/portsy",
    },
)