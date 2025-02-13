from setuptools import setup, find_namespace_packages

setup(
    name="dolphin",
    version="0.1.0",
    packages=find_namespace_packages(include=["dolphin", "dolphin.*"]),
    install_requires=[
        "base58>=2.0.0",
        "typing_extensions>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "black>=21.0.0",
            "mypy>=0.900",
        ]
    },
    python_requires=">=3.7",
    author="Caballo Loko",
    author_email="caballoloko@cimai.biz",
    description="A Python-to-Solana Framework",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Cimai-Decentralized-Games/dolphin-project",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Rust",
        "Topic :: Software Development :: Compilers",
    ],
)