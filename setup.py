import sys
import setuptools


long_description = '''
Plat is a platformer game based on a 32x32 grid. Many different types of tiles
occupy these grid spaces and have unique reactions with their environment.
'''

if sys.version_info < (3, 11):
    sys.exit('Python>=3.11 is required.')

setuptools.setup(
    name="plat",
    version="0.5.0",
    url="https://github.com/FirTreeMan/plat",

    description="Simple Platformer",
    long_description=long_description,
    license='Apache License Version 2.0',

    packages=setuptools.find_packages(),
    platforms='any',

    install_requires=[
        'regex>=2018.01.10',
        'numpy<1.17.0',
        'pathlib>=1.0',
        'pyyaml',
        'requests',
        'funcsigs>=1.0.2',
        'sentencepiece>=0.1.8',
        'packaging'
    ],
)