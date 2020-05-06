#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages
from pkg_resources import parse_requirements

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()


def load_requirements(fname) -> list:
    requirements = []
    with open(fname, "r") as fp:
        for req in parse_requirements(fp.read()):
            name = req.name
            if req.extras:
                name += "[" + ",".join(req.extras) + "]"
            requirements.append(name + str(req.specifier))
        return requirements


setup(
    author="Ivan Sitkin",
    author_email="alvinera@yandex.ru",
    python_requires=">=3.5",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="Wrapper to provide distributed locks with some brokers"
    "(eg aiopg)",
    install_requires=load_requirements("requirements.txt"),
    license="MIT license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="async_lock",
    name="async_lock",
    packages=find_packages(include=["async_lock", "async_lock.*"]),
    extras_require={"develop": load_requirements("requirements.dev.txt"),},
    test_suite="tests",
    url="https://github.com/alviner/async_lock",
    version='0.0.0',
    zip_safe=False,
)
