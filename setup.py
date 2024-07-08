from setuptools import find_packages, setup

setup(
    name='zakat',
    packages=find_packages(include=['zakat']),
    version='0.2.62',
    description='A Python Library for Islamic Financial Management.',
    author='Abdelaziz Elrashed Elshaikh Mohamed',
    install_requires=[],
    python_requires=">=3.10",
    setup_requires=['pytest-runner'],
    tests_require=['pytest==8.2.2'],
    test_suite='tests',
)