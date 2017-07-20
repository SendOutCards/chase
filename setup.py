"""Python Library For Interacting with Chase Paymentech
"""
from setuptools import setup, find_packages
import sys

setup_requires = []

if 'test' in sys.argv:
    setup_requires.append('pytest-runner')

install_requires = [
    'requests>=2.0',
    'six',
]

tests_require = [
    'pytest',
    'responses',
    'coverage >= 3.7.1, < 5.0.0',
    'vcrpy',
]

setup(
    name='orbital_gateway',
    version='1.0.3',
    description='Python Library For Chase Paymentech',
    url='https://github.com/SendOutCards/chase',
    author='SendoutCards',
    author_email='colin@sendoutcards.com',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Web APIs',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
    ],
    packages=find_packages(exclude=['*.tests']),
    keywords='payment',
    install_requires=install_requires,
    tests_require=tests_require,
    setup_requires=setup_requires,
    extras_require={},
    package_data={'orbital_gateway': ['templates/*.xml']},
)
