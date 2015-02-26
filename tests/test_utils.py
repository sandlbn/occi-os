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
Test utils module.
"""

#pylint: disable=W0102,C0103,R0904,R0801

import unittest
import mock
import nova
from occi_os_api.utils import get_openstack_api, get_neutron_url
from oslo.config import cfg


class TestUtils(unittest.TestCase):
    """
    Tests the storage backend!
    """
    def test_p_get_openstack_api(self):
        """
        Check get_openstack_api function for positive scenarious
        """

        nova.rpc.get_client = mock.MagicMock(return_value=True)
        nova.rpc.get_notifier = mock.MagicMock(return_value=True)

        neutron = get_openstack_api('neutron')
        self.assertEqual(
            type(neutron),
            type(nova.compute.API().network_api)
        )
        compute = get_openstack_api('compute')
        self.assertEqual(
            type(compute),
            type(nova.compute.API())
        )

        security = get_openstack_api('security')
        self.assertEqual(
            type(security),
            type(nova.compute.API().security_group_api)
        )

        image = get_openstack_api('image')
        self.assertEqual(
            type(image),
            type(nova.image.glance.get_default_image_service())
        )

        volume = get_openstack_api('volume')
        self.assertEqual(
            type(volume),
            type(nova.compute.API().volume_api)
        )

    def test_n_get_openstack_api(self):
        """
        Check get_openstack_api function for negative scenarious
        """

        nova.rpc.get_client = mock.MagicMock(return_value=True)
        nova.rpc.get_notifier = mock.MagicMock(return_value=True)

        with self.assertRaises(ValueError):
            get_openstack_api('non_ex_api')

        with self.assertRaises(TypeError):
            get_openstack_api()

    def test_p_get_neutron_url(self):
        """
        Test get_neutron_url for positive scenario
        """

        opt_group = cfg.OptGroup(name='neutron')
        neutron_opts = [
            cfg.StrOpt('url', default='localhost:999')
        ]
        CONF = cfg.CONF
        CONF.register_group(opt_group)
        CONF.register_opts(neutron_opts, opt_group)

        neutron_url = get_neutron_url()
        self.assertEqual(neutron_url, "localhost:999")
