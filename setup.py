#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

version = "0.0.0"

requirements = [
    "PyYAML==3.13.*",
    "click==6.7",
]

setup(
    name='charmer',
    version=version,
    description=(
        'A command-line utility that  creates scopes and file colours for PyCharm projects'
    ),
    long_description="",
    author='Timofey Danshin',
    author_email='t.danshin@gmail.com',
    url='https://github.com/ibolit/charmer',
    packages=[
        'charmer',
    ],
    package_data={"charmer": ["config/config.yml"]},
    package_dir={'charmer': 'charmer'},
    entry_points={
        'console_scripts': [
            'charmer = charmer.main:main',
        ]
    },
    include_package_data=True,
    python_requires='>=3.4',
    install_requires=requirements,
    license='BSD',
    zip_safe=False,
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development',
    ],
    keywords=(),
)
