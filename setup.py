from setuptools import setup, find_packages
import pathlib


here = pathlib.Path(__file__).parent.resolve()
long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name="lexupdater",
    version="0.0.2",
    author="Språkbanken",
    author_email="sprakbanken@nb.no",
    description="Verktøy for å oppdatere uttaleleksikon for norske dialekter",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/peresolb/lexupdater",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: MIT License",
        "Operating System :: OS Independent",
        "Natural Language :: Norwegian",
    ],
    package_dir={"": "lexupdater"},
    packages=find_packages(where="lexupdater"),
    python_requires=">=3.7",
    install_requires=['schema'],
    extras_require={
        'dev': ['pytest', 'pytest-cov', 'pylint', 'mypy', 'pigar'],
    },
)
