#!/usr/bin/env python

# Copyright (C) 2015 MTA SZTAKI

"""
Common code used in use-case scripts for OCCO

Author: adam.visegradi@sztaki.mta.hu
"""

import occo.util.config as config

def init():
    def setup_args(cfg):
        cfg.add_argument('node_def')

    return config.config(setup_args=setup_args)
