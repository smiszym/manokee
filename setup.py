#!/usr/bin/env python3

from setuptools import setup

import codecs
import os.path


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), "r") as fp:
        return fp.read()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


setup(
    name="manokee",
    version=get_version("manokee/__init__.py"),
    author="Michał Szymański",
    author_email="smiszym@gmail.com",
    description="""Audio recording software with a mobile-first web interface""",
    license="MIT",
    url="https://github.com/smiszym/manokee",
    packages=["manokee"],
    requires=[
        "mypy",
    ],
    install_requires=[
        "amio @ https://api.github.com/repos/smiszym/amio/tarball/5cd4bc4415ccae430508a2bbe6905fa86bebe51a",
        "eventlet",
        "Flask",
        "Flask-SocketIO",
        "mido",
        "netifaces",
        "python-rtmidi",
        "soundfile",
    ],
)
