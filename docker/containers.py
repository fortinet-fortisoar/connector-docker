"""
Copyright start
MIT License
Copyright (c) 2026 Fortinet Inc
Copyright end
"""

import json, os
import base64
from integrations.crudhub import make_request
from os.path import join
from connectors.core.connector import get_logger, ConnectorError
from .utils import invoke_rest_endpoint, invoke_binary_endpoint
from .constants import *
from connectors.cyops_utilities.builtins import upload_file_to_cyops
from connectors.cyops_utilities.builtins import download_file_from_cyops
from django.conf import settings

logger = get_logger(LOGGER_NAME)


def list_containers(config, params, *args, **kwargs):
    """List Docker containers"""
    filters = params.get('filters')
    if filters:
        filters = json.dumps(filters)
    query_params = {
        "filters": filters,
        "all": params.get('all'),
        "limit": params.get('limit'),
        "size": params.get('size')
    }
    return invoke_rest_endpoint(config, '/containers/json', 'GET', query_params=query_params)


def inspect_container(config, params, *args, **kwargs):
    container_id = params.get('id')
    query_params = {
        "size": params.get('size')
    }
    return invoke_rest_endpoint(config, '/containers/{0}/json'.format(container_id), 'GET', query_params=query_params)


def start_container(config, params, *args, **kwargs):
    container_id = params.get('id')
    query_params = {
        "detachKeys": params.get('detachKeys')
    }
    response = invoke_rest_endpoint(config, '/containers/{0}/start'.format(container_id), 'POST', query_params=query_params)
    if response:
        return "Successfully started container {0}".format(container_id)


def stop_container(config, params, *args, **kwargs):
    container_id = params.get('id')
    query_params = {
        "signal": params.get('signal'),
        "t": params.get('t')
    }
    response = invoke_rest_endpoint(config, '/containers/{0}/stop'.format(container_id), 'POST',
                                query_params=query_params)
    if response:
        return "Successfully stopped container {0}".format(container_id)


def remove_container(config, params, *args, **kwargs):
    container_id = params.get('id')
    query_params = {
        "force": params.get('force'),
        "signal": params.get('signal'),
        "t": params.get('t')
    }
    response = invoke_rest_endpoint(config, '/containers/{0}'.format(container_id), 'DELETE',
                                query_params=query_params)
    if response:
        return "Successfully removed container {0}".format(container_id)


def create_container(config, params, *args, **kwargs):
    name = params.get('name')
    cmd = params.get('Cmd')
    query_params = {
        "name": name,
        "platform": params.get('platform') if params.get('platform') else ""
    }
    body = {
        "Image": params.get('image'),
        "Cmd": cmd if isinstance(cmd, list) else [cmd],
        "Hostname": params.get('Hostname'),
        "Domainname": params.get('domain_name')
    }
    additional_fields = params.get('additional_fields')
    if additional_fields:
        body.update(additional_fields)
    return invoke_rest_endpoint(config, '/containers/create', 'POST', data=body, query_params=query_params)


def restart_container(config, params, *args, **kwargs):
    container_id = params.get('id')
    query_params = {
        "signal": params.get('signal'),
        "t": params.get('t')
    }
    response = invoke_rest_endpoint(config, '/containers/{0}/restart'.format(container_id), 'POST',
                                query_params=query_params)
    if response:
        return "Successfully restarted container {0}".format(container_id)


def kill_container(config, params, *args, **kwargs):
    container_id = params.get('id')
    query_params = {
        "signal": params.get('signal')
    }
    response = invoke_rest_endpoint(config, '/containers/{0}/kill'.format(container_id), 'POST', query_params=query_params)
    if response:
        return "Successfully killed container {0}".format(container_id)


def container_logs(config, params, *args, **kwargs):
    """Fetch container logs"""
    container_id = params.get('id')
    since = params.get('since', 0)
    until = params.get('until', 0)
    if 'T' in str(since):
        since = convert_timestamp(since)
    if 'T' in str(until):
        until = convert_timestamp(until)
    query_params = {
        "stdout": params.get('stdout'),
        "stderr": params.get('stderr'),
        "tail": params.get('tail'),
        "since": since,
        "until": until,
        "timestamps": params.get('timestamps'),
        "follow": params.get('follow')
    }
    return invoke_rest_endpoint(config, '/containers/{0}/logs'.format(container_id), 'GET',
                                headers={'accept': 'text/plain'},
                                query_params=query_params)


def rename_container(config, params, *args, **kwargs):
    container_id = params.get('id')
    name = params.get('name')
    response = invoke_rest_endpoint(config, '/containers/{0}/rename'.format(container_id), 'POST',
                                query_params={'name': name})
    if response:
        return "Successfully renamed container {0}".format(name)


def prune_containers(config, params, *args, **kwargs):
    filters = params.get('filters')
    query_params = {'filters': json.dumps(filters)} if filters else ""
    return invoke_rest_endpoint(config, '/containers/prune', 'POST', query_params=query_params)


def exec_container(config, params, *args, **kwargs):
    """Execute a command in a running container"""
    container_id = params.get('id')
    cmd = params.get('Cmd')
    body = {
        'Cmd': cmd if isinstance(cmd, list) else [cmd],
        'User': params.get('User'),
        'WorkingDir': params.get('WorkingDir'),
        'Privileged': params.get('Privileged'),
        'AttachStdin': params.get('AttachStdin'),
        'AttachStdout': params.get('AttachStdout'),
        'AttachStderr': params.get('AttachStderr')
    }
    additional_fields = params.get('additional_fields')
    if additional_fields:
        body.update(additional_fields)
    # Create exec instance
    exec_create = invoke_rest_endpoint(config, '/containers/{0}/exec'.format(container_id), 'POST', data=body)
    exec_id = exec_create.get('Id')
    if not exec_id:
        raise ConnectorError('Failed to create exec: missing Id')

    # Exec start parameters
    detach = params.get('Detach')
    tty = params.get('Tty')

    # Start exec
    started = invoke_rest_endpoint(config, '/exec/{0}/start'.format(exec_id), 'POST',
                                   data={'Detach': detach, 'Tty': tty})
    return {'exec_id': exec_id, 'output': started}


def pause_container(config, params, *args, **kwargs):
    container_id = params.get('id')
    response = invoke_rest_endpoint(config, '/containers/{0}/pause'.format(container_id), 'POST')
    if response:
        return "Successfully paused container {0}".format(container_id)


def unpause_container(config, params, *args, **kwargs):
    container_id = params.get('id')
    response = invoke_rest_endpoint(config, '/containers/{0}/unpause'.format(container_id), 'POST')
    if response:
        return "Successfully unpaused container {0}".format(container_id)


def container_stats(config, params, *args, **kwargs):
    container_id = params.get('id')
    query_params = {
        "stream": params.get('stream'),
        "one-shot": params.get('oneshot')
    }
    return invoke_rest_endpoint(config, '/containers/{0}/stats'.format(container_id), 'GET',
                                query_params=query_params)


def container_export(config, params, *args, **kwargs):
    container_id = params.get('id')

    if not container_id:
        raise ConnectorError('Container ID is required')

    response = invoke_binary_endpoint(
        config,
        '/containers/{0}/export'.format(container_id),
        'GET',
        headers={
            'Accept': 'application/x-tar'
        }
    )

    if response.get('status_code') != 200:
        raise ConnectorError(
            'Failed to export container: {0}'.format(
                response.get('result') or response
            )
        )

    result = response.get('content')

    if not result:
        raise ConnectorError(
            'Docker returned an empty container export'
        )

    path = os.path.join(
        settings.TMP_FILE_ROOT,
        '{0}.tar'.format(container_id)
    )

    logger.debug(
        'Writing container export to: {0}'.format(path)
    )

    try:
        # invoke_binary_endpoint() returns Base64-encoded data
        if isinstance(result, str):
            result = base64.b64decode(result)

        with open(path, 'wb') as fp:
            fp.write(result)

        logger.debug(
            'Container export written successfully: {0} bytes'.format(
                len(result)
            )
        )

        attach_response = upload_file_to_cyops(
            file_path=path,
            filename='{0}.tar'.format(container_id),
            name='{0}.tar'.format(container_id),
            create_attachment=True
        )

        return attach_response

    finally:
        if os.path.exists(path):
            os.remove(path)


def container_commit(config, params, *args, **kwargs):
    query_params = {
        'container': params.get('id'),
        'repo': params.get('repo'),
        'tag': params.get('tag', 'latest'),
        'comment': params.get('comment'),
        'author': params.get('author'),
        'changes': params.get('changes'),
        'pause': params.get('pause')
    }
    body = {}
    additional_fields = params.get('additional_fields')
    if additional_fields:
        body.update(additional_fields)
    return invoke_rest_endpoint(config, '/commit', 'POST', query_params=query_params, data=body)


def update_container(config, params, *args, **kwargs):
    container_id = params.get('id')
    # Get update parameters
    body = {
        "Memory": params.get('Memory'),
        "CpuShares": params.get('CpuShares'),
        "CpuQuota": params.get('CpuQuota'),
        "CpuPeriod": params.get('CpuPeriod')
    }
    additional_fields = params.get('additional_fields')
    if additional_fields:
        body.update(additional_fields)
    return invoke_rest_endpoint(config, '/containers/{0}/update'.format(container_id), 'POST', data=body)


def wait_container(config, params, *args, **kwargs):
    """Wait for a container to stop and return its exit code"""
    container_id = params.get('id')
    query_params = {
        "condition": CONDITION_TYPE.get(params.get('condition')) if params.get('condition') else "",
    }
    return invoke_rest_endpoint(config, '/containers/{0}/wait'.format(container_id), 'POST', query_params=query_params)


def attach_container(config, params, *args, **kwargs):
    """Attach to a container's stdout/stderr streams"""
    container_id = params.get('id')
    # Get attachment parameters
    query_params = {
        'detachKeys': params.get('detachKeys'),
        'stdin': params.get('stdin'),
        'stdout': params.get('stdout'),
        'stderr': params.get('stderr'),
        'stream': params.get('stream'),
        'logs': params.get('logs'),

    }
    response = invoke_rest_endpoint(config, '/containers/{0}/attach'.format(container_id), 'POST',
                                query_params=query_params,
                                headers={'accept': 'application/vnd.docker.raw-stream'})
    if response:
        return "Successfully attached container {0}".format(container_id)


def resize_container(config, params, *args, **kwargs):
    """Resize a container's TTY"""
    container_id = params.get('id')
    height = params.get('h')
    width = params.get('w')

    query_params = {'h': height, 'w': width}
    response = invoke_rest_endpoint(config, '/containers/{0}/resize'.format(container_id), 'POST',
                                query_params=query_params)
    if response:
        return "Successfully resized container {0}".format(container_id)


def copy_from_container(config, params, *args, **kwargs):
    """Copy files/folders from a container."""

    container_id = params.get('id')
    container_path = params.get('path')

    if not container_id:
        raise ConnectorError('Container ID is required')

    if not container_path:
        raise ConnectorError('Path is required')

    logger.debug(
        'Copying from container: id={0}, path={1}'.format(
            container_id,
            container_path
        )
    )

    response = invoke_binary_endpoint(
        config,
        '/containers/{0}/archive'.format(container_id),
        'GET',
        query_params={
            'path': container_path
        },
        headers={
            'Accept': 'application/x-tar'
        }
    )

    if response.get('status_code') != 200:
        raise ConnectorError(
            'Failed to fetch container archive: {0}'.format(
                response.get('content') or
                response.get('result') or
                response
            )
        )

    result = response.get('content')

    if not result:
        raise ConnectorError(
            'Docker returned an empty archive'
        )

    file_path = os.path.join(
        settings.TMP_FILE_ROOT,
        '{0}.tar'.format(container_id)
    )

    logger.debug(
        'Writing container archive to: {0}'.format(file_path)
    )

    try:
        # Decode only if invoke_binary_endpoint returns Base64 text.
        if isinstance(result, str):
            result = base64.b64decode(result)

        with open(file_path, 'wb') as fp:
            fp.write(result)

        logger.debug(
            'Container archive written successfully: {0} bytes'.format(
                len(result)
            )
        )

        return upload_file_to_cyops(
            file_path=file_path,
            filename='{0}.tar'.format(container_id),
            name='{0}.tar'.format(container_id),
            create_attachment=True
        )

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


def handle_params(params):
    value = str(params.get('value'))
    input_type = params.get('input')
    try:
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        if input_type == 'Attachment ID':
            if not value.startswith('/api/3/attachments/'):
                value = '/api/3/attachments/{0}'.format(value)
            attachment_data = make_request(value, 'GET')
            file_iri = attachment_data['file']['@id']
            file_name = attachment_data['file']['filename']
            logger.info('file id = {0}, file_name = {1}'.format(file_iri, file_name))
            return file_iri
        elif input_type == 'File IRI':
            if value.startswith('/api/3/files/'):
                return value
            else:
                raise ConnectorError('Invalid File IRI {0}'.format(value))
    except Exception as err:
        logger.info('handle_params(): Exception occurred {0}'.format(err))
        raise ConnectorError('Requested resource could not be found with input type "{0}" and value "{1}"'.format
                             (input_type, value.replace('/api/3/attachments/', '')))


def copy_to_container(config, params, *args, **kwargs):
    """Copy files/folders to a container using a TAR archive."""

    container_id = params.get('id')
    container_path = params.get('path')

    if not container_id:
        raise ConnectorError('Container ID is required')

    if not container_path:
        raise ConnectorError('Path is required')

    file_iri = handle_params(params)

    if not file_iri:
        raise ConnectorError('Archive file is required')

    file_info = download_file_from_cyops(file_iri)
    cyops_file_path = file_info.get('cyops_file_path')

    if not cyops_file_path:
        raise ConnectorError(
            'Unable to access the uploaded archive file'
        )

    file_path = os.path.join(
        settings.TMP_FILE_ROOT,
        cyops_file_path
    )

    if not os.path.isfile(file_path):
        raise ConnectorError(
            'Archive file does not exist: {0}'.format(file_path)
        )

    logger.debug(
        'Copying archive to container: id={0}, path={1}'.format(
            container_id,
            container_path
        )
    )

    with open(file_path, 'rb') as attachment:
        archive_bytes = attachment.read()

    if not archive_bytes:
        raise ConnectorError(
            'Uploaded archive file is empty'
        )

    logger.debug(
        'Archive size: {0} bytes'.format(len(archive_bytes))
    )

    response = invoke_binary_endpoint(
        config,
        '/containers/{0}/archive'.format(container_id),
        'PUT',
        body=archive_bytes,
        query_params={
            'path': container_path
        },
        headers={
            'Content-Type': 'application/x-tar'
        },
        expect_json_response=True
    )
    if response:
        return "Successfully uploaded archive to container"
