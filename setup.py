import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="lexupdater",
    version="0.0.1",
    author="Per Erik Solberg",
    author_email="per.solberg@nb.no",
    description="Verktøy for å oppdatere uttaleleksikon for norske dialekter",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/peresolb/lexupdater",
    project_urls={
        "Bug Tracker": "https://github.com/pypa/sampleproject/issues", #TODO Finn ut hva dette er
    },
    classifiers=[       # TODO: FInn ut hva dette betyr
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "lexupdater"},
    packages=setuptools.find_packages(where="lexupdater"),
    python_requires=">=3.6",
)