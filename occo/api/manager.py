### Copyright 2014, MTA SZTAKI, www.sztaki.hu
###
### Licensed under the Apache License, Version 2.0 (the "License");
### you may not use this file except in compliance with the License.
### You may obtain a copy of the License at
###
###    http://www.apache.org/licenses/LICENSE-2.0
###
### Unless required by applicable law or agreed to in writing, software
### distributed under the License is distributed on an "AS IS" BASIS,
### WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
### See the License for the specific language governing permissions and
### limitations under the License.

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
from occo.infobroker import main_uds
import traceback

import logging
log = logging.getLogger('occo.manager_service')
datalog = logging.getLogger('occo.data.manager_service')

class InfrastructureMaintenanceProcess(GracefulProcess):
    """
    A process maintaining a single infrastructure. This process consists of an
    Enactor, and the corresponding Infrastructure Processor. The Enactor is
    instructed to make a pass at given intervals.

    :param str infra_id: The identifier of the already submitted infrastructure.
    :param float enactor_interval: The number of seconds to elapse between
        Enactor passes.
    :param str process_strategy: The identifier of the processing strategy for
        Infrastructure Processor
    """

    def __init__(   self, 
                    infra_id,
                    enactor_interval = 10,
                    process_strategy='sequential'):
        super(InfrastructureMaintenanceProcess, self).__init__(target=self)
        self.infra_id = infra_id
        self.enactor_interval = enactor_interval
        self.process_strategy = process_strategy

    def __call__(self):
        log.info('Starting maintenance process for %s', self.infra_id)

        from occo.enactor import Enactor
        from occo.infraprocessor import InfraProcessor

        infraprocessor = InfraProcessor.instantiate(
                                        protocol='basic',
                                        process_strategy=self.process_strategy)
        enactor = Enactor(self.infra_id, infraprocessor)
        while True:
            try:
                enactor.make_a_pass()
                time.sleep(self.enactor_interval)
            except KeyboardInterrupt:
                log.info('Ctrl+C - exiting.')
                infraprocessor.cancel_pending()
                return 1
            except Exception as ex:
                log.error('Unexpected error:')
                log.debug(traceback.format_exc())
                log.error(str(ex))
                time.sleep(self.enactor_interval)

class InfrastructureManager(object):
    """
    Manages a set of infrastructures. Each submitted infrastructure is assigned
    an :class:`InfrastructureMaintenanceProcess` that maintains it.

    Compiling + storing the infrastructure is decoupled from starting
    provisioning. This enables the manager to attach to existing, but not
    provisioned infrastructures. I.e., if the manager fails, it can be
    restarted and reattached to previously submitted infrastructures.

    :param str process_strategy: The identifier of the processing strategy for
        Infrastructure Processor
    """
    def __init__(self, process_strategy = 'sequential'):
        self.process_strategy = process_strategy
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

    def attach(self, infra_id):
        """
        Start provisioning an existing infrastructure.

        :param str infra_id: The identifier of the infrastructure. The
            infrastructure must be already compiled and stored in the UDS.
        """
        self.start_provisioning(infra_id)
        return infra_id

    def detach(self, infra_id):
        """
        Stop provisioning an existing infrastructure.

        :param str infra_id: The identifier of the infrastructure. The
            infrastructure must be already compiled and stored in the UDS.
        """
        self.stop_provisioning(infra_id)
        return infra_id

    def submit_infrastructure(self, infra_desc):
        """
        Compile the given infrastructure and stores it in the UDS.

        :param infra_desc: An :ref:`infrastructure description
            <infradescription>`.
        """

        from occo.compiler import StaticDescription

        datalog.debug('Adding infrastructure:\n%s', infra_desc)
        compiled_infrastructure = StaticDescription(infra_desc)
        main_uds.add_infrastructure(compiled_infrastructure)
        infra_id = compiled_infrastructure.infra_id
        log.info("Submitted infrastructure: %s", infra_id)
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

        log.debug('Starting provisioning infrastructure %s', infra_id)
        p = InfrastructureMaintenanceProcess(   infra_id = infra_id, 
                                                process_strategy = self.process_strategy)
        self.process_table[infra_id] = p
        log.info('Spawning maintenance process for %s', infra_id)
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
        log.debug('Stopping provisioning infrastructure %s', infra_id)
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

        log.debug('Tearing down infrastructure %s', infra_id)

        from occo.infraprocessor import InfraProcessor
        ip = InfraProcessor.instantiate(protocol='basic',
                                        process_strategy=self.process_strategy)

        import occo.api.occoapp as occoapp
        occoapp.teardown(infra_id, ip)
