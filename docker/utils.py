"""
Copyright start
MIT License
Copyright (c) 2026 Fortinet Inc
Copyright end
"""

import requests
import json
import base64
import time
import os
import threading
from connectors.core.connector import get_logger, ConnectorError
from connectors.cyops_utilities.builtins import download_file_from_cyops
from .constants import LOGGER_NAME

logger = get_logger(LOGGER_NAME)

# Rate limiting storage (thread-safe)
_rate_limit_lock = threading.Lock()
_request_times = []


def check_payload(payload):
    updated_payload = {}
    for key, value in payload.items():
        if isinstance(value, dict):
            nested = check_payload(value)
            if len(nested.keys()) > 0:
                updated_payload[key] = nested
        elif value:
            updated_payload[key] = value
    return updated_payload


def _build_auth(config):
    username = config.get('username')
    password = config.get('password')
    token = config.get('access_token')
    headers = {}
    auth = None
    if token:
        headers['Authorization'] = 'Bearer {0}'.format(token)
    elif username and password:
        auth = (username, password)
    return auth, headers


def _build_registry_auth(config):
    """Build Docker registry authentication header"""
    registry_username = config.get('registry_username')
    registry_password = config.get('registry_password')
    registry_server = config.get('registry_server', 'https://index.docker.io/v1/')

    if registry_username and registry_password:
        auth_config = {
            'username': registry_username,
            'password': registry_password,
            'serveraddress': registry_server
        }
        auth_string = base64.b64encode(json.dumps(auth_config).encode()).decode()
        return {'X-Registry-Auth': auth_string}
    return {}


def _build_url(config, endpoint, use_api_version=True):
    try:
        server_address = config.get('server_address')
        port = config.get('port')
        protocol = config.get('protocol')
        api_version = config.get('api_version')

        if not server_address:
            raise ConnectorError('Missing required parameter: server_address')
        server_address = server_address.strip()
        if server_address.startswith('https://'):
            server_address = server_address[len('https://'):]
        elif server_address.startswith('http://'):
            server_address = server_address[len('http://'):]
        server_address = server_address.rstrip('/')
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
        if use_api_version and not endpoint.startswith('/' + api_version):
            endpoint = '/' + api_version + endpoint
        url = '{protocol}://{server_address}:{port}{endpoint}'.format(protocol=protocol.lower(),
                                                                      server_address=server_address,
                                                                      port=port,
                                                                      endpoint=endpoint)
        return url
    except Exception as e:
        logger.error('Error building URL: {0}'.format(str(e)))
        raise ConnectorError('Error building URL: {0}'.format(str(e)))


def _apply_rate_limit(config):
    """Apply rate limiting based on configuration (thread-safe)"""
    rate_limit = config.get('rate_limit', 60)  # requests per minute
    if rate_limit <= 0:
        return

    with _rate_limit_lock:
        current_time = time.time()
        # Remove requests older than 1 minute
        global _request_times
        _request_times = [t for t in _request_times if current_time - t < 60]

        # If we're at the rate limit, wait
        if len(_request_times) >= rate_limit:
            sleep_time = 60 - (current_time - _request_times[0])
            if sleep_time > 0:
                logger.info('Rate limit reached, sleeping for {0:.2f} seconds'.format(sleep_time))
                time.sleep(sleep_time)

        _request_times.append(current_time)


def _get_uploaded_file_path(file_config):
    """Download a FortiSOAR uploaded file and return its local filesystem path."""

    if not file_config:
        logger.error('Uploaded file config is empty')
        return None

    logger.debug(
        'Uploaded file config: {0}'.format(file_config)
    )

    try:
        if isinstance(file_config, dict):
            file_id = file_config.get('@id') or file_config.get('id')
        else:
            file_id = file_config

        logger.debug(
            'Uploaded file ID: {0}'.format(file_id)
        )

        if not file_id:
            logger.error('No file ID found in uploaded file config')
            return None

        file_info = download_file_from_cyops(file_id)

        logger.debug(
            'Downloaded file information: {0}'.format(file_info)
        )

        cyops_file_path = file_info.get('cyops_file_path')

        if not cyops_file_path:
            logger.error(
                'cyops_file_path was not returned for uploaded file'
            )
            return None

        # cyops_file_path returned by FortiSOAR is not an absolute path.
        # The downloaded file is stored under /tmp.
        file_path = os.path.join('/tmp', cyops_file_path)

        logger.debug(
            'Resolved local file path: {0}'.format(file_path)
        )

        if not os.path.isfile(file_path):
            logger.error(
                'Downloaded file does not exist at: {0}'.format(file_path)
            )
            return None

        logger.debug(
            'Downloaded file exists: {0}'.format(file_path)
        )

        return file_path

    except Exception as e:
        logger.exception(
            'Error downloading uploaded file: {0}'.format(str(e))
        )
        raise ConnectorError(
            'Unable to access uploaded certificate file: {0}'.format(str(e))
        )


def _build_ssl_context(config):
    """Build SSL options for Docker Engine mTLS."""

    verify_ssl = config.get('verify_ssl', True)

    cert_path = _get_uploaded_file_path(
        config.get('cert_path')
    )

    key_path = _get_uploaded_file_path(
        config.get('key_path')
    )

    ca_cert_path = _get_uploaded_file_path(
        config.get('ca_cert_path')
    )

    logger.debug(
        'Client certificate path: {0}'.format(cert_path)
    )
    logger.debug(
        'Client key path: {0}'.format(key_path)
    )
    logger.debug(
        'CA certificate path: {0}'.format(ca_cert_path)
    )

    if not cert_path:
        raise ConnectorError(
            'Docker client certificate file was not found'
        )

    if not key_path:
        raise ConnectorError(
            'Docker client private key file was not found'
        )

    if not ca_cert_path:
        raise ConnectorError(
            'Docker CA certificate file was not found'
        )

    cert = (cert_path, key_path)
    verify = ca_cert_path if verify_ssl else False

    return verify, cert


def invoke_rest_endpoint(config, endpoint, method='GET', data=None,
                         headers=None, query_params=None, timeout=None,
                         use_registry_auth=False,
                         use_api_version=True, raw_data=False):
    try:
        # Apply rate limiting
        _apply_rate_limit(config)

        timeout = timeout or config.get('timeout', 60)

        default_headers = {
            'accept': 'application/json'
        }

        if headers is None:
            headers = {}

        # Add registry authentication if needed
        if use_registry_auth:
            registry_headers = _build_registry_auth(config)
            headers.update(registry_headers)

        # Merge headers with precedence to explicit headers
        merged_headers = {
            **default_headers,
            **headers
        }

        # Build SSL context
        verify, cert = _build_ssl_context(config)

        url = _build_url(
            config,
            endpoint,
            use_api_version=use_api_version
        )

    except Exception as e:
        logger.error(
            'Error in invoke_rest_endpoint setup: {0}'.format(str(e))
        )
        raise ConnectorError(
            'Error setting up request: {0}'.format(str(e))
        )

    # Retry logic
    retry_attempts = config.get('retry_attempts', 3)
    retry_delay = config.get('retry_delay', 1)

    if query_params:
        query_params = check_payload(query_params)

    response = None

    logger.debug('Endpoint: {0}'.format(url))
    logger.debug('Method: {0}'.format(method))
    logger.debug('Query Params: {0}'.format(query_params))

    for attempt in range(retry_attempts):
        try:
            payload = None

            if data is not None:

                if raw_data:
                    # Build API / binary request
                    payload = data

                    if 'content-type' not in {
                        k.lower() for k in merged_headers.keys()
                    }:
                        merged_headers['Content-Type'] = \
                            'application/octet-stream'

                else:
                    # Existing JSON API behavior
                    payload = json.dumps(data)

                    if 'content-type' not in {
                        k.lower() for k in merged_headers.keys()
                    }:
                        merged_headers['Content-Type'] = \
                            'application/json'

            logger.debug(
                'Headers: {0}'.format(merged_headers)
            )

            response = requests.request(
                method=method,
                url=url,
                verify=verify,
                cert=cert,
                data=payload,
                params=query_params,
                headers=merged_headers,
                timeout=timeout
            )

            logger.debug(
                'Response Status Code: {0}'.format(
                    response.status_code
                )
            )

            # Don't log potentially large binary responses
            if raw_data:
                logger.debug(
                    'Response Content Length: {0}'.format(
                        len(response.content)
                    )
                )
            else:
                logger.debug(
                    'Response: {0}'.format(response.text)
                )

            # Successful response
            if response.ok:
                break

            # Don't retry 4xx
            if 400 <= response.status_code < 500:
                break

            # Retry 5xx
            if attempt < retry_attempts - 1:
                logger.warning(
                    'Server error {0}, retrying in {1} seconds '
                    '(attempt {2}/{3})'.format(
                        response.status_code,
                        retry_delay,
                        attempt + 1,
                        retry_attempts
                    )
                )

                time.sleep(retry_delay)

        except requests.RequestException as e:
            logger.error(
                'Request failed: {0}'.format(str(e))
            )

            if attempt < retry_attempts - 1:
                time.sleep(retry_delay)
                continue

            raise ConnectorError(
                'Docker API request failed: {0}'.format(str(e))
            )

    # Handle response
    if response is None:
        raise ConnectorError(
            'No response received from Docker API'
        )

    if response.ok:

        if raw_data:
            # Docker /build returns newline-delimited JSON.
            build_output = []

            for line in response.text.splitlines():
                if not line:
                    continue

                try:
                    build_output.append(json.loads(line))
                except ValueError:
                    build_output.append({
                        'stream': line
                    })

            return {
                'status_code': response.status_code,
                'build_output': build_output
            }

        # Existing JSON response handling
        try:
            return response.json()
        except ValueError:
            return {
                'status_code': response.status_code,
                'response': response.text
            }

    # Error handling
    content = response.text

    logger.error(
        'HTTP {0}: {1}'.format(
            response.status_code,
            content
        )
    )

    if response.status_code == 400:
        raise ConnectorError(
            'Bad Request: {0}'.format(content)
        )

    elif response.status_code == 401:
        raise ConnectorError(
            'Unauthorized: {0}'.format(content)
        )

    elif response.status_code == 403:
        raise ConnectorError(
            'Forbidden: {0}'.format(content)
        )

    elif response.status_code == 404:
        raise ConnectorError(
            'Resource not found: {0}'.format(content)
        )

    elif response.status_code == 409:
        raise ConnectorError(
            'Conflict: {0}'.format(content)
        )

    elif response.status_code == 500:
        raise ConnectorError(
            'Docker Engine internal error: {0}'.format(content)
        )

    elif response.status_code == 503:
        raise ConnectorError(
            'Docker Engine unavailable: {0}'.format(content)
        )

    else:
        raise ConnectorError(
            'HTTP {0}: {1}'.format(
                response.status_code,
                content
            )
        )


def invoke_binary_endpoint(config, endpoint, method='GET', body=None, headers=None,
                           query_params=None, timeout=None, use_registry_auth=False,
                           use_api_version=True, expect_json_response=False):
    """
    Invoke a Docker API endpoint that sends or receives binary data (e.g., tar streams).
    - For upload-style endpoints (e.g., copy_to_container, images/load), pass binary bytes in `body`.
    - For download-style endpoints (e.g., container_export, images/get), the response content is
      returned as base64-encoded data in a JSON object.
    """
    try:
        # Apply rate limiting
        _apply_rate_limit(config)

        timeout = timeout or config.get('timeout', 60)
        default_headers = {'accept': 'application/json'}

        if headers is None:
            headers = {}

        # Add registry authentication if needed
        if use_registry_auth:
            registry_headers = _build_registry_auth(config)
            headers.update(registry_headers)

        # Merge headers with precedence to explicit headers
        merged_headers = {**default_headers, **headers}

        # Build SSL context
        verify, cert = _build_ssl_context(config)

        url = _build_url(config, endpoint, use_api_version=use_api_version)
    except Exception as e:
        logger.error('Error in invoke_binary_endpoint setup: {0}'.format(str(e)))
        raise ConnectorError('Error setting up binary request: {0}'.format(str(e)))

    # Retry logic (mirrors invoke_rest_endpoint)
    retry_attempts = config.get('retry_attempts', 3)
    retry_delay = config.get('retry_delay', 1)
    response = None
    if query_params:
        query_params = check_payload(query_params)
    for attempt in range(retry_attempts):
        try:
            payload = None
            if body is not None:
                # Expect bytes/bytearray for binary payload; strings are encoded as UTF-8
                if isinstance(body, (bytes, bytearray)):
                    payload = body
                elif isinstance(body, str):
                    payload = body.encode('utf-8')
                else:
                    # Fallback: JSON-encode dict-like payloads if provided
                    try:
                        payload = json.dumps(body).encode('utf-8')
                        if 'content-type' not in {k.lower() for k in merged_headers.keys()}:
                            merged_headers['Content-Type'] = 'application/json'
                    except Exception:
                        raise ConnectorError('Invalid binary payload type for endpoint {0}'.format(endpoint))

            response = requests.request(method=method, url=url, verify=verify, cert=cert,
                                        data=payload, params=query_params, headers=merged_headers, timeout=timeout)

            # If successful, break out of retry loop
            if response.ok:
                break

            # If it's a client error (4xx), don't retry
            if 400 <= response.status_code < 500:
                break

            # For server errors (5xx), retry if we have attempts left
            if attempt < retry_attempts - 1:
                logger.warning('Server error {0}, retrying in {1} seconds (attempt {2}/{3})'.format(
                    response.status_code, retry_delay, attempt + 1, retry_attempts))
                time.sleep(retry_delay)
                continue

        except requests.exceptions.Timeout:
            if attempt < retry_attempts - 1:
                logger.warning('Timeout connecting to {0}, retrying in {1} seconds (attempt {2}/{3})'.format(
                    endpoint, retry_delay, attempt + 1, retry_attempts))
                time.sleep(retry_delay)
                continue
            else:
                logger.error('Timeout connecting to {0}'.format(endpoint))
                raise ConnectorError('Timeout connecting to Docker API: {0}'.format(endpoint))
        except requests.exceptions.ConnectionError:
            if attempt < retry_attempts - 1:
                logger.warning('Connection error to {0}, retrying in {1} seconds (attempt {2}/{3})'.format(
                    endpoint, retry_delay, attempt + 1, retry_attempts))
                time.sleep(retry_delay)
                continue
            else:
                logger.error('Connection error to {0}'.format(endpoint))
                raise ConnectorError('Cannot connect to Docker API: {0}'.format(endpoint))
        except Exception as e:
            logger.exception('Error invoking binary endpoint: {0}'.format(endpoint))
            if attempt == retry_attempts - 1:
                raise ConnectorError('Error invoking {0}: {1}'.format(endpoint, str(e)))
            continue

    if response is None:
        raise ConnectorError('No response received from Docker API after {0} attempts'.format(retry_attempts))

    if response.ok:
        if expect_json_response:
            try:
                return response.json()
            except ValueError:
                return {'result': response.text}

        # Return base64-encoded content for FortiSOAR-friendly handling
        content_b64 = base64.b64encode(response.content).decode()
        return {
            'content': content_b64,
            'content_type': response.headers.get('Content-Type', 'application/octet-stream'),
            'status_code': response.status_code
        }
    else:
        content = response.text
        logger.error('HTTP {0} (binary): {1}'.format(response.status_code, content))

        if response.status_code == 400:
            raise ConnectorError('Bad Request (binary): {0}'.format(content))
        elif response.status_code == 401:
            raise ConnectorError('Unauthorized (binary): {0}'.format(content))
        elif response.status_code == 403:
            raise ConnectorError('Forbidden (binary): {0}'.format(content))
        elif response.status_code == 404:
            raise ConnectorError('Resource not found (binary) for endpoint: {0}'.format(content))
        elif response.status_code == 409:
            raise ConnectorError('Conflict (binary): {0}'.format(content))
        elif response.status_code == 500:
            raise ConnectorError('Docker Engine internal error (binary): {0}'.format(content))
        elif response.status_code == 503:
            raise ConnectorError('Docker Engine unavailable (binary): {0}'.format(content))
        else:
            raise ConnectorError('HTTP {0} (binary): {1}'.format(response.status_code, content))
