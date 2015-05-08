#
# Copyright (C) 2014 MTA SZTAKI
#
# Configuration primitives for the SZTAKI Cloud Orchestrator
#

from multiprocessing import Process
import os
import occo.infraprocessor as ip
import occo.infobroker as ib

class InfrastructureIDTakenException(Exception):
    def __init__(self):
        pass

class InfrastructureIDNotFoundException(Exception):
    def __init__(self):
        pass

class ProcessWrapper(object):
    def __init__(self, ip_config, skel_config):
        self.ip_config = ip_config
        self.skel_config = skel_config
    def __call__(self):
        try:
            infra_processor = ip.InfraProcessor(**self.ip_config)
            infra_skeleton = ip.RemoteInfraProcessorSkeleton(backend_ip = infra_processor, **self.skel_config)
            while True:
                infra_skeleton.start_consuming()
        except KeyboardInterrupt:
            log.info("Received interrupt - exiting.")
class ProcessManager(object):
    def __init__(self, ip_config, user_data_store, skel_config):
        from occo.infobroker import main_info_broker
        self.ip_config = ip_config
        self.skel_config = skel_config
        self.process_table = dict()
        self.infobroker = main_info_broker
        self.user_data_store = user_data_store
    def add(self, infra_desc):
        infra_id = submit_infrastructure(infra_desc)
        start_provisioning(infra_id)
    def submit_infrastructure(self, infra_desc):
        from occo.compiler import StaticDescription
        from occo.api.infra_process import run_infrastructure
        compiled_infrastructure = StaticDescription(infra_description)
        user_data_store.add_infrastructure(compiled_infrastructure)
        infra_id = compiled_infrastructure.infra_id
        log.info("Infrastructure submitted with %r infrastructure_id", infra_id)
        return infra_id
    
    def start_provisioning(self, infra_id):
        if not infra_id in self.process_table:
            raise InfrastructureIDNotFoundException()
        p = Process(target=run_infrastructure, args=(infra_id, 
                                                    self.user_data_store,
                                                    self.infobroker,
                                                    self.cloudhandler,
                                                    self.servicecomposer))
        self.process_table[infra_id] = p
        p.start()

    def stop_provisioning(self, infra_id):
        if infra_id in self.process_table:
            p = self.process_table[infra_id]
            process_id = p.pid
            os.signal(SIGINT, process_id)
            try:
                p.join(60)
            except BaseException:
                log.exception('')
            if p.is_alive():
                os.signal(SIGKILL, process_id)
            del self.process_table[infra_id]
        else:
            raise InfrastructureIDNotFoundException()
    def get(self, infra_id):
        return self.process_table[infra_id]
    def tear_down(self, infra_id):
        from occo.infraProcessor import InfraProcessor
        
        dynamic_state = self.infobroker.get('infrastructure.state', infra_id)
        ip = InfraProcessor.instantiate(protocol = 'basic',
                                        user_data_store = self.uds,
                                        cloudhandler = self.cloudhandler,
                                        servicecomposer = self.servicecomposer)
        from occo.util import flatten
        nodes = flatten(i.itervalues() for i in dynamic_state.itervalues())

        drop_node_commands = [ip.cri_drop_node(n) for n in nodes]
        ip.push_instructions(drop_node_commands)

        ip.push_instructions(ip.cri_drop_environment(infra_id))
