"""
Copyright start
MIT License
Copyright (c) 2026 Fortinet Inc
Copyright end
"""

LOGGER_NAME = 'docker'

SYSTEM_TYPE = {
    "Container": "container",
    "Image": "image",
    "Volume": "volume",
    "Build Cache": "build_cache"
}

CONDITION_TYPE = {
    "Not Running": "not-running",
    "Next Exit": "next-exit",
    "Removed": "removed"
}

from datetime import datetime


def convert_timestamp(timestamp):
    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    epoch = int(dt.timestamp())
    return epoch
