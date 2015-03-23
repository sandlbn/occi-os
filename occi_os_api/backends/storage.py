# coding=utf-8
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# Copyright (c) 2012, Intel Performance Learning Solutions Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Backends for the storage resource.
"""

# pylint: disable=R0201,W0232,W0613
from datetime import date

import uuid

from occi import backend
from occi import exceptions
from occi.extensions import infrastructure

from occi_os_api.nova_glue import storage
from occi_os_api.nova_glue import vm
from occi_os_api.utils import get_image_name


class StorageBackend(backend.KindBackend, backend.ActionBackend):

    """
    Backend to handle storage resources.
    """

    def create(self, entity, extras):
        """
        Creates a new volume.
        """
        context = extras['nova_ctx']
        if 'occi.storage.size' not in entity.attributes:
            raise AttributeError('size attribute not found!')
        size = entity.attributes['occi.storage.size']

        if 'occi.core.title' not in entity.attributes:
            name = str(uuid.uuid4())
        else:
            name = entity.attributes['occi.core.title']

        new_volume = storage.create_storage(size, name, context)
        vol_id = new_volume['id']

        # Work around problem that instance is lazy-loaded...
        new_volume = storage.get_storage(vol_id, context)

        if new_volume['status'] == 'error':
            raise exceptions.HTTPError(500, 'There was an error creating the '
                                            'volume')
        entity.attributes['occi.core.id'] = str(vol_id)
        entity.identifier = infrastructure.STORAGE.location + vol_id

        if new_volume['status'] == 'available':
            entity.attributes['occi.storage.state'] = 'active'

        entity.actions = [infrastructure.OFFLINE, infrastructure.BACKUP,
                          infrastructure.SNAPSHOT, infrastructure.RESIZE]

    def retrieve(self, entity, extras):
        """
        Gets a representation of the storage volume and presents it ready for
        rendering by pyssf.
        """
        v_id = entity.attributes['occi.core.id']

        volume = storage.get_storage(v_id, extras['nova_ctx'])

        entity.attributes['occi.core.title'] = str(get_image_name(volume))
        entity.attributes['occi.storage.size'] = str(float(volume.get('size')))

        # OS volume states:
        #       available, creating, deleting, in-use, error, error_deleting
        if volume['status'] == 'available' or volume['status'] == 'in-use':
            entity.attributes['occi.storage.state'] = 'online'
            entity.actions = [infrastructure.OFFLINE, infrastructure.BACKUP,
                              infrastructure.SNAPSHOT, infrastructure.RESIZE]
        else:
            entity.attributes['occi.storage.state'] = 'offline'
            entity.actions = [infrastructure.ONLINE]

    def update(self, old, new, extras):
        """
        Updates simple attributes of a storage resource:
        occi.core.title, occi.core.summary
        """
        # update attributes.
        if len(new.attributes) > 0:
            # support only title and summary changes now.
            if 'occi.core.title' in new.attributes and \
                    len(new.attributes['occi.core.title']) > 0:
                old.attributes['occi.core.title'] = \
                    new.attributes['occi.core.title']
            if 'occi.core.title' in new.attributes and \
                    len(new.attributes['occi.core.summary']) > 0:
                old.attributes['occi.core.summary'] = \
                    new.attributes['occi.core.summary']

    def delete(self, entity, extras):
        """
        Deletes the storage resource
        """
        context = extras['nova_ctx']
        volume_id = entity.attributes['occi.core.id']

        storage.delete_storage_instance(volume_id, context)

    def action(self, entity, action, attributes, extras):
        """
        Executes actions against the target storage resource.
        """
        if action not in entity.actions:
            raise AttributeError("This action is currently no applicable.")
        elif action in [infrastructure.ONLINE, infrastructure.OFFLINE,
                        infrastructure.BACKUP, infrastructure.RESIZE]:
            pass
            # TODO: 'The operations online, offline, backup and resize
            # currently not supported!')
        elif action == infrastructure.SNAPSHOT:
            volume_id = entity.attributes['occi.core.id']
            name = volume_id + date.today().isoformat()
            if 'occi.core.summary' in entity.attributes:
                description = entity.attributes['occi.core.summary']
            else:
                description = 'N/A'
            storage.snapshot_storage_instance(volume_id, name, description,
                                              extras['nova_ctx'])


class StorageLinkBackend(backend.KindBackend):

    """
    A backend for the storage links.
    """

    def create(self, link, extras):
        """
        Creates a link from a compute instance to a storage volume.
        The user must specify what the device id is to be.
        """
        context = extras['nova_ctx']
        instance_id = link.source.attributes['occi.core.id']
        volume_id = link.target.attributes['occi.core.id']
        mount_point = link.attributes['occi.storagelink.deviceid']

        vm.attach_volume(instance_id, volume_id, mount_point, context)

        link.attributes['occi.core.id'] = str(uuid.uuid4())
        link.attributes['occi.storagelink.deviceid'] = \
            link.attributes['occi.storagelink.deviceid']
        link.attributes['occi.storagelink.mountpoint'] = ''
        link.attributes['occi.storagelink.state'] = 'active'

    def delete(self, link, extras):
        """
        Unlinks the the compute from the storage resource.
        """
        instance_id = link.source.attributes['occi.core.id']
        volume_id = link.target.attributes['occi.core.id']

        volume = storage.get_storage(volume_id, extras['nova_ctx'])
        vm.detach_volume(instance_id, volume, extras['nova_ctx'])
