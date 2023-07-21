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

    packages=setuptools.find_packages(),
    platforms='any',

    install_requires=[
        'pygame-ce>=2.3.0',
        'glitch-this>=1.0.2',
    ],
)
