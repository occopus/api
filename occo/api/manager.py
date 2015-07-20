#
# Copyright (C) 2014 MTA SZTAKI
#

"""
OCCO Infrastructure Manager

.. moduleauthor:: Adam Novak <adam.novak@sztaki.mta.hu>,
    Adam Visegradi <adam.visegradi@sztaki.mta.hu>

"""

__all__ = ['InfrastructureManager',
           'InfrastructureMaintenanceProcess']

import time, os
from occo.util.parproc import GracefulProcess
from occo.exceptions import\
    InfrastructureIDTakenException, \
    InfrastructureIDNotFoundException
import occo.infraprocessor as ip
from occo.infobroker import main_info_broker
import logging
log = logging.getLogger('occo.manager_service')

class InfrastructureMaintenanceProcess(GracefulProcess):
    """
    A process maintaining a single infrastructure. This process consists of an
    Enactor, and the corresponding Infrastructure Processor. The Enactor is
    instructed to make a pass at given intervals.

    :param str infra_id: The identifier of the already submitted infrastructure.
    :param dict ip_config: Configuration parameters for the Infrastructure
        Processor. Its contents depend on the concrete type of InfraProcessor
        used.
    :param float enactor_interval: The number of seconds to elapse between
        Enactor passes.
    """

    def __init__(self, infra_id, ip_config, enactor_interval=10):
        super(InfrastructureMaintenanceProcess, self).__init__(target=self)
        self.infra_id,  self.ip_config = infra_id, ip_config
        self.enactor_interval = enactor_interval

    def __call__(self):
        log.info('Starting maintenance process for %r', self.infra_id)

        from occo.enactor import Enactor
        from occo.infraprocessor.infraprocessor import InfraProcessor

        infraprocessor = InfraProcessor.instantiate(**self.ip_config)
        enactor = Enactor(self.infra_id, infraprocessor)
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

class InfrastructureManager(object):
    """
    Manages a set of infrastructures. Each submitted infrastructure is assigned
    an :class:`InfrastructureMaintenanceProcess` that maintains it.

    Compiling + storing the infrastructure is decoupled from starting
    provisioning. This enables the manager to attach to existing, but not
    provisioned infrastructures. I.e., if the manager fails, it can be
    restarted and reattached to previously submitted infrastructures.

    :param user_data_store: A reference to the UDS service.
    :param ip_config: Configuration for the Infrastructure Processor instances.
    """
    def __init__(self, user_data_store, ip_config):
        self.ip_config, self.user_data_store = ip_config, user_data_store
        self.process_table = dict()

    def add(self, infra_desc):
        """
        Compile, store, and start provisioning the given infrastructure. A
        simple composition of :meth:`submit_infrastructure` and
        :meth:`start_provisioning`.

        :param infra_desc: An :ref:`infrastructure description
            <infradescription>`.
        """
        infra_id = self.submit_infrastructure(infra_desc)
        self.start_provisioning(infra_id)
        return infra_id

    def submit_infrastructure(self, infra_desc):
        """
        Compile the given infrastructure and stores it in the UDS.

        :param infra_desc: An :ref:`infrastructure description
            <infradescription>`.
        """

        from occo.compiler import StaticDescription

        compiled_infrastructure = StaticDescription(infra_desc)
        self.user_data_store.add_infrastructure(compiled_infrastructure)
        infra_id = compiled_infrastructure.infra_id
        log.info("Submitted infrastructure: %r", infra_id)
        return infra_id
    
    def start_provisioning(self, infra_id):
        """
        Start provisioning the given infrastructure.

        An :class:`InfrastructureMaintenanceProcess` is created for the given
        infrastructure. This process is then stored in a process table so it
        can be managed.

        This method can be used to *attach* the manager to infrastructures
        already started and having a state in the database.

        .. todo:: Add callback possibility for when the first pass has been
            successfully executed (i.e. when the infrastructure is ready).

        :param str infra_id: The identifier of the infrastructure. The
            infrastructure must be already compiled and stored in the UDS.
        :raise InfrastructureIDTakenException: when the infrastructure specified
            is already being managed.
        """
        if infra_id in self.process_table:
            raise InfrastructureIDTakenException(infra_id)

        p = InfrastructureMaintenanceProcess(infra_id, self.ip_config)
        self.process_table[infra_id] = p
        log.info('Spawning maintenance process for %r', infra_id)
        p.start()

    def stop_provisioning(self, infra_id, wait_timeout=60):
        """
        Stop provisioning the given infrastructure.

        The managing process of the infrastructure is terminated gracefully, so
        the infrastructure stops being maintained; the manager is *detached*
        from the infrastructure.

        The infrastructure itself will *not* be torn down.

        :param str infra_id: The identifier of the infrastructure.
        :raise InfrastructureIDNotFoundException: if the infrastructure is not
            managed.
        """
        try:
            p = self.process_table.pop(infra_id)
            p.graceful_terminate(wait_timeout)
        except KeyError:
            raise InfrastructureIDNotFoundException(infra_id)

    def get(self, infra_id):
        """
        Get the managing process of the given infrastructure.

        :param str infra_id: The identifier of the infrastructure.
        :raise InfrastructureIDNotFoundException: if the infrastructure is not
            managed.
        """
        try:
            return self.process_table[infra_id]
        except KeyError:
            raise InfrastructureIDNotFoundException(infra_id)

    def tear_down(self, infra_id):
        """
        Tear down an infrastructure.

        This method tears down a running, but unmanaged infrastructure. For
        this purpose, an Infrastructure Processor is created, so this method
        does not rely on the Enactor's ability (non-existent at the time of
        writing) to tear down an infrastructure.

        If the infrastructure is being provisioned (the manager is attached),
        this method will fail, and *not* call :meth:`stop_provisioning`
        implicitly.

        :param str infra_id: The identifier of the infrastructure.
        :raise ValueError: if the infrastructure is being maintained by this
            manager. Call :meth:`stop_provisioning` first, explicitly.
        """

        if infra_id in self.process_table:
            raise ValueError(
                'Cannot tear down an infrastructure while it\'s '
                'being maintained.', infra_id)

        from occo.infraprocessor.infraprocessor import InfraProcessor
        ip = InfraProcessor.instantiate(**self.ip_config)

        """
        from occo.util import flatten

        dynamic_state = main_info_broker.get('infrastructure.state', infra_id)
        nodes = flatten(i.itervalues() for i in dynamic_state.itervalues())

        drop_node_commands = [ip.cri_drop_node(n) for n in nodes]
        ip.push_instructions(drop_node_commands)

        ip.push_instructions(ip.cri_drop_infrastructure(infra_id))
        """
        
        import occo.api.occoapp as occoapp
        occoapp.killall(infra_id,ip)


