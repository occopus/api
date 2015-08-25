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
        'bin/nodestart', 'bin/infrastart',
        'bin/nodestop', 'bin/infrastop',
        'bin/ibclient',
        'bin/listkeys',
        'bin/listnodes',
        'bin/redisload',
        'bin/manager_service',
    ],
    url='http://www.lpds.sztaki.hu/',
    license='LICENSE.txt',
    description='OCCO API',
    long_description=open('README.txt').read(),
    install_requires=[
        'Flask',
        'PyChef',
        'PyYAML',
        'OCCO-Util',
        'OCCO-InfoBroker',
        'OCCO-Compiler',
        'OCCO-Enactor',
        'OCCO-InfraProcessor',
        'OCCO-ServiceComposer',
    ]
)
