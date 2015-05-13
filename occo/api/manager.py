#
# Copyright (C) 2014 MTA SZTAKI
#
# OCCO Infrastructure Manager
#

__all__ = ['InfrastructureIDTakenException',
           'InfrastructureIDNotFoundException',
           'ProcessManager']

import time, os
from occo.util.parproc import GracefulProcess
import occo.infraprocessor as ip
import occo.infobroker as ib

class InfrastructureIDTakenException(Exception): pass
class InfrastructureIDNotFoundException(Exception): pass

class InfrastructureMaintenanceProcess(GracefulProcess):

    def __init__(self, infra_id, ip_config, enactor_interval=10):
        self.infra_id,  self.ip_config = infra_id, ip_config
        self.enactor_interval = enactor_interval

    def __call__(self):
        from occo.enactor import Enactor
        from occo.infraprocessor import InfraProcessor

        infraprocessor = InfraProcessor.instantiate(**self.ip_config)
        enactor = Enactor(infra_id, info_broker, infraprocessor)
        try:
            while True:
                enactor.make_a_pass()
                time.sleep(self.enactor_interval)
        except KeyboardInterrupt:
            log.info('Ctrl+C - exiting.')
            infraprocessor.cancel_pending()
        except:
            log.exception('Unexpected error:')
            exit(1)

class ProcessManager(object):
    def __init__(self, user_data_store, ip_config):
        from occo.infobroker import main_info_broker
        self.ip_config, self.user_data_store = ip_config, user_data_store
        self.process_table = dict()

    def add(self, infra_desc):
        infra_id = self.submit_infrastructure(infra_desc)
        self.start_provisioning(infra_id)

    def submit_infrastructure(self, infra_desc):
        from occo.compiler import StaticDescription

        compiled_infrastructure = StaticDescription(infra_description)
        self.user_data_store.add_infrastructure(compiled_infrastructure)
        infra_id = compiled_infrastructure.infra_id
        log.info("Submitted infrastructure: %r", infra_id)
        return infra_id
    
    def start_provisioning(self, infra_id):
        if infra_id in self.process_table:
            raise InfrastructureIDTakenException(infra_id)

        from occo.api.infra_process import run_infrastructure
        p = InfrastructureMaintenanceProcess(
                infra_id, self.user_data_store, self.ip_config)
        self.process_table[infra_id] = p
        p.start()

    def stop_provisioning(self, infra_id, wait_timeout=60):
        try:
            p = self.process_table.pop(infra_id)
            p.graceful_terminate(wait_timeout)
        except KeyError:
            raise InfrastructureIDNotFoundException()

    def get(self, infra_id):
        return self.process_table[infra_id]

    def tear_down(self, infra_id):
        from occo.infraProcessor import InfraProcessor
        from occo.util import flatten

        dynamic_state = main_info_broker.get('infrastructure.state', infra_id)
        ip = InfraProcessor.instantiate(**self.ip_config)
        nodes = flatten(i.itervalues() for i in dynamic_state.itervalues())

        drop_node_commands = [ip.cri_drop_node(n) for n in nodes]
        ip.push_instructions(drop_node_commands)

        ip.push_instructions(ip.cri_drop_environment(infra_id))
