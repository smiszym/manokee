#!/usr/bin/env python3

from setuptools import setup

import codecs
import os.path


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()

def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


setup(
    name = 'manokee',
    version = get_version("manokee/__init__.py"),
    author = "Michał Szymański",
    author_email="smiszym@gmail.com",
    description = """Audio recording software with a mobile-first web interface""",
    license="MIT",
    url="https://github.com/smiszym/manokee",
    packages = ["manokee"],
    install_requires = [
        "amio @ https://api.github.com/repos/smiszym/amio/tarball/0c9c34ee222b591abab562881c931e606503c5e2",
        "eventlet",
        "Flask",
        "Flask-SocketIO",
        "mido",
        "netifaces",
        "python-rtmidi",
    ],
)
