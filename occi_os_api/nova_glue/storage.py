# coding=utf-8
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
#    Copyright (c) 2012, Intel Performance Learning Solutions Ltd.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
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
Storage related glue :-)
"""

from occi import exceptions
from occi_os_api.utils import get_openstack_api


def create_storage(size, name, context):
    """
    Create a storage instance.

    size -- Size of the storage.
    name -- Name of the storage volume.
    context -- The os context.
    """
    # L8R: A blueprint?
    # OpenStack deals with size in terms of integer.
    # Need to convert float to integer for now and only if the float
    # can be losslessly converted to integer
    # e.g. See nova/quota.py:allowed_volumes(...)
    if not float(size).is_integer:
        raise AttributeError('Volume sizes cannot be specified as fractional'
                             ' floats.')
    size = int(float(size))

    try:
        return get_openstack_api('volume').create(context,
                                 size,
                                 name,
                                 name)
    except Exception as e:
        raise AttributeError(e.message)


def delete_storage_instance(uid, context):
    """
    Delete a storage instance.

    uid -- Id of the volume.
    context -- The os context.
    """
    try:
        get_openstack_api('volume').delete(context, uid)
    except Exception as e:
        raise AttributeError(e.message)


def snapshot_storage_instance(uid, name, description, context):
    """
    Snapshots an storage instance.

    uid -- Id of the volume.
    context -- The os context.
    """
    try:
        instance = get_storage(uid, context)
        get_openstack_api('volume').create_snapshot(context, instance, name, description)
    except Exception as e:
        raise AttributeError(e.message)


def get_storage(uid, context):
    """
    Retrieve an Volume instance from nova.

    uid -- id of the instance
    context -- the os context
    """
    try:
        instance = get_openstack_api('volume').get(context, uid)
    except Exception:
        raise exceptions.HTTPError(404, 'Volume not found!')
    return instance


def get_storage_volumes(context):
    """
    Retrieve all storage entities from user.
    """
    return get_openstack_api('volume').get_all(context)
