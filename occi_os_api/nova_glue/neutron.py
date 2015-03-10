# coding=utf-8
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
#    Copyright (c) 2014, Intel Performance Learning Solutions Ltd.
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
SDN related 'glue' :-)

Main reason this uses python-neutronclient is that the nova internal API throw
NotImplementedErrors when creating networks:

    https://github.com/openstack/nova/blob/master/nova/network/\
        neutronv2/api.py#L1018
"""

from nova.openstack.common import log
from neutronclient.neutron import client
from nova.network.neutronv2 import constants
from occi_os_api.utils import get_neutron_url

LOG = log.getLogger(__name__)


def list_networks(context):
    """
    List networks.
    """
    token = context.auth_token

    try:
        neutron = client.Client('2.0', endpoint_url=get_neutron_url(), token=token)
        tmp = neutron.list_networks()
        return tmp['networks']
    except Exception as err:
        raise AttributeError(err)


def create_network(context):
    """
    Create a new network with subnet.
    """
    token = context.auth_token

    try:
        neutron = client.Client('2.0', endpoint_url=get_neutron_url(), token=token)
        network = {'admin_state_up': True}
        tmp = neutron.create_network({'network': network})
        return tmp['network']['id']
    except Exception as err:
        raise AttributeError(err)


def retrieve_network(context, iden):
    """
    Retrieve network information.
    """
    token = context.auth_token

    try:
        neutron = client.Client('2.0', endpoint_url=get_neutron_url(), token=token)
        network = neutron.show_network(iden)
        return network.get('network')
    except Exception as err:
        raise AttributeError(err)


def delete_network(context, iden):
    """
    Delete a network.
    """
    token = context.auth_token

    try:
        neutron = client.Client('2.0', endpoint_url=get_neutron_url(), token=token)
        neutron.delete_network(iden)
    except Exception as err:
        raise AttributeError(err)


def create_subnet(context, iden, cidr, gw, dynamic=True):
    """
    Create a subnet for a network.
    """
    token = context.auth_token
    tent = context.tenant

    try:
        neutron = client.Client('2.0', endpoint_url=get_neutron_url(), token=token)

        subnet = {'network_id': iden,
                  'ip_version': 4,
                  'cidr': cidr,
                  'enable_dhcp': int(dynamic),
                  'gateway_ip': gw,
                  'tenant_id': tent}
        neutron.create_subnet({'subnet': subnet})
    except Exception as err:
        raise AttributeError(err)


def retrieve_subnet(context, iden):
    """
    Retrieve a subnet.
    """
    token = context.auth_token

    try:
        neutron = client.Client('2.0', endpoint_url=get_neutron_url(), token=token)
        return neutron.show_subnet(iden)
    except Exception as err:
        raise AttributeError(err)


def delete_subnet(context, iden):
    """
    Delete a subnet.
    """
    token = context.auth_token

    try:
        neutron = client.Client('2.0', endpoint_url=get_neutron_url(), token=token)
        return neutron.delete_subnet(iden)
    except Exception as err:
        raise AttributeError(err)


def create_router(context, source_id, target_id):
    """
    Create a router.
    """
    token = context.auth_token

    try:
        # TODO: check if we can do this for all!
        neutron = client.Client('2.0', endpoint_url=get_neutron_url(), token=token)

        router = neutron.create_router({'router': {'name': 'occirouter'}})
        subnet = neutron.list_subnets(network_id=source_id)['subnets'][0]

        neutron.add_interface_router(router['router']['id'],
                                     {'subnet_id': subnet['id']})
        neutron.add_gateway_router(router['router']['id'],
                                   {'network_id': target_id})

        return router
    except Exception as err:
        raise AttributeError(err)


def delete_router(context, router_id, network_id):
    """
    Remove a router.
    """
    token = context.auth_token

    try:
        neutron = client.Client('2.0', endpoint_url=get_neutron_url(), token=token)
        neutron.remove_gateway_router(router_id)
        subnet = neutron.list_subnets(network_id=network_id)['subnets'][0]
        neutron.remove_interface_router(router_id, {'subnet_id': subnet['id']})
        neutron.delete_router(router_id)
    except Exception as err:
        raise AttributeError(err)


def add_floating_ip(context, iden, network_id):
    """
    Add a floating ip.
    """
    token = context.auth_token
    neutron = client.Client('2.0', endpoint_url=get_neutron_url(), token=token)

    try:
        port = list_ports(device_id=iden)

        if len(port) == 0:
            return None
        else:
            body = {'floatingip':
                        {
                            'floating_network_id': network_id,
                            'port_id': port[0]['id']
                        }
            }
            float = neutron.create_floatingip(body)
        return float
    except Exception as err:
        raise AttributeError(err)


def remove_floating_ip(context, iden):
    """
    Remove a floating ip.
    """
    token = context.auth_token
    neutron = client.Client('2.0', endpoint_url=get_neutron_url(), token=token)
    try:
        neutron.delete_floatingip(iden)
    except Exception as err:
        raise AttributeError(err)

def retrieve_port(context, iden, **kwargs):
    """
    Retrieve port information.
    """
    token = context.auth_token

    try:
        neutron = client.Client('2.0', endpoint_url=get_neutron_url(), token=token)
        port = neutron.show_port(iden, **kwargs)
        return port['port']
    except Exception as err:
        raise AttributeError(err)

def list_ports(context, **kwargs):
    """
    List ports
    """
    token = context.auth_token

    try:
        neutron = client.Client('2.0', endpoint_url=get_neutron_url(), token=token)
        ports = neutron.list_ports(**kwargs)
        return ports['ports']
    except Exception as err:
        raise AttributeError(err)

def get_port_status(context, iden):
    """
    Retrieve port status.
    """
    token = context.auth_token

    try:
        neutron = client.Client('2.0', endpoint_url=get_neutron_url(), token=token)
        port = neutron.show_port(iden)
        return port['port']
    except Exception as err:
        raise AttributeError(err)