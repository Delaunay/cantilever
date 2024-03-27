#!/usr/bin/env python
from pathlib import Path

from setuptools import setup

with open("cantilever/core/__init__.py") as file:
    for line in file.readlines():
        if "version" in line:
            version = line.split("=")[1].strip().replace('"', "")
            break

extra_requires = {"plugins": ["importlib_resources"]}
extra_requires["all"] = sorted(set(sum(extra_requires.values(), [])))

if __name__ == "__main__":
    setup(
        name="cantilever",
        version=version,
        extras_require=extra_requires,
        description="Python toolbox",
        long_description=(Path(__file__).parent / "README.rst").read_text(),
        author="Setepenre",
        author_email="setepenre@outlook.com",
        license="BSD 3-Clause License",
        url="https://cantilever.readthedocs.io",
        classifiers=[
            "License :: OSI Approved :: BSD License",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Operating System :: OS Independent",
        ],
        packages=[
            "cantilever.core",
            "cantilever.plugins.example",
        ],
        setup_requires=["setuptools"],
        install_requires=["importlib_resources"],
        # deprecated
        # namespace_packages=[
        #     "cantilever",
        #     "cantilever.plugins",
        # ],
        package_data={
            "cantilever.data": [
                "cantilever/data",
            ],
        },
    )
