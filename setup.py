"""Python Library For Interacting with Chase Paymentech
"""
from setuptools import setup, find_packages
from codecs import open
from os import path
import sys

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup_requires = []

if 'test' in sys.argv:
    setup_requires.append('pytest-runner')

install_requires = [
    'requests>=2.0',
]

tests_require = [
    'pytest',
    'responses',
    'coverage >= 3.7.1, < 5.0.0',
    'pytest-cov',
]

setup(
    name='chase',
    version='1.0.0',
    description='Python Library For Chase Paymentech',
    long_description=long_description,
    url='https://github.com/dave2328/chase',
    author='James Maxwell',
    author_email='james@dxetech.com',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Web APIs',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    packages=find_packages(exclude=['*.tests']),
    keywords='payment',
    install_requires=install_requires,
    tests_require=tests_require,
    setup_requires=setup_requires,
    extras_require={},
    package_data={'chase': ['*.xml']},
)

