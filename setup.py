#!/usr/bin/env python3
"""
Setup script for Whisper Transcriber
"""

from setuptools import setup, find_packages
import os

# Read version from src/__init__.py
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), 'src', '__init__.py')
    if os.path.exists(version_file):
        with open(version_file, 'r') as f:
            for line in f:
                if line.startswith('__version__'):
                    return line.split('=')[1].strip().strip('"\'')
    return "1.0.0"

# Read README.md
def get_long_description():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def get_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="whisper-transcriber",
    version=get_version(),
    author="Marcus Pereira",
    author_email="marcus@example.com",
    description="Real-time audio transcription with Whisper AI and translation",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/marcuspmd/whisper",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    python_requires=">=3.8",
    install_requires=get_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=4.0.0",
            "mypy>=0.991",
            "pre-commit>=2.20.0",
        ],
        "gpu": [
            "torch>=1.13.0",
            "torchaudio>=0.13.0",
        ],
        "web": [
            "waitress>=2.1.0",
            "flask-cors>=4.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "whisper-transcriber=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.txt", "*.md"],
    },
    project_urls={
        "Bug Reports": "https://github.com/marcuspmd/whisper/issues",
        "Source": "https://github.com/marcuspmd/whisper",
        "Documentation": "https://github.com/marcuspmd/whisper/blob/main/README.md",
    },
)
