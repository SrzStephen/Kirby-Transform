from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'readme.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="kirby_transform",
    version="0.0.5",
    description="Transformation middleware for project Kirby",
    long_description_content_type="text/markdown",
    url="TODO",
    author="Stephen Mott",
    classifiers=["Development Status ::3 - Alpha",
                 "Intended Audience :: Developers",
                 "Topic :: Software Development :: Libraries",
                 "Programming Language :: Python :: 3.7"],
    package_dir={'': 'src'},
    packages = find_packages(where='src'),
    python_requires=">=3.5",
    platforms="linux",
    entry_points={'console_scripts': [
    ]}
)