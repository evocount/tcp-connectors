"""
Copyright (C) EvoCount GmbH - All Rights Reserved

Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential.
"""


from codecs import open
from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='connectors',
    version='0.1.0',
    description='Connectors for connecting to any TCP service',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/evocount/connectors',
    download_url='https://github.com/evocount/connectors/archive/v0.1.0.tar.gz',
    author='EvoCount GmbH',
    author_email='abhishek.mv1995@gmail.com',
    license='Unlicensed',
    packages=find_packages(),
    install_requires=[
        "gmqtt",
        "aiohttp",
        "cchardet",
        "aiodns",
    ],
    # see: https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',

        'License :: MIT License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],

    python_requires='>=3.6',
)