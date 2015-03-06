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
OCCI registry
"""

#R0201:method could be func.E1002:old style obj,R0914-R0912:# of branches
#E1121:# positional args.
#pylint: disable=R0201,E1002,R0914,R0912,E1121

import uuid

from oslo.config import cfg

from occi_os_api.backends import openstack
from occi_os_api.extensions import os_addon

from occi_os_api.nova_glue import vm
from occi_os_api.nova_glue import storage
from occi_os_api.nova_glue import net
from occi_os_api.nova_glue import security
from occi_os_api.nova_glue import neutron

from occi import registry as occi_registry
from occi import core_model
from occi.extensions import infrastructure

CONF = cfg.CONF


class OCCIRegistry(occi_registry.NonePersistentRegistry):
    """
    Registry for OpenStack.

    Idea is the following: Create the OCCI entities (Resource and their
    links) here and let the backends handle actions, updates the attributes
    etc.
    """

    def __init__(self):
        super(OCCIRegistry, self).__init__()
        self.cache = {}

    def set_hostname(self, hostname):
        if CONF.occi_custom_location_hostname:
            hostname = CONF.occi_custom_location_hostname
        super(OCCIRegistry, self).set_hostname(hostname)

    def get_extras(self, extras):
        """
        Get data which is encapsulated in the extras.
        """
        sec_extras = None
        if extras is not None:
            sec_extras = {'user_id': extras['nova_ctx'].user_id,
                          'project_id': extras['nova_ctx'].project_id}
        return sec_extras

    # The following two are here to deal with the security group mixins

    def delete_mixin(self, mixin, extras):
        """
        Allows for the deletion of user defined mixins.
        If the mixin is a security group mixin then that mixin's
        backend is called.
        """
        if (hasattr(mixin, 'related') and
                os_addon.SEC_GROUP in mixin.related):
            backend = self.get_backend(mixin, extras)
            backend.destroy(mixin, extras)

        super(OCCIRegistry, self).delete_mixin(mixin, extras)

    def set_backend(self, category, backend, extras):
        """
        Assigns user id and tenant id to user defined mixins
        """
        if (hasattr(category, 'related') and
                os_addon.SEC_GROUP in category.related):
            backend = openstack.SecurityGroupBackend()
            backend.init_sec_group(category, extras)

        super(OCCIRegistry, self).set_backend(category, backend, extras)

    # The following two deal with the creation and deletion os links.

    def add_resource(self, key, resource, extras):
        """
        Just here to prevent the super class from filling up an unused dict.
        """
        if (key, extras['nova_ctx'].user_id) not in self.cache and \
                core_model.Link.kind in resource.kind.related:
            # don't need to cache twice, only adding links :-)
            self.cache[(key, extras['nova_ctx'].user_id)] = resource
        elif (key, extras['nova_ctx'].user_id) not in self.cache and \
                resource.kind == os_addon.SEC_RULE:
            # don't need to cache twice, only adding links :-)
            self.cache[(key, extras['nova_ctx'].user_id)] = resource

    def delete_resource(self, key, extras):
        """
        Just here to prevent the super class from messing up.
        """
        if (key, extras['nova_ctx'].user_id) in self.cache:
            self.cache.pop((key, extras['nova_ctx'].user_id))

    # the following routines actually retrieve the info form OpenStack. Note
    # that a cache is used. The cache is stable - so delete resources
    # eventually also get deleted form the cache.

    def get_resource(self, key, extras):
        """
        Retrieve a single resource.
        """
        context = extras['nova_ctx']
        iden = key[key.rfind('/') + 1:]

        vms = vm.get_vms(context)
        vm_res_ids = [item['uuid'] for item in vms]

        stors = storage.get_storage_volumes(context)
        stor_res_ids = [item['id'] for item in stors]

        nets = neutron.list_networks(context)
        net_ids = [item['id'] for item in nets]

        ports = neutron.list_ports(context)
        port_ids = [item['id'] for item in ports]

        secs = security.retrieve_groups_by_project(context)
        sec_ids = [item['id'] for item in secs]

        secr = [rule.get('rules') for rule in secs if rule.get('rules')][0]
        secr_ids = [rule.get('id') for rule in secr]

        if (key, context.user_id) in self.cache:
            # I have seen it - need to update or delete if gone in OS!
            # I have already seen it
            cached_item = self.cache[(key, context.user_id)]
            if iden not in net_ids and cached_item.kind == \
                    infrastructure.NETWORK:
                # it was delete in OS -> remove from cache + KeyError!
                # can delete it because it was my item!
                self.cache.pop((key, repr(extras)))
                raise KeyError
            if iden not in vm_res_ids and cached_item.kind == \
                    infrastructure.COMPUTE:
                # it was delete in OS -> remove links, cache + KeyError!
                # can delete it because it was my item!
                for link in cached_item.links:
                    self.cache.pop((link.identifier, repr(extras)))
                self.cache.pop((key, repr(extras)))
                raise KeyError
            if iden not in stor_res_ids and cached_item.kind == \
                    infrastructure.STORAGE:
                # it was delete in OS -> remove from cache + KeyError!
                # can delete it because it was my item!
                self.cache.pop((key, repr(extras)))
                raise KeyError
            if iden not in sec_ids and cached_item.kind == \
                    os_addon.SEC_GROUP:
                # it was delete in OS -> remove from cache + KeyError!
                # can delete it because it was my item!
                self.cache.pop((key, repr(extras)))
                raise KeyError
            if iden not in secr_ids and cached_item.kind == \
                    os_addon.SEC_RULE:
                # it was delete in OS -> remove from cache + KeyError!
                # can delete it because it was my item!
                self.cache.pop((key, repr(extras)))
                raise KeyError
            elif iden in net_ids:
                # it also exists in OS -> update it!
                result = self._update_occi_network(cached_item, extras)
            elif iden in vm_res_ids:
                # it also exists in OS -> update it (take links, mixins
                # from cached one)
                result = self._update_occi_compute(cached_item, extras)
            elif iden in sec_ids:
                result = self._update_occi_osgroup(cached_item, extras)
            elif iden in stor_res_ids:
                # it also exists in OS -> update it!
                result = self._update_occi_storage(cached_item, extras)
            else:
                # return cached item (links)
                return cached_item
        elif (key, None) in self.cache:
            # return shared entities from cache!
            return self.cache[(key, None)]
        else:
            # construct it.
            if iden in net_ids:
                # create new & add to cache!
                result = self._construct_occi_network(iden, extras)[0]
            elif iden in vm_res_ids:
                # create new & add to cache!
                result = self._construct_occi_compute(iden, extras)[0]
            elif iden in stor_res_ids:
                result = self._construct_occi_storage(iden, extras)[0]
            elif iden in port_ids:
                result = self._construct_occi_networkinterface(iden, extras)[0]
            elif iden in sec_ids:
                result = self._construct_occi_security_group(iden, extras)[0]
            elif iden in secr_ids:
                result = self._construct_occi_security_rule(iden, extras)[0]
            else:
                # doesn't exist!
                raise KeyError

        if result.identifier != key:
            raise AttributeError('Key/identifier mismatch! Requested: ' +
                                 key + ' Got: ' + result.identifier)
        return result

    def get_resource_keys(self, extras):
        """
        Retrieve the keys of all resources.
        """
        keys = []
        for item in self.cache.values():
            if item.extras is not None and item.extras != extras:
                # filter out items not belonging to this user!
                continue
            else:
                # add identifier
                keys.append(item.identifier)

        return keys

    def get_resources(self, extras):
        """
        Retrieve a set of resources.
        """

        # TODO: add security rules!

        context = extras['nova_ctx']
        result = []

        vms = vm.get_vms(context)
        vm_res_ids = [item['uuid'] for item in vms]

        stors = storage.get_storage_volumes(context)
        stor_res_ids = [item['id'] for item in stors]

        nets = neutron.list_networks(context)
        net_ids = [item['id'] for item in nets]

        secs = security.retrieve_groups_by_project(context)
        sec_ids = [item['id'] for item in secs]

        secr = [rule.get('rules') for rule in secs if rule.get('rules')][0]
        secr_ids = [rule.get('id') for rule in secr]


        for item in self.cache.values():
            if item.extras is not None and item.extras['user_id'] != \
                    context.user_id:
                # filter out items not belonging to this user!
                continue
            item_id = item.identifier[item.identifier.rfind('/') + 1:]
            if item.extras is None:
                # add to result set
                result.append(item)
            elif item_id in net_ids and item.kind == \
                    infrastructure.NETWORK:
                # check & update (take links, mixins from cache)
                # add compute and it's links to result
                self._update_occi_network(item, extras)
                result.append(item)
            elif item_id in vm_res_ids and item.kind == \
                    infrastructure.COMPUTE:
                # check & update (take links, mixins from cache)
                # add compute and it's links to result
                self._update_occi_compute(item, extras)
                result.append(item)
                result.extend(item.links)
            elif item_id in stor_res_ids and item.kind == \
                    infrastructure.STORAGE:
                # check & update (take links, mixins from cache)
                # add compute and it's links to result
                self._update_occi_storage(item, extras)
                result.append(item)
            elif item_id in sec_ids and item.kind == \
                    os_addon.SEC_GROUP:
                # check & update (take links, mixins from cache)
                # add compute and it's links to result
                self._update_occi_osgroup(item, extras)
                result.append(item)
            elif item_id in secr_ids and item.kind == \
                    os_addon.SEC_RULE:
                # check & update (take links, mixins from cache)
                # add compute and it's links to result
                self._update_occi_osrule(item, extras)
                result.append(item)
            elif item_id not in net_ids and item.kind == \
                    infrastructure.NETWORK:
                # remove item and it's links from cache!
                for link in item.links:
                    self.cache.pop((link.identifier, item.extras['user_id']))
                self.cache.pop((item.identifier, item.extras['user_id']))
            elif item_id not in vm_res_ids and item.kind == \
                    infrastructure.COMPUTE:
                # remove item and it's links from cache!
                for link in item.links:
                    self.cache.pop((link.identifier, item.extras['user_id']))
                self.cache.pop((item.identifier, item.extras['user_id']))
            elif item_id not in stor_res_ids and item.kind == \
                    infrastructure.STORAGE:
                # remove item
                self.cache.pop((item.identifier, item.extras['user_id']))
        for item in nets:
            if (infrastructure.NETWORK.location + item['id'],
                    context.user_id) in self.cache:
                continue
            else:
                # construct (with links and mixins and add to cache!
                ent_list = self._construct_occi_network(item['id'], extras)
                result.extend(ent_list)
        for item in secs:
            if (os_addon.SEC_GROUP.location + item['id'],
                    context.user_id) in self.cache:
                continue
            else:
                # construct (with links and mixins and add to cache!
                ent_list = self._construct_occi_security_group(item['id'], extras)
                result.extend(ent_list)
        for item in secr:
            if (os_addon.SEC_RULE.location + item['id'],
                    context.user_id) in self.cache:
                continue
            else:
                # construct (with links and mixins and add to cache!
                ent_list = self._construct_occi_security_rule(item['id'], extras)
                result.extend(ent_list)
        for item in vms:
            if (infrastructure.COMPUTE.location + item['uuid'],
                    context.user_id) in self.cache:
                continue
            else:
                # construct (with links and mixins and add to cache!
                # add compute and it's linke to result
                ent_list = self._construct_occi_compute(item['uuid'], extras)
                result.extend(ent_list)
        for item in stors:
            if (infrastructure.STORAGE.location + item['id'],
                    context.user_id) in self.cache:
                continue
            else:
                # construct (with links and mixins and add to cache!
                # add compute and it's linke to result
                ent_list = self._construct_occi_storage(item['id'], extras)
                result.extend(ent_list)
        return result

    # Not part of parent

    def _update_occi_compute(self, entity, extras):
        """
        Update an occi compute resource instance.
        """
        return entity

    def _construct_occi_compute(self, identifier, extras):
        """
        Construct a OCCI compute instance.

        First item in result list is entity self!

        Adds it to the cache too!
        """
        result = []
        context = extras['nova_ctx']

        instance = vm.get_vm(identifier, context)

        # 1. get identifier
        iden = infrastructure.COMPUTE.location + identifier
        entity = core_model.Resource(iden, infrastructure.COMPUTE,
                                     [os_addon.OS_VM])
        result.append(entity)

        # 2. os and res templates
        flavor_id = int(instance['instance_type_id'])
        res_tmp = self.get_category('/' + str(flavor_id) + '/', extras)
        if res_tmp:
            entity.mixins.append(res_tmp)

        os_id = instance['image_ref']
        image_id = vm.retrieve_image(os_id, context)['id']
        image_tmp = self.get_category('/' + image_id + '/', extras)
        if image_tmp:
            entity.mixins.append(image_tmp)

        # 3. network links & get links from cache!
        net_links = net.get_network_details(identifier, context)

        for item in net_links:
            source = self.get_resource(infrastructure.NETWORK.location +
                                       str(item['net_id']), extras)
            link = core_model.Link(infrastructure.NETWORKINTERFACE.location +
                                   str(item['vif']),
                                   infrastructure.NETWORKINTERFACE, [], source,
                                   entity)
            link.attributes['occi.core.id'] = str(item['vif'])
            link.extras = self.get_extras(extras)
            source.links.append(link)
            result.append(link)
            self.cache[(link.identifier, context.user_id)] = link

        # core.id and cache it!
        entity.attributes['occi.core.id'] = identifier
        entity.extras = self.get_extras(extras)
        self.cache[(entity.identifier, context.user_id)] = entity

        return result

    def _update_occi_storage(self, entity, extras):
        """
        Update a storage resource instance.
        """
        return entity

    def _construct_occi_storage(self, identifier, extras):
        """
        Construct a OCCI storage instance.

        First item in result list is entity self!

        Adds it to the cache too!
        """
        result = []
        context = extras['nova_ctx']
        stor = storage.get_storage(identifier, context)

        # id, display_name, size, status
        iden = infrastructure.STORAGE.location + identifier
        entity = core_model.Resource(iden, infrastructure.STORAGE, [])
        result.append(entity)

        # create links on VM resources
        if stor['status'] == 'in-use':
            iden = str(uuid.uuid4())
            source = self.get_resource(infrastructure.COMPUTE.location +
                                       str(stor['instance_uuid']), extras)
            link = core_model.Link(infrastructure.STORAGELINK.location +
                                   iden,
                                   infrastructure.STORAGELINK, [], source,
                                   entity)
            link.attributes['occi.core.id'] = iden
            link.extras = self.get_extras(extras)
            source.links.append(link)
            result.append(link)
            self.cache[(link.identifier, context.user_id)] = link

        # core.id and cache it!
        entity.attributes['occi.core.id'] = identifier
        entity.extras = self.get_extras(extras)
        self.cache[(entity.identifier, context.user_id)] = entity

        return result

    def _update_occi_network(self, entity, extras):
        """
        Update a network resource.
        """
        return entity

    def _construct_occi_network(self, identifier, extras):
        """
        Create a network resource.
        """
        result = []
        context = extras['nova_ctx']

        net = neutron.retrieve_network(context, identifier)
        mixins = []
        if len(net['subnets']) > 0:
            mixins = [infrastructure.IPNETWORK]

        iden = infrastructure.NETWORK.location + identifier
        entity = core_model.Resource(iden, infrastructure.NETWORK, mixins)
        entity.attributes['occi.core.id'] = identifier
        entity.extras = self.get_extras(extras)
        self.cache[(entity.identifier, context.user_id)] = entity
        result.append(entity)

        # TODO: deal with routers!
        return result

    def _construct_occi_networkinterface(self, identifier, extras):
        """
        Create a network interface resource.
        """
        result = []
        context = extras['nova_ctx']
        item = neutron.retrieve_port(context, identifier)
        iden = infrastructure.NETWORKINTERFACE.location + identifier
        # get network resource
        entity = self.get_resource(
            infrastructure.COMPUTE.location + str(item['device_id']),
            extras
        )
        # get compute resource
        source = self.get_resource(
            infrastructure.NETWORK.location + str(item['network_id']),
            extras
        )
        # create link
        link = core_model.Link(
            infrastructure.NETWORKINTERFACE.location + item['id'],
            infrastructure.NETWORKINTERFACE,
            [],
            source,
            entity
        )
        link.attributes['occi.core.id'] = iden
        link.extras = self.get_extras(extras)
        source.links.append(link)
        result.append(link)
        self.cache[(link.identifier, context.user_id)] = link
        return result

    def _construct_occi_security_rule(self, identifier, extras):
        """
        Contruct security group
        :param identifier: Id of
        :param extras:
        :return: cache object
        """
        result = []
        context = extras['nova_ctx']

        group = security.retrieve_rule(identifier, context)
        mixins = []

        iden = os_addon.SEC_RULE.location + identifier
        entity = core_model.Resource(iden, os_addon.SEC_RULE, mixins)
        entity.attributes['occi.core.id'] = identifier
        entity.extras = self.get_extras(extras)
        self.cache[(entity.identifier, context.user_id)] = entity
        result.append(entity)

        return result

    def _update_occi_osgroup(self, entity, extras):
        return entity

    def _construct_occi_security_group(self, identifier, extras):
        """
        Contruct security group
        :param identifier: Id of
        :param extras:
        :return: cache object
        """
        result = []
        context = extras['nova_ctx']

        mixins = []

        group = security.retrieve_group(identifier, context)
        if len(group.get('rules') > 0):
            for rule in group.get('rules'):
                mixins.append(
                    self. _construct_occi_security_rule(
                        rule.get('id'),
                        extras
                    )
                )

        iden = os_addon.SEC_GROUP.location + identifier
        entity = core_model.Resource(iden, os_addon.SEC_GROUP, mixins)
        entity.attributes['occi.core.id'] = identifier
        entity.extras = self.get_extras(extras)
        self.cache[(entity.identifier, context.user_id)] = entity
        result.append(entity)

        return result

    def _update_occi_osrule(self, entity, extras):
        return entity
