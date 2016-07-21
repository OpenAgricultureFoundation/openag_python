from setuptools import setup

setup(
    name='openag',
    version='0.1',
    py_modules=['openag'],
    install_requires=[
        'click>=6.6',
        'Sphinx>=1.4.5',
        'requests>=2.10.0',
        'voluptuous>=0.8.11'
    ],
    entry_points={
        'console_scripts': [
            'openag=openag:main'
        ]
    }
)
