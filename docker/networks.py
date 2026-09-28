"""
Copyright start
MIT License
Copyright (c) 2026 Fortinet Inc
Copyright end
"""

import json
from connectors.core.connector import get_logger, ConnectorError
from .utils import invoke_rest_endpoint
from .constants import *

logger = get_logger(LOGGER_NAME)


def list_networks(config, params, *args, **kwargs):
    filters = params.get('filters')
    if filters:
        filters = json.dumps(filters)
    query_params = {
        'filters': filters
    }
    return invoke_rest_endpoint(config, '/networks', 'GET', query_params=query_params)


def inspect_network(config, params, *args, **kwargs):
    net_id = params.get('id')
    query_params = {
        'verbose': params.get('verbose'),
        'scope': params.get('scope')
    }
    return invoke_rest_endpoint(config, '/networks/{0}'.format(net_id), 'GET', query_params=query_params)


def create_network(config, params, *args, **kwargs):
    body = {
        'Name': params.get('Name'),
        'Driver': params.get('Driver'),
        'Scope': params.get('Scope'),
        'Internal': params.get('Internal'),
        'Attachable': params.get('Attachable'),
        'Ingress': params.get('Ingress'),
        'EnableIPv4': params.get('EnableIPv4'),
        'EnableIPv6': params.get('EnableIPv6')
    }
    additional_fields = params.get('additional_fields')
    if additional_fields:
        body.update(additional_fields)
    return invoke_rest_endpoint(config, '/networks/create', 'POST', data=body)


def connect_network(config, params, *args, **kwargs):
    net_id = params.get('id')
    body = {
        'Container': params.get('Container'),
    }
    additional_fields = params.get('additional_fields')
    if additional_fields:
        body.update(additional_fields)
    response = invoke_rest_endpoint(config, '/networks/{0}/connect'.format(net_id), 'POST', data=body)
    if response:
        return "Successfully connected to {0}".format(net_id)


def disconnect_network(config, params, *args, **kwargs):
    net_id = params.get('id')
    container = params.get('Container')
    force = params.get('Force', False)
    body = {'Container': container}
    if force:
        body['Force'] = force
    response = invoke_rest_endpoint(config, '/networks/{0}/disconnect'.format(net_id), 'POST', data=body)
    if response:
        return "Successfully disconnected from {0}".format(net_id)


def remove_network(config, params, *args, **kwargs):
    net_id = params.get('id')
    response = invoke_rest_endpoint(config, '/networks/{0}'.format(net_id), 'DELETE')
    if response:
        return "Successfully removed network {0}".format(net_id)


def prune_networks(config, params, *args, **kwargs):
    filters = params.get('filters')
    query_params = {
        'filters': filters
    }
    return invoke_rest_endpoint(config, '/networks/prune', 'POST', query_params=query_params)
