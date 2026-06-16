from setuptools import setup, find_packages

setup(
    name='devassist',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'typer',
        'rich',
        'chromadb',
        'sentence-transformers',
        'requests',
        'python-dotenv',
        'gitpython',
    ],
    entry_points={
        'console_scripts': [
            'devassist=devassist.cli:app',
        ],
    },
)
