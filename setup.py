import os
import sys
from setuptools import setup, find_packages

if sys.version_info < (2,7) or sys.version_info.major > 2:
    sys.exit('Only Python 2.7 is supported')

readme_path = os.path.join(os.path.dirname(__file__), "README.rst")
with open(readme_path) as f:
    readme = f.read()

setup(
    name='openag',
    version='0.1.2',
    author='Open Agriculture Initiative',
    description='Core Python package for the OpenAg software stack',
    long_description=readme,
    license="GPL",
    url="https://github.com/OpenAgInitiative/openag_python",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 2.7",
    ],
    packages=find_packages(exclude=("tests", "tests.*")),
    install_requires=[
        'couchdb>=1.0.1',
        'requests>=2.10.0',
        'voluptuous>=0.8.11',
        'click>=5,<6'
    ],
    extras_require={
        "test": [
            'mock>=2.0.0',
            'httpretty>=0.8.14',
            'nose>=1.3.7',
            'coverage>=4.2'
        ]
    },
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'openag=openag.cli:main'
        ]
    }
)
