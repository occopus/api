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
This is the REST interface of occo-manager-service tool.

Author: jozsef.kovacs@sztaki.mta.hu
"""

import occo.util as util
import occo.api.occoapp as occoapp
import occo.api.manager as inframanager
import occo.enactor.scaling as scaling

from occo.infobroker import main_info_broker
from occo.infobroker import main_uds
from occo.exceptions import KeyNotFoundError, ArgumentError

import logging 

from flask import Flask, request, jsonify

app = Flask(__name__)

manager = None

log = None

def init(strategy):
    global log, manager
    log = logging.getLogger('occo.manager-service')
    manager = inframanager.InfrastructureManager(
            process_strategy = occoapp.args.strategy)

def keyboardInterrupt():
    log.info('Ctrl+C - Exiting.')
    for i in manager.process_table.iterkeys():
        log.info('Infrastructure left running: %s', str(i))

class RequestException(Exception):
    def __init__(self, status_code, reason, *args):
        super(RequestException, self).__init__(*args)
        self.status_code, self.reason = status_code, reason
    def to_dict(self):
        return dict(status_code=self.status_code,
                    reason=self.reason,
                    message=str(self))

def create_infra_report(infraid):
    infrastate = main_info_broker.get('infrastructure.state', infra_id=infraid)
    result = dict()
    for nodename,instances in infrastate.iteritems():
        nnd = dict()
        instancevals = dict()
        for nodeid,nivalue in instances.iteritems():
            instancevals[nodeid] = dict((item,svalue) for item,svalue in
                    nivalue.iteritems() if item in
                    ['resource_address','state'])
        nnd['instances'] = instancevals
        nnd['scaling'] = scaling.report(infrastate[nodename])
        result[nodename]=nnd
    return result

@app.errorhandler(RequestException)
def handled_exception(error):
    log.error('An exception occured: %r', error)
    #print error.to_dict()
    return jsonify(error.to_dict())

@app.errorhandler(Exception)
def unhandled_exception(error):
    import traceback as tb
    log.error('An unhandled exception occured: %r\n%s',
                error, tb.format_exc(error))
    response = jsonify(dict(message=error.message))
    response.status_code = 500
    return response

def error_if_nodename_does_not_exist(infraid,nodename):
    sd = main_info_broker.get('infrastructure.static_description',
                               infra_id=infraid)
    if not nodename in [ node['name'] for node in sd.nodes ]:
        raise RequestException(300, 
              'ERROR: node \'{0} does not exist in infrastructure \'{1}\'!'.format(
              nodename,infraid))

def error_if_infraid_does_not_exist(infraid):
    if infraid not in util.Infralist().get():
        raise RequestException(300,
              'ERROR: infrastructure \'{0}\' does not exist!'.format(
              infraid))

@app.route('/infrastructures/', methods=['POST'])
def submit_infrastructure():
    """Create a new infrastructure and returns the identifier of the
    infrastructure. The returned identifier can be used as ``infraid`` parameter
    in the infrastructure-related commands.

    Requires an :ref:`infrastructure description <infradescription>` as POST data.

    :return type:
        .. code::

            {
                "infraid": "<infraid_in_uuid_format>"
            }

    Example::
    
        curl -X POST http://127.0.0.1:5000/infrastructures/ --data-binary @my_infrastructure_description.yaml
    """
    log.debug('Serving request %s infrastructures',
                request.method)
    infra_desc = request.stream.read()
    log.info('Submitting infrastructure:\n%s', util.yamldump(infra_desc))
    if not infra_desc:
        raise RequestException(400, 'Empty POST data')
    try:
        infraid = manager.add(infra_desc)
        util.Infralist().add(infraid)
    except Exception as ex:
        log.exception('manager.add:')
        raise RequestException(400, str(ex))
    else:
        return jsonify(dict(infraid=infraid))

@app.route('/infrastructures/<infraid>', methods=['GET'])
def report_infrastructure(infraid):
    """Report the details of an infrastructure.

    :param infraid: The identifier of the infrastructure. 

    :return type:
        .. code::

            {
                "<nodename>": {
                    "instances": {
                        "<nodeid>": {
                            "resource_address": "<ipaddress>",
                            "state": "<state>"
                        }
                    },
                    "scaling": {
                        "actual": <current_number_of_instances>,
                        "max": <maximum_number_of_instances>,
                        "min": <minimum_number_of_instances>,
                        "target": <target_number_of_instances>
                    }
                },
                ...
            }

    """
    error_if_infraid_does_not_exist(infraid)
    log.debug('Serving request %s infrastructures/%s',
                request.method, infraid)
    result = create_infra_report(infraid)
    return jsonify(result)

@app.route('/infrastructures/', methods=['GET'])
def list_infrastructures():
    """List the identifier of infrastructures currently maintained by the service.

    :return type:
        .. code::

            {
                "infrastructures": [
                    "<infraid_in_uuid_format_for_an_infrastructure>",
                    "<infraid_in_uuid_format_for_another_infrastructure>"
                ]
            }

    """
    log.debug('Serving request: %s infrastructures',request.method)
    return jsonify(dict(infrastuctures=util.Infralist().get()))

@app.route('/infrastructures/<infraid>', methods=['DELETE'])
def delete_infrastructure(infraid):
    """Shuts down an infrastructure.

    :param infraid: The identifier of the infrastructure. 

    :return type:
        .. code::

            {
                "infraid": "<infraid>"
            }

    """
    error_if_infraid_does_not_exist(infraid)
    log.debug('Serving request %s infrastructures/%s',
                request.method, infraid)
    if infraid in manager.process_table:
        manager.stop_provisioning(infraid)
    manager.tear_down(infraid)
    util.Infralist().remove(infraid)
    
    return jsonify(dict(infraid=infraid))
    
@app.route('/infrastructures/<infraid>/attach', methods=['POST'])
def attach_infrastructure(infraid):
    """Starts maintaining an existing infrastructure.

    :param infraid: The identifier of the infrastructure. 

    :return type:
        .. code::

            {
                "infraid": "<infraid>"
            }

    """
    error_if_infraid_does_not_exist(infraid)
    if infraid in manager.process_table.keys():
        raise RequestException(300, 
              'ERROR: Infrastructure {0} already being maintained!'.format(
              infraid))
    log.debug('Serving request %s infrastructures/%s',
                request.method, infraid)
    log.info('Start maintenance for infrastructure %s', infraid)
    try:
        infraid = manager.attach(infraid)
    except Exception as ex:
        log.exception('manager.attach:')
        raise RequestException(400, str(ex))
    else:
        return jsonify(dict(infraid=infraid))

    return jsonify(dict(infraid=infraid))

@app.route('/infrastructures/<infraid>/detach', methods=['POST'])
def detach_infrastructure(infraid):
    """Stops maintaining an infrastructure.

    :param infraid: The identifier of the infrastructure. 

    :return type:
        .. code::

            {
                "infraid": "<infraid>"
            }

    """
    error_if_infraid_does_not_exist(infraid)
    if not infraid in manager.process_table.keys():
        raise RequestException(300, 
              'ERROR: Infrastructure {0} is not maintained!'.format(
              infraid))
    log.debug('Serving request %s infrastructures/%s',
                request.method, infraid)
    log.info('Stop maintaining infrastructure %s', infraid)
    try:
        infraid = manager.detach(infraid)
    except Exception as ex:
        log.exception('manager.detach:')
        raise RequestException(400, str(ex))
    else:
        return jsonify(dict(infraid=infraid))

    return jsonify(dict(infraid=infraid))

@app.route('/infrastructures/<infraid>/scaleup/<nodename>', methods=['POST'])
def create_node_nocount(infraid, nodename):
    """Scales up a node in an infrastructure by creating a new instance of the
    node.

    :param infraid: The identifier of the infrastructure.
    :param nodename: The name of the node to be scaled up.

    :return type:
        .. code::

            {
                "count": 1,
                "infraid": "<infraid>",
                "method": "scaleup",
                "nodename": "<nodename>"
            }

    """
    return create_node(infraid, nodename, count = 1)

@app.route('/infrastructures/<infraid>/scaleup/<nodename>/<int:count>', methods=['POST'])
def create_node(infraid, nodename, count = 1):
    """Scales up a node in an infrastructure by creating the specified number of
    instances of the node.

    :param infraid: The identifier of the infrastructure. 
    :param nodename: The name of the node to be scaled up. 
    :param count: The number of instances to be created. 

    :return type:
        .. code::

            {
                "count": <count>,
                "infraid": "<infraid>",
                "method": "scaleup",
                "nodename": "<nodename>"
            }
    """
    error_if_infraid_does_not_exist(infraid)
    error_if_nodename_does_not_exist(infraid,nodename)
    scaling.add_createnode_request(infraid, nodename, count)
    return jsonify(dict(method='scaleup', 
                        infraid=infraid,
                        nodename=nodename,
                        count=count))

@app.route('/infrastructures/<infraid>/scaledown/<nodename>', methods=['POST'])
def drop_node_noselect(infraid, nodename):
    """Scales down a node by destroying one of its instances in the infrastructure. The instance to be
    destroyed is automatically selected by OCCO based on its configured DownScale
    strategy.

    :param infraid: The identifier of the infrastructure.
    :param nodename: The name of the node to be scaled down.

    :return type:
        .. code::

            {
                "infraid": "<infraid>",
                "method": "scaledown",
                "nodeid": null,
                "nodename": "<nodename>"
            }
    """
    return drop_node(infraid, nodename, None)

@app.route('/infrastructures/<infraid>/scaledown/<nodename>/<nodeid>', methods=['POST'])
def drop_node(infraid, nodename, nodeid):
    """Scales down a node in an infrastructure by destroying one of its instances specified.

    :param infraid: The identifier of the infrastructure. 
    :param nodename: The name of the node which is to be scaled down. 
    :param nodeid: The identifier of the selected instance. 

    :return type:
        .. code::

            {
                "infraid": "<infraid>",
                "method": "scaledown",
                "nodeid": "<nodeid>"
                "nodename": "<nodename>"
            }
    """
    error_if_infraid_does_not_exist(infraid)
    error_if_nodename_does_not_exist(infraid,nodename)
    scaling.add_dropnode_request(infraid, nodename, nodeid)
    return jsonify(dict(method='scaledown', 
                        infraid=infraid,
                        nodename=nodename,
                        nodeid=nodeid))

@app.route('/info/<key>', methods=['GET'])
def info(key):
    """Evaluates a key by the info broker and returns the value

    :param key: The name of the key to be evaluated.

    """
    params=dict((k, v) for k, v in request.args.items())
    log.debug('Serving request %s info/%s with params: %s', request.method, key, str(params))
    try:
        return jsonify({"result": main_info_broker.get(key, **params) })
    except ArgumentError as e:
        log.info('InfoRouter: ArgumentError: %s', str(e))
        raise RequestException(400, 'Invalid parameter value for key "{0}"'.format(key), str(e))
    except KeyNotFoundError as e:
        log.info('InfoRouter: KeyNotFound: %s', str(e))
        raise RequestException(404, 'Key not found: "{0}"'.format(key), str(e))
    except Exception as e:
        log.info('InfoRouter: Exception: %s', str(e))
        log.exception('main_info_broker.get:')
        raise RequestException(404, str(e), 'Request cannot be served.')


