#
# Copyright (C) 2014 MTA SZTAKI
#
# Configuration primitives for the SZTAKI Cloud Orchestrator
#

from multiprocessing import Process
import os

class InfrastructureIDTakenException(Exception):
    def __init__(self, msg = ""):
	self.msg = msg
    def __str__(self):
	return repr(self.msg)

class InfrastructureIDNotFoundException(Exception):
    def __init__(self, msg = ""):
	self.msg = msg
    def __str__(self):
	return repr(self.msg)

class ProcessWrapper(object):
    def __init__(self, ip_config):
	self.ip_config = ip_config
    def __call__(self):
        pass

class ProcessManager(object):
    def __init__(self, ip_config):
	self.ip_config = ip_config
	self.process_table = dict()
    def add(self, infra_id):
	if infra_id in self.process_table:
	    raise InfrastructureIDTakenException("Unable to add infrastructure - ID already in use")
	else: 
	    infra_process = ProcessWrapper(self.ip_config)
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
	    raise InfrastructureIDNotFoundException("Error removing process - no such Infrastructure ID")
    def get(self, infra_id):
	return self.process_table[infra_id]
    def abort(self, infra_id):
	pass
    def wait_abort(self, infra_id):
	pass