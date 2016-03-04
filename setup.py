### Copyright 2014, MTA SZTAKI, www.sztaki.hu
###
### Licensed under the Apache License, Version 2.0 (the "License");
### you may not use this file except in compliance with the License.
### You may obtain a copy of the License at
###
###    http://www.apache.org/licenses/LICENSE-2.0
###
### Unless required by applicable law or agreed to in writing, software
### distributed under the License is distributed on an "AS IS" BASIS,
### WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
### See the License for the specific language governing permissions and
### limitations under the License.
#!/usr/bin/env -e python

import setuptools
from pip.req import parse_requirements

setuptools.setup(
    name='OCCO-API',
    version='0.3.0',
    author='MTA SZTAKI',
    author_email='occopus@lpds.sztaki.hu',
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
        'bin/occo-import-node',
    ],
    url='https://github.com/occopus',
    license='LICENSE.txt',
    description='Occopus API',
    long_description=open('README.txt').read(),
    install_requires=[
        'Flask',
        'PyYAML',
        'PyYAML',
        'Jinja2',
        'OCCO-Util',
        'OCCO-ResourceHandler',
        'OCCO-ConfigManager',
        'OCCO-InfoBroker',
        'OCCO-Enactor',
        'OCCO-Compiler',
        'OCCO-InfraProcessor'
    ]
)
