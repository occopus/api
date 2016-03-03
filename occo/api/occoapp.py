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

"""
Common functions of a generic OCCO app.

Author: Adam Visegradi <adam.visegradi@sztaki.mta.hu>

This module can be used to implement OCCO-based applications in a unified way.
The module provides features for command-line and file based configuration of
an OCCO application, and other generic features.

There are *two* ways to build an OCCO application.

1. The components provided by OCCO can be used as simple librares: they can be
   imported and glued together with specialized code, a script.

2. The other way is to use this module as the core of such an application. This
   module can build an OCCO architecture based on the contents of a YAML config
   file. (Utilizing the highly dynamic nature of YAML compared to other markup
   languages.)

The :func:`setup` function expects a config file either through its
``cfg_path`` parameter, or it will try to get the path from the command line,
or it will try some default paths (see :func:`occo.util.config.config` for
specifics). See the documentation of :func:`setup` for details.

"""

args = None
"""Arguments parsed by argparse or an :mod:`occo.util.config` class."""

configuration = None
"""Configuration data loaded from the file(s) specified with ``--cfg``."""

infrastructure = None
"""The OCCO infrastructure defined in the configuration."""

def setup(setup_args=None, cfg_path=None):
    """
    Build an OCCO application from configuration.

    :param function setup_args: A function that accepts an
        :class:`argparse.ArgumentParser` object. This function can set up the
        argument parser as needed (mainly: add command line arguments).
    :param str cfg_path: Optional. The path of the configuration file. If
        unspecified, other sources will be used (see
        :func:`occo.util.config.config` for details).

    **OCCO Configuration**

    OCCO uses YAML as a configuration language, mainly for its dynamic
    properties, and its human readability. The parsed configuration is a
    dictionary, containing both static parameters and objects already
    instantiated (or executed, sometimes!) by the YAML parser.

    The configuration must contain the following items.

        ``logging``

            The :mod:`logging` configuration dictionary that will be used with
            :func:`logging.config.dictConfig` to setup logging.
        
        ``components``

            The components of the OCCO architecture that's need to be built.

                ``resourcehandler``

                    *The* ``ResourceHandler`` instance (singleton) to be used by
                    other components (e.g. the
                    :class:`~occo.infraprocessor.InfraProcessor`. Multiple
                    backends can be supported by using a basic
                    :class:`occo.resourcehandler.ResourceHandler` instance here
                    configured with multiple backend clouds/resources.

                ``servicecomposer``

                    *The* ``ServiceComposer`` instance (singleton) to be used
                    by other components (e.g. the
                    :class:`~occo.infraprocessor.InfraProcessor`. Multiple
                    backends can be supported by using a basic
                    :class:`occo.resourcehandler.ServiceComposer` instance here
                    configured with multiple backend service composers [#f1]_.

                ``uds``

                    The storage used by this OCCO application.

    .. [#f1] This feature is not yet implemented at the time of writing.

    .. todo:: Change conditionals and scattered error handling in this function
        to preliminary schema-checking (when the schema has been finalized).
    """
    import occo.exceptions as exc
    import occo.util as util
    import occo.util.config as config
    import occo.infobroker as ib
    import logging
    import os

    cfg = config.config(setup_args=setup_args, cfg_path=cfg_path)

    log = logging.getLogger('occo')
    log.info('Starting up; PID = %d', os.getpid())

    # This is shorter and faster than setting all variables through
    # `globals()`, and much shorter than listing all variables as "global"
    modvars = globals()

    modvars['args'] = cfg
    modvars['configuration'] = cfg.configuration
    try:
        occo_infra = cfg.configuration['components']
        modvars['components'] = occo_infra

        ib.real_main_info_broker = occo_infra['infobroker']
        ib.real_main_uds = occo_infra['uds']
        ib.real_main_resourcehandler = occo_infra['resourcehandler']
        ib.real_main_servicecomposer = occo_infra['servicecomposer']

        util.global_dry_run_set(util.coalesce(occo_infra.get('dry_run'), False))

    except KeyError as ex:
        raise exc.MissingConfigurationError(ex.args[0])

def yaml_file(filepath):
    import occo.util.config
    return occo.util.config.yaml_load_file(filepath)

def killall(infra_id, ip):
    import logging
    import occo.infobroker as ib
    log = logging.getLogger('occo.occoapp')
    log.info('Dropping infrastructure %r', infra_id)
    teardown(infra_id, ip)
    ib.main_uds.remove_infrastructure(infra_id)

def teardown(infra_id, ip):
    import logging
    log = logging.getLogger('occo.occoapp')
    datalog = logging.getLogger('occo.data.occoapp')

    log.info('Tearing down infrastructure %r', infra_id)

    from occo.infobroker import main_info_broker
    dynamic_state = main_info_broker.get('infrastructure.state', infra_id)

    from occo.util import flatten
    nodes = list(flatten(i.itervalues() for i in dynamic_state.itervalues()))

    import yaml
    drop_node_commands = [ip.cri_drop_node(n) for n in nodes]
    log.debug('Dropping nodes: %r', [n['node_id'] for n in nodes])
    datalog.debug('DropNode:\n%s',
                  yaml.dump(drop_node_commands, default_flow_style=False))

    ip.push_instructions(drop_node_commands)

    ip.push_instructions(ip.cri_drop_infrastructure(infra_id))
