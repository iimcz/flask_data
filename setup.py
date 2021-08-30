from distutils.core import setup
import setuptools

setuptools.setup(
    name='flask_data',
    version='0.1',
    description='A set of helper classes to act as a data middleman between a server/data file and Neos VR (or any other application)',
    author='Ondřej Slabý',
    author_email='slaby@iim.cz',
    packages=setuptools.find_packages(exclude='examples'),
    install_requirements=['flask', 'flask_sock', 'matplotlib', 'numpy']
)
