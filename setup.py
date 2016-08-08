from setuptools import setup

setup(
    name='openag',
    version='0.1',
    py_modules=['openag'],
    install_requires=[
        'click>=6.6',
        'couchdb-1.0.1',
        'requests>=2.10.0',
        'voluptuous>=0.8.11'
    ],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'openag=openag.cli:main'
        ]
    }
)
