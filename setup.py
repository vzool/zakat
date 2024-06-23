from setuptools import find_packages, setup

setup(
    name='zakat',
    packages=find_packages(include=['zakat']),
    version='0.1.0',
    description='This module provides the ZakatTracker class for tracking and calculating Zakat.',
    author='Abdelaziz Elrashed Elshaikh Mohamed',
    install_requires=[],
    setup_requires=['pytest-runner'],
    tests_require=['pytest==8.2.2'],
    test_suite='tests',
)