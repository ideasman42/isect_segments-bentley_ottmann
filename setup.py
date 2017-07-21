#!/usr/bin/env python3

from setuptools import setup

setup(
    name='isect_segments-bentley_ottmann',
    version='0.1.0',
    license='MIT',
    description='BentleyOttmann sweep-line implementation',
    author='Campbell Barton',
    author_email='ideasman42@gmail.com',
    url='https://github.com/ideasman42/isect_segments-bentley_ottmann',
    py_modules=['poly_point_isect'],
    zip_safe=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
)
