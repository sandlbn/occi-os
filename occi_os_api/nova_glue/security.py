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
Security related 'glue'
"""

from occi_os_api.utils import get_openstack_api


# TODO: exception handling


def create_group(name, description, context):
    """
    Create a OS security group.

    name -- Name of the group.
    description -- Description.
    context -- The os context.
    """
    get_openstack_api('security').create_security_group(context, name, description)


def remove_group(group, context):
    """
    Remove a security group.

    group -- the security group.
    context -- The os context.
    """
    get_openstack_api('security').destroy(context, group)


def retrieve_group_by_name(name, context):
    """
    Retrieve the security group associated with the security mixin.

    mixin_term -- The term of the mixin representing the group.
    context -- The os context.
    """
    return get_openstack_api('security').list(context, names=[name], project=context.project_id)[0]

def retrieve_group(iden, context):
    """
    Retrieve the security group

    mixin_term -- The term of the mixin representing the group.
    context -- The os context.
    """
    return get_openstack_api('security').get(context, iden)

def retrieve_groups_by_project(context):
    """
    Retrieve list of security groups by project.

    context -- The os context.
    """
    return get_openstack_api('security').list(context, project=context.project_id)


def create_rule(name, iden, rule, context):
    """
    Create a security rule.

    rule -- The rule.
    context -- The os context.
    """
    # TODO: needs work!
    try:
        return get_openstack_api('security').add_rules(context, iden, name, rule)[0]
    except Exception as e:
        raise AttributeError(e.message)


def remove_rule(rule, context):
    """
    Remove a security rule.

    rule -- The rule
    context -- The os context.
    """
    group_id = rule['parent_group_id']
    security_group = get_openstack_api('security').get(context, None, group_id)
    get_openstack_api('security').remove_rules(context, security_group, (rule['id'], ))


def retrieve_rule(uid, context):
    """
    Retrieve a rule.

    uid -- Id of the rule (entity.attributes['occi.core.id'])
    context -- The os context.
    """
    return get_openstack_api('security').get_rule(context, uid)
