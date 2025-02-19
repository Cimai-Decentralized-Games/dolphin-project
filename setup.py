from setuptools import setup, find_namespace_packages

setup(
    name="dolphin",
    version="0.1.0",
    packages=find_namespace_packages(include=["dolphin", "dolphin.*"]),
    package_data={
        'dolphin': [
            'templates/*.py',  # Include all template files
            'templates/__init__.py',
        ],
    },

    entry_points={
        'console_scripts': [
            'dolphin=dolphin.cli:main',
        ],
    },

    include_package_data=True,
    install_requires=[
        'click>=8.0.0',  # CLI framework
        'base58>=2.0.0',  # For Solana address encoding
        'typing_extensions>=4.0.0',  # For Python 3.8 compatibility
        'solana>=0.29.0',  # Solana client
        'anchorpy>=0.17.0',  # Anchor framework Python bindings
        'construct>=2.10.0',  # For binary serialization
        'borsh-construct>=0.1.0',  # Borsh serialization
        'toml>=0.10.0',  # For config files
        'pydantic>=2.0.0',  # For data validation
        'rich>=13.0.0',  # For terminal output
        'aiohttp>=3.8.0',  # For async HTTP requests
        'cryptography>=40.0.0',  # For keypair handling
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "pytest-xdist>=3.3.0",  # For parallel testing
            "pytest-sugar>=0.9.7",  # For better test output
            "pytest-timeout>=2.1.0",  # For test timeouts
            "pytest-mock>=3.11.0",  # For mocking
            "black>=21.0.0",  # Code formatting
            "mypy>=0.900",  # Type checking
            "isort>=5.10.0",  # Import sorting
            "flake8>=6.0.0",  # Linting
            "flake8-docstrings>=1.7.0",  # Docstring linting
            "tox>=3.24.0",  # Test automation
            "build>=0.7.0",  # Package building
            "twine>=3.4.0",  # Package publishing
            "maturin>=1.0.0",  # Rust binary building
            "pre-commit>=3.3.0",  # Git hooks
        ],
        "docs": [
            "mkdocs>=1.4.0",
            "mkdocs-material>=9.1.0",
            "mkdocstrings>=0.22.0",
            "mkdocstrings-python>=1.1.0",
        ]
    },
    python_requires=">=3.8",
    author="Caballo Loko",
    author_email="caballoloko@cimai.biz",
    description="A Python-to-Solana Framework with Game Development Support",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Cimai-Decentralized-Games/dolphin-project",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Rust",
        "Topic :: Software Development :: Compilers",
        "Topic :: Games/Entertainment",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Build Tools",
        "Framework :: Pytest",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    project_urls={
        "Documentation": "https://github.com/Cimai-Decentralized-Games/dolphin-project/docs",
        "Source": "https://github.com/Cimai-Decentralized-Games/dolphin-project",
        "Tracker": "https://github.com/Cimai-Decentralized-Games/dolphin-project/issues",
    },
)
