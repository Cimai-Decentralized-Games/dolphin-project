from setuptools import setup, find_namespace_packages

setup(
    name="dolphin",
    version="0.1.0",
    packages=find_namespace_packages(include=["dolphin", "dolphin.*"]),
    package_data={
        'dolphin': ['js/*', 'templates/*'],
    },

    entry_points={
        'console_scripts': [
            'dolphin=dolphin.cli:main',
        ],
    },

    include_package_data=True,
    install_requires=[
        'click>=8.0.0',
        'py03>=0.3.0',
        'base58>=2.0.0',
        'typing_extensions>=4.0.0',
        'solana>=0.29.0',
        'anchorpy>=0.17.0',
        'construct>=2.10.0',
        'borsh-construct>=0.1.0',
        'toml>=0.10.0',
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-asyncio>=0.18.0",
            "pytest-cov>=3.0.0",
            "black>=21.0.0",
            "mypy>=0.900",
            "tox>=3.24.0",
            "build>=0.7.0",
            "twine>=3.4.0",
            "isort>=5.10.0",
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
    ],
    project_urls={
        "Documentation": "https://github.com/Cimai-Decentralized-Games/dolphin-project/docs",
        "Source": "https://github.com/Cimai-Decentralized-Games/dolphin-project",
        "Tracker": "https://github.com/Cimai-Decentralized-Games/dolphin-project/issues",
    },
)
