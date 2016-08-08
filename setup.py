from setuptools import setup

setup(
    name='openag',
    version='0.1',
    py_modules=['openag'],
    install_requires=[
        'click>=6.6',
        'couchdb>=1.0.1',
        'requests>=2.10.0',
        'voluptuous>=0.8.11'
    ],
    extras_require={
        "test": [
            'mock>=2.0.0',
            'httpretty>=0.8.14',
            'nose>=1.3.7'
        ]
    },
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'openag=openag.cli:main'
        ]
    }
)
