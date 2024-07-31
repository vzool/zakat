from setuptools import find_packages, setup

setup(
    name='zakat',
    version='0.2.87',
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
        'camelx',
    ],
)