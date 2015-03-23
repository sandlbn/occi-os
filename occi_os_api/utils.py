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

from nova import compute
from nova.image import glance

from occi.extensions import infrastructure
from oslo.config import cfg

from occi_os_api.extensions import os_addon


CONF = cfg.CONF


def get_openstack_api(api):
    """
    returns openstack api instance
    """

    if api == 'security':
        return compute.API().security_group_api
    elif api == 'compute':
        return compute.API()
    elif api == 'neutron':
        return compute.API().network_api
    elif api == 'volume':
        return compute.API().volume_api
    elif api == 'image':
        return glance.get_default_image_service()
    else:
        raise ValueError('{0} API not found'.format(str(api)))


def get_neutron_url():
    """
    returns neutron url based on oslo config
    """
    return CONF.neutron.url


def occify_terms(term_name):
    """
    Occifies a term_name so that it is compliant with GFD 185.
    """
    if term_name:
        return str(term_name).strip().replace(
            ' ', '_').replace(
            '.', '-').lower()


def sanitize(value):
    """
    Removes empty spaces from api responses,
    returning empty string if response is None
    """
    if value:
        return str(value).strip().lower()
    else:
        return ''


def get_item_id(item):
    return item.identifier[item.identifier.rfind('/') + 1:]


def get_image_name(image):
    """
    Return image name if Image name is not None
    if Image name is None return Image Id
    """
    if image.get('name'):
        return image.get('name')
    else:
        return image.get('id')


def is_compute(resource):
    """
    Return True if object is a compute resource
    :param resource:
    :return: bool
    """
    if resource == infrastructure.COMPUTE:
        return True
    return False


def is_network(resource):
    """
    Return True if object is a network resource
    :param resource:
    :return: bool
    """
    if resource == infrastructure.NETWORK:
        return True
    return False


def is_networkinterface(resource):
    """
    Return True if object is a network
    interface resource
    :param resource:
    :return: bool
    """
    if resource == infrastructure.NETWORKINTERFACE:
        return True
    return False


def is_sec_group(resource):
    """
    Return True if object is a security
    group resource
    :param resource:
    :return: bool
    """
    if resource == os_addon.SEC_GROUP:
        return True
    return False


def is_sec_rule(resource):
    """
    Return True if object is a security
    rule resource
    :param resource:
    :return: bool
    """
    if resource == os_addon.SEC_RULE:
        return True
    return False


def is_storage(resource):
    """
    Return True if object is a storage
    resource
    :param resource:
    :return: bool
    """
    if resource == infrastructure.STORAGE:
        return True
    return False
