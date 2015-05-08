#!/usr/bin/env python

# Copyright (C) 2015 MTA SZTAKI

"""
This is an infra process for OCCO API.

Author: novak.adam@sztaki.mta.hu 
"""

import logging
log=logging.getLogger('occo')

def submit_infrastructure(infra_id, uds, info_broker, cloudhandler,
                          servicecomposer, infra_protocol):

    from occo.enactor import Enactor
    from occo.infraprocessor import InfraProcessor

    infraprocessor = InfraProcessor.instantiate(infra_protocol, uds, 
                                                cloudhandler, servicecomposer)
    enactor = Enactor(compiled_infrastructure.infra_id, info_broker,
                      infraprocessor)
    return infraprocessor, enactor

def run_infrastructure(infra_id, uds, info_broker, cloudhandler, 
                       servicecomposer, infra_protocol='basic'):
    ip, enactor = SubmitInfrastructure(infra_id, uds, info_broker,
                                        cloudhandler, servicecomposer,
                                                 infra_protocol)

    log.info('Submitted infrastructure: %r', infra_id)

    try:
        while True:
            enactor.make_a_pass()
    except KeyboardInterrupt:
        log.info('Ctrl+C - exiting.')
    except:
        log.exception('Unexpected error:')
        exit(1)

        

