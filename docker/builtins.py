"""
Copyright start
MIT License
Copyright (c) 2026 Fortinet Inc
Copyright end
"""

from .system_ops import get_version, get_info, system_df, system_events, ping, auth
from .containers import list_containers, inspect_container, start_container, stop_container, remove_container, \
    create_container, restart_container, kill_container, container_logs, rename_container, prune_containers, \
    exec_container, pause_container, unpause_container, container_stats, container_export, container_commit, \
    update_container, wait_container, attach_container, resize_container, copy_from_container, copy_to_container
from .images import list_images, pull_image, inspect_image, remove_image, tag_image, prune_images, build_image, \
    search_images, image_history, push_image
from .networks import list_networks, inspect_network, create_network, connect_network, disconnect_network, \
    remove_network, prune_networks
from .volumes import list_volumes, inspect_volume, create_volume, remove_volume, prune_volumes

supported_operations = {
    # System operations
    'get_version': get_version, 'get_info': get_info, 'system_df': system_df, 'system_events': system_events,
    'ping': ping, 'auth': auth,

    # Container operations
    'list_containers': list_containers, 'inspect_container': inspect_container, 'start_container': start_container,
    'stop_container': stop_container, 'remove_container': remove_container, 'create_container': create_container,
    'restart_container': restart_container, 'kill_container': kill_container, 'container_logs': container_logs,
    'rename_container': rename_container, 'prune_containers': prune_containers, 'exec_container': exec_container,
    'pause_container': pause_container, 'unpause_container': unpause_container, 'container_stats': container_stats,
    'container_export': container_export, 'container_commit': container_commit, 'update_container': update_container,
    'wait_container': wait_container, 'attach_container': attach_container, 'resize_container': resize_container,
    'copy_from_container': copy_from_container, 'copy_to_container': copy_to_container,

    # Image operations
    'list_images': list_images, 'pull_image': pull_image, 'inspect_image': inspect_image, 'remove_image': remove_image,
    'tag_image': tag_image, 'prune_images': prune_images, 'build_image': build_image, 'search_images': search_images,
    'image_history': image_history, 'push_image': push_image,

    # Network operations
    'list_networks': list_networks, 'inspect_network': inspect_network, 'create_network': create_network,
    'connect_network': connect_network, 'disconnect_network': disconnect_network, 'remove_network': remove_network,
    'prune_networks': prune_networks,

    # Volume operations
    'list_volumes': list_volumes, 'inspect_volume': inspect_volume, 'create_volume': create_volume,
    'remove_volume': remove_volume, 'prune_volumes': prune_volumes
}
