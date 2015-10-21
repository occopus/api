#!/usr/bin/env -e python

import setuptools
from pip.req import parse_requirements

setuptools.setup(
    name='OCCO-API',
    version='0.1.0',
    author='Adam Visegradi',
    author_email='adam.visegradi@sztaki.mta.hu',
    namespace_packages=[
        'occo',
    ],
    packages=[
        'occo.api',
    ],
    scripts=[
        'bin/occo-infra-start',
        'bin/occo-infra-stop',
        'bin/occo-manager-service',
        'bin/occo-get-ibkeys',
        'bin/redisload',
    ],
    url='http://www.lpds.sztaki.hu/',
    license='LICENSE.txt',
    description='OCCO API',
    long_description=open('README.txt').read(),
    install_requires=[
        'Flask',
        'PyYAML',
        'OCCO-Compiler',
        'OCCO-Enactor',
        'OCCO-InfoBroker',
        'OCCO-InfraProcessor',
        'OCCO-Util',
    ]
)
