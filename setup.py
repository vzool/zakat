from setuptools import find_packages, setup
from zakat.zakat_tracker import ZakatTracker

setup(
    name='zakat',
    version=ZakatTracker.Version(),
    description='A Python Library for Islamic Financial Management.',
    author='Abdelaziz Elrashed Elshaikh Mohamed',
    author_email='aeemh.sdn@gmail.com',
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires=">=3.10",
    packages=find_packages(
        include=[
            'zakat',
        ],
    ),
    requires=[
    ],
)
