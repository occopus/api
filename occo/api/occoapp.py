#
# Copyright (C) 2015 MTA SZTAKI
#
"""
Common functions of a generic OCCO app.

Author: Adam Visegradi <adam.visegradi@sztaki.mta.hu>

This module can be used to implement OCCO-based applications in a unified way.
The module provides features for command-line and file based configuration of
an OCCO application, and other generic features.
"""

args = None
"""Arguments parsed by argparse or an :mod:`occo.util.config` class."""

configuration = None
"""Configuration data loaded from the file(s) specified with ``--cfg``."""

infrastructure = None
"""The OCCO infrastructure defined in the configuration."""

def setup(setup_args=None, cfg_path=None):
    import occo.util.config as config

    cfg = config.config(setup_args=setup_args, cfg_path=cfg_path)

    import logging
    import os
    log = logging.getLogger('occo')
    log.info('Starting up; PID = %d', os.getpid())

    # This is shorter than listing all variables with `global`
    modvars = globals()
    modvars['args'] = cfg
    modvars['configuration'] = cfg.configuration
    occo_infra = cfg.configuration['infrastructure']
    modvars['infrastructure'] = occo_infra
    modvars['uds'] = occo_infra['uds']
    modvars['cloudhandler'] = occo_infra['cloudhandler']
    modvars['servicecomposer'] = occo_infra['servicecomposer']

def yaml_file(filepath):
    import occo.util.config
    return occo.util.config.yaml_load_file(filepath)

def killall(infra_id, ip, uds):
    import logging
    log = logging.getLogger('occo.occoapp')
    log.info('Dropping infrastructure %r', infra_id)
    teardown(infra_id, ip)
    uds.remove_infrastructure(infra_id)

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
