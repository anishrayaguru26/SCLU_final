"""
SCLU Trading System Setup Configuration
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Read requirements
def read_requirements(filename):
    """Read requirements from file."""
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Development status classifiers
DEVELOPMENT_STATUS = "Development Status :: 4 - Beta"

setup(
    name="sclu",
    version="1.0.0",
    author="Anish Rayaguru",
    author_email="your.email@example.com",
    description="Smart Capital Live Unleashed - Algorithmic Options Trading System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/SCLU",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/SCLU/issues",
        "Documentation": "https://github.com/yourusername/SCLU/blob/main/README.md",
        "Source Code": "https://github.com/yourusername/SCLU",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        DEVELOPMENT_STATUS,
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Software Development :: Libraries :: Python Modules",

        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Natural Language :: English",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements("requirements.txt"),
    extras_require={
        "dev": read_requirements("requirements-dev.txt"),
        "visualization": [
            "matplotlib>=3.5.0",
            "plotly>=5.0.0",
            "seaborn>=0.11.0",
        ],
        "database": [
            "SQLAlchemy>=1.4.0",
            "psycopg2-binary>=2.9.0",
            "alembic>=1.7.0",
        ],
        "advanced": [
            "scipy>=1.7.0",
            "scikit-learn>=1.0.0",
            "ta-lib>=0.4.24",
            "numba>=0.56.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "sclu-backtest=scripts.run_backtest:main",
            "sclu-live=scripts.live_trading:main",
        ],
    },
    include_package_data=True,
    package_data={
        "sclu": [
            "config/*.yaml",
            "config/*.json",
        ],
    },
    keywords=[
        "algorithmic trading",
        "options trading",
        "backtesting",
        "financial markets",
        "quantitative finance",
        "indian stock market",
        "nse",
        "zerodha",
        "kite connect",
        "open interest analysis",
    ],
    zip_safe=False,
)
