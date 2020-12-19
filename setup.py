from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'requirements.txt')) as f:
    required = f.read().splitlines()

with open(path.join(here, 'readme.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="kirby_transform",
    version="0.1.0",
    description="Transformation middleware for Project Kirby",
    long_description_content_type="text/markdown",
    long_description=long_description,
    url="https://github.com/SrzStephen/Kirby-Transform",
    author="Stephen Mott",
    classifiers=["Development Status :: 3 - Alpha",
                 "Intended Audience :: Developers",
                 "Topic :: Software Development :: Libraries",
                 "Programming Language :: Python :: 3.7"],
    package_dir={'': 'src'},
    install_requires=required,
    packages=find_packages(where='src'),
    python_requires=">=3.5",
    platforms="linux",
    entry_points={'console_scripts': [
    ]}
)
