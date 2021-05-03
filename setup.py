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
        "aiohttp==3.7.4.post0",
        "amio @ https://api.github.com/repos/smiszym/amio/tarball/d0603eb1de379b6bd8dbe1089bce0aef86f7cc2f",
        "jsonpatch==1.32",
        "mido==1.2.9",
        "netifaces==0.10.9",
        "psutil==5.8.0",
        "pygit2==1.5.0",
        "python-rtmidi==1.4.7",
        "python-socketio==4.6.1",
        "qrcode==6.1",
        "SoundFile==0.10.3.post1",
        "toml==0.10.2",
    ],
)
