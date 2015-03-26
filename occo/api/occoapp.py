#
# Copyright (C) 2015 MTA SZTAKI
#
"""
Common functions of a generic OCCO app.

Author: Adam Visegradi <adam.visegradi@sztaki.mta.hu>
"""

args = None
"""Arguments parsed by argparse or an :mod:`occo.util.config` class."""

configuration = None
"""Configuration data loaded from the file(s) specified with ``--cfg``."""

infrastructure = None
"""The OCCO infrastructure defined in the configuration."""

def setup(setup_args):
    import occo.util.config as config

    cfg = config.config(setup_args=setup_args)

    import logging
    import os
    log = logging.getLogger('occo')
    log.info('Starting up; PID = %d', os.getpid())

    # This is shorter than listing all variables with `global`
    modvars = globals()
    modvars['args'] = cfg
    modvars['configuration'] = cfg.configuration
    modvars['infrastructure'] = cfg.configuration['infrastructure']

def yaml_file(filepath):
    import yaml
    with open(filepath) as f:
        return yaml.load(f)
