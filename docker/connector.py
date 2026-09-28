"""
Copyright start
MIT License
Copyright (c) 2026 Fortinet Inc
Copyright end
"""

from connectors.core.connector import Connector
from connectors.core.connector import get_logger, ConnectorError
from django.utils.module_loading import import_string
from .builtins import *
from .constants import LOGGER_NAME
from .health_check import health_check

logger = get_logger(LOGGER_NAME)


class DockerConnector(Connector):

    def execute(self, config, operation, params, *args, **kwargs):
        operation_callable = supported_operations.get(operation)
        if not operation_callable:
            raise ConnectorError('Unsupported operation: {0}'.format(operation))
        return operation_callable(config, params)

    def check_health(self, config=None, *args, **kwargs):
        return health_check(config, *args, **kwargs)
