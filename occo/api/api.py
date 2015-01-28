#
# Copyright (C) 2014 MTA SZTAKI
#
# Configuration primitives for the SZTAKI Cloud Orchestrator
#

from multiprocessing import Process
import os
import occo.infrastructure-processor as ip

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
    def __init__(self, ip_config, skel_config):
	self.ip_config = ip_config
	self.skel_config = skel_config
	self.process_table = dict()
    def add(self, infra_id):
	if infra_id in self.process_table:
	    raise InfrastructureIDTakenException()
	else: 
	    infra_process = ProcessWrapper(self.ip_config, self. skel_config)
	    p = Process(target=infra_process, args=())
	    self.process_table[infra_id] = p
	    p.start()
    def remove(self, infra_id):
	if infra_id in self.process_table:
	    p = self.process_table[infra_id]
	    process_id = p.pid
	    os.signal(SIGINT, process_id)
	    p.join(60)
	    if p.is_alive():
		os.signal(SIGKILL, process_id)
	    del self.process_table[infra_id]
	else:
	    raise InfrastructureIDNotFoundException()
    def get(self, infra_id):
	return self.process_table[infra_id]
    def abort(self, infra_id):
	pass
    def wait_abort(self, infra_id):
	pass