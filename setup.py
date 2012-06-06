import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "TXMODEM",
    version = "1.0",
    author = "Armin Tamzarian",
    author_email = "tamzarian1989@gmail.com",
    description = ("A Python class implementing the XMODEM and XMODEM-CRC send protocol."),
    long_description = read('README.md'),
    license = "MIT",
    url = "https://github.com/ArminTamzarian/txmodem",
    keywords = "xmodem",
    packages = [
        'txmodem',
    ],
    requires = [
        'serial',
    ],
    classifiers = [
        "Development Status :: 4 - Beta",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
    ],
)