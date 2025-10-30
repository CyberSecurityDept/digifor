# setup.py
from setuptools import setup, find_packages

setup(
    name="sdp_crypto",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "cryptography>=41.0.0",
    ],
    python_requires=">=3.7",
)