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


def get_version(config, params, *args, **kwargs):
    # Use a version-less endpoint for Docker's /version
    return invoke_rest_endpoint(config, '/version', 'GET', use_api_version=False)


def get_info(config, params, *args, **kwargs):
    return invoke_rest_endpoint(config, '/info', 'GET')


def system_df(config, params, *args, **kwargs):
    query_params = {
        'type': SYSTEM_TYPE.get(params.get('type')) if params.get('type') else "",
        'verbose': params.get('verbose')
    }
    return invoke_rest_endpoint(config, '/system/df', 'GET', query_params=query_params)


def system_events(config, params, *args, **kwargs):
    """Get system events snapshot with optional filtering"""
    filters = params.get('filters')
    since = params.get('since')
    until = params.get('until')
    if 'T' in str(until):
        until = convert_timestamp(until)
    if 'T' in str(since):
        since = convert_timestamp(since)
    if filters:
        filters = json.dumps(filters.get('filters'))
    query_params = {
        'filters': filters,
        'since': since,
        'until': until
    }
    response = invoke_rest_endpoint(config, '/events', 'GET', query_params=query_params)
    result = response.get("result", "")
    events = [json.loads(line) for line in result.splitlines() if line.strip()]
    return events


def ping(config, params, *args, **kwargs):
    """Ping the Docker daemon"""
    # Use a version-less endpoint for Docker's /_ping
    return invoke_rest_endpoint(config, '/_ping', 'GET', use_api_version=False)


def auth(config, params, *args, **kwargs):
    """Authenticate with a registry"""
    username = params.get('username')
    password = params.get('password')
    serveraddress = params.get('serveraddress', 'https://index.docker.io/v1/')

    auth_data = {
        'username': username,
        'password': password,
        'serveraddress': serveraddress
    }

    return invoke_rest_endpoint(config, '/auth', 'POST', data=auth_data)
