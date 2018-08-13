#!/usr/bin/env python

import setuptools


setuptools.setup(
    name='musictags',
    version='0.0.1',
    description='stuff done on a whim',
    author='Petre Mierlutiu',
    author_email='petrem@gmail.com',
    url='https://github.com/petrem/musictags',
    license='proprietary/not decided',
    platforms=["any"],
    classifiers=["Development Status :: 2 - Pre-Alpha",
                 "Intended Audience :: End Users/Desktop",
                 "Operating System :: OS Independent",
                 "Programming Language :: Python",
                 "License :: Other/Proprietary License",
                 "Topic :: Personal Music Library"],
    packages=setuptools.find_packages(),
    include_package_data=True,
    requires=['mutagen', 'termcolor'],
    provides=["musictags"],
    scripts=["bin/check-tags"],
)
