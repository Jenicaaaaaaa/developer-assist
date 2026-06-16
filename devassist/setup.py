from setuptools import setup, find_packages

setup(
    name="devassist-jenica",
    version="0.1.0",
    author="Jenica Kumar",
    description="AI-powered developer CLI tool with codebase-aware RAG",
    long_description=open("README.md").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "typer",
        "rich",
        "chromadb",
        "sentence-transformers",
        "requests",
        "python-dotenv",
        "gitpython",
        "rank-bm25",
    ],
    entry_points={
        "console_scripts": [
            "devassist=devassist.cli:app",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)