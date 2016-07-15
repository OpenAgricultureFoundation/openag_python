from setuptools import setup

setup(
    name='openag_cli',
    version='0.1',
    py_modules=['openag_cli'],
    install_requires=[
        'click>=6.6',
        'Sphinx>=1.4.5',
        'voluptuous>=0.8.11'
    ],
    entry_points={
        'console_scripts': [
            'openag=openag_cli:main'
        ]
    }
)
