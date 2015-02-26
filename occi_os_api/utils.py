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

from nova import compute
from nova.image import glance
from oslo.config import cfg

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
