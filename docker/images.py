"""
Copyright start
MIT License
Copyright (c) 2026 Fortinet Inc
Copyright end
"""

import json, tarfile
from io import BytesIO
from connectors.core.connector import get_logger, ConnectorError
from .utils import invoke_rest_endpoint
from .constants import *

logger = get_logger(LOGGER_NAME)


def list_images(config, params, *args, **kwargs):
    """List Docker images"""
    filters = params.get('filters')
    if filters:
        filters = json.dumps(filters)
    query_params = {
        'all': params.get('all'),
        'digests': params.get('digests'),
        'filters': filters,
        'shared-size': params.get('shared_size'),
        'manifests': params.get('manifests'),
        'identity': params.get('identity')
    }
    return invoke_rest_endpoint(config, '/images/json', 'GET', query_params=query_params)


def pull_image(config, params, *args, **kwargs):
    query_params = {
        'fromImage': params.get('fromImage'),
        'fromSrc': params.get('fromSrc'),
        'repo': params.get('repo'),
        'tag': params.get('tag'),
        'message': params.get('message')
    }
    additional_fields = params.get('additional_fields')
    if additional_fields:
        query_params.update(additional_fields)
    response = invoke_rest_endpoint(config, '/images/create', 'POST', query_params=query_params,
                                    headers={'accept': 'application/json'}, use_registry_auth=True)
    result = response.get("result", "")
    result = [json.loads(line) for line in result.splitlines() if line.strip()]
    return result


def inspect_image(config, params, *args, **kwargs):
    image_id = params.get('name')
    query_params = {'manifests': params.get('manifests')}
    return invoke_rest_endpoint(config, '/images/{0}/json'.format(image_id), 'GET', query_params=query_params)


def remove_image(config, params, *args, **kwargs):
    image_id = params.get('name')
    query_params = {
        'force': params.get('force'),
        'noprune': params.get('noprune')
    }
    return invoke_rest_endpoint(config, '/images/{0}'.format(image_id), 'DELETE', query_params=query_params)


def tag_image(config, params, *args, **kwargs):
    image_id = params.get('name')
    query_params = {
        'repo': params.get('repo'),
        'tag': params.get('tag')
    }
    response = invoke_rest_endpoint(config, '/images/{0}/tag'.format(image_id), 'POST',
                                query_params=query_params)
    if response:
        return "Successfully tagged {0}".format(image_id)


def prune_images(config, params, *args, **kwargs):
    filters = params.get('filters')
    if filters:
        filters = json.dumps(filters)
    query_params = {
        'filters': filters
    }
    return invoke_rest_endpoint(config, '/images/prune', 'POST', query_params=query_params)


def build_image(config, params, *args, **kwargs):
    """
    Build a Docker image using Docker Engine API.

    The Docker build API expects the build context as a TAR archive.
    """

    dockerfile_content = params.get('dockerfile_content')

    if not dockerfile_content:
        raise ConnectorError(
            'Dockerfile content is required'
        )
    # Convert escaped newline characters to actual newlines
    dockerfile_content = dockerfile_content.replace('\\n', '\n')
    image_name = params.get('t')

    if not image_name:
        raise ConnectorError(
            'Image name/tag (t) is required'
        )

    # Create Docker build context TAR in memory
    tar_buffer = BytesIO()

    with tarfile.open(fileobj=tar_buffer, mode='w') as tar:
        dockerfile_bytes = dockerfile_content.encode('utf-8')

        dockerfile_info = tarfile.TarInfo(name='Dockerfile')
        dockerfile_info.size = len(dockerfile_bytes)

        tar.addfile(
            dockerfile_info,
            BytesIO(dockerfile_bytes)
        )

    tar_buffer.seek(0)

    # Docker build API query parameters
    query_params = {
        't': image_name
    }

    if params.get('nocache') is not None:
        query_params['nocache'] = params.get('nocache')

    if params.get('pull') is not None:
        query_params['pull'] = params.get('pull')

    additional_fields = params.get('additional_fields')

    if additional_fields:
        if isinstance(additional_fields, str):
            try:
                additional_fields = json.loads(additional_fields)
            except ValueError:
                raise ConnectorError(
                    'additional_fields must be valid JSON'
                )

        query_params.update(additional_fields)

    # Build arguments
    buildargs = params.get('buildargs')
    if buildargs:
        if isinstance(buildargs, str):
            try:
                buildargs = json.loads(buildargs)
            except ValueError:
                raise ConnectorError(
                    'buildargs must be valid JSON'
                )

        query_params['buildargs'] = json.dumps(buildargs)

    labels = params.get('labels')
    if labels:
        if isinstance(labels, str):
            try:
                labels = json.loads(labels)
            except ValueError:
                raise ConnectorError(
                    'labels must be valid JSON'
                )

        query_params['labels'] = json.dumps(labels)

    if params.get('networkmode'):
        query_params['networkmode'] = params.get('networkmode')

    if params.get('platform'):
        query_params['platform'] = params.get('platform')

    headers = {
        'Content-Type': 'application/x-tar',
        'Accept': 'application/json'
    }

    return invoke_rest_endpoint(
        config=config,
        endpoint='/build',
        method='POST',
        query_params=query_params,
        data=tar_buffer.getvalue(),
        headers=headers,
        use_api_version=True,
        raw_data=True,
        timeout=300
    )


def search_images(config, params, *args, **kwargs):
    filters = params.get('filters')
    if filters:
        filters = json.dumps(filters)
    query_params = {
        'filters': filters,
        'term': params.get('term'),
        'limit': params.get('limit')
    }
    return invoke_rest_endpoint(config, '/images/search', 'GET', query_params=query_params)


def image_history(config, params, *args, **kwargs):
    image_id = params.get('id')
    query_params = {
        'platform': params.get('platform')
    }
    return invoke_rest_endpoint(config, '/images/{0}/history'.format(image_id), 'GET', query_params=query_params)


def push_image(config, params, *args, **kwargs):
    """Push an image to a registry"""
    image_name = params.get('name')
    query_params = {
        'tag': params.get('tag'),
        'platform': params.get('platform')
    }
    # Docker push via POST /images/{name}/push
    return invoke_rest_endpoint(config, '/images/{0}/push'.format(image_name), 'POST',
                                headers={'accept': 'application/json'}, use_registry_auth=True,
                                query_params=query_params)