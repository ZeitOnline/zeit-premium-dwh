#!/usr/bin/env python

from setuptools import setup

setup(
    name='zeit-premium-dwh',
    version='0.5.2',
    description='Twisted app for relaying Premium data to CRM',
    license='BSD',
    author='Stefan Freudenberg',
    author_email='stefan@agaric.com',
    packages=[
        'zeit_premium_dwh'
    ],
    package_data={
        'zeit_premium_dwh': ['zeit_premium_dwh.tac']
    },
    include_package_data=True,
    install_requires=[
        'lxml>=2.3',
        'pika>=0.10',
        'twisted>=12.0',
    ],
    extras_require = {
        'testing': [
            'pytest'
        ]
    }
)
