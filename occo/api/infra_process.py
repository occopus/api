#!/usr/bin/env python

# Copyright (C) 2015 MTA SZTAKI

"""
This is an infra process for OCCO API.

Author: novak.adam@sztaki.mta.hu 
"""

import logging
log=logging.getLogger('occo')

def submit_infrastructure(infra_desc, uds, info_broker, cloudhandler,
                          servicecomposer, infra_protocol):

    from occo.compiler import StaticDescription
    from occo.enactor import Enactor
    from occo.infraprocessor import InfraProcessor

    compiled_infrastructure = StaticDescription(infra_description)
    uds.add_infrastructure(compiled_infrastructure)

    infraprocessor = InfraProcessor.instantiate(infra_protocol, uds, 
                                                cloudhandler, servicecomposer)
    enactor = Enactor(compiled_infrastructure.infra_id, info_broker,
                      infraprocessor)
    return compiled_infrastructure.infra_id, infraprocessor, enactor

def run_infrastructure(infra_desc, uds, info_broker, cloudhandler, 
                       servicecomposer, infra_protocol='basic'):
    infraid, ip, enactor = submit_infrastructure(infra_desc, uds, info_broker,
                                                 cloudhandler, servicecomposer,
                                                 infra_protocol)

    log.info('Submitted infrastructure: %r', infraid)

    try:
        while True:
            enactor.make_a_pass()
    except KeyboardInterrupt:
        log.info('Ctrl+C - exiting.')
    except:
        log.exception('Unexpected error:')
        exit(1)

        

