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


def list_volumes(config, params, *args, **kwargs):
    filters = params.get('filters')
    query_params = {
        'filters': json.dumps(filters)
    }
    return invoke_rest_endpoint(config, '/volumes', 'GET', query_params=query_params)


def inspect_volume(config, params, *args, **kwargs):
    name = params.get('name')
    return invoke_rest_endpoint(config, '/volumes/{0}'.format(name), 'GET')


def create_volume(config, params, *args, **kwargs):
    body = {
        'Name': params.get('Name'),
        'Driver': params.get('Driver')
    }
    additional_fields = params.get('additional_fields')
    if additional_fields:
        body.update(additional_fields)
    return invoke_rest_endpoint(config, '/volumes/create', 'POST', data=body)


def remove_volume(config, params, *args, **kwargs):
    name = params.get('name')
    query_params = {
        'force': params.get('force')
    }
    response = invoke_rest_endpoint(config, '/volumes/{0}'.format(name), 'DELETE', query_params=query_params)
    if response:
        return "Successfully removed volume {0}".format(name)


def prune_volumes(config, params, *args, **kwargs):
    filters = params.get('filters')
    query_params = {
        'filters': json.dumps(filters)
    }
    return invoke_rest_endpoint(config, '/volumes/prune', 'POST', query_params=query_params)
