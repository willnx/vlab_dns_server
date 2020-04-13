# -*- coding: UTF-8 -*-
"""
A suite of tests for the functions in vmware.py
"""
import unittest
from unittest.mock import patch, MagicMock

from vlab_dns_api.lib.worker import vmware


class TestVMware(unittest.TestCase):
    """A set of test cases for the vmware.py module"""

    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, 'vCenter')
    def test_show_dns(self, fake_vCenter, fake_consume_task, fake_get_info):
        """``dns`` returns a dictionary when everything works as expected"""
        fake_vm = MagicMock()
        fake_vm.name = 'Dns'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder
        fake_get_info.return_value = {'meta': {'component': 'Dns',
                                               'created': 1234,
                                               'version': '1.0',
                                               'configured': False,
                                               'generation': 1}}

        output = vmware.show_dns(username='alice')
        expected = {'Dns': {'meta': {'component': 'Dns',
                                                             'created': 1234,
                                                             'version': '1.0',
                                                             'configured': False,
                                                             'generation': 1}}}
        self.assertEqual(output, expected)

    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware.virtual_machine, 'power')
    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, 'vCenter')
    def test_delete_dns(self, fake_vCenter, fake_consume_task, fake_power, fake_get_info):
        """``delete_dns`` returns None when everything works as expected"""
        fake_logger = MagicMock()
        fake_vm = MagicMock()
        fake_vm.name = 'DnsBox'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder
        fake_get_info.return_value = {'meta': {'component': 'Dns',
                                               'created': 1234,
                                               'version': '1.0',
                                               'configured': False,
                                               'generation': 1}}

        output = vmware.delete_dns(username='bob', machine_name='DnsBox', logger=fake_logger)
        expected = None

        self.assertEqual(output, expected)

    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware.virtual_machine, 'power')
    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, 'vCenter')
    def test_delete_dns_value_error(self, fake_vCenter, fake_consume_task, fake_power, fake_get_info):
        """``delete_dns`` raises ValueError when unable to find requested vm for deletion"""
        fake_logger = MagicMock()
        fake_vm = MagicMock()
        fake_vm.name = 'win10'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder
        fake_get_info.return_value = {'meta': {'component': 'Dns',
                                               'created': 1234,
                                               'version': '1.0',
                                               'configured': False,
                                               'generation': 1}}

        with self.assertRaises(ValueError):
            vmware.delete_dns(username='bob', machine_name='myOtherDnsBox', logger=fake_logger)

    @patch.object(vmware.virtual_machine, 'config_static_ip')
    @patch.object(vmware.virtual_machine, 'set_meta')
    @patch.object(vmware, 'Ova')
    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware.virtual_machine, 'deploy_from_ova')
    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, 'vCenter')
    def test_create_dns(self, fake_vCenter, fake_consume_task, fake_deploy_from_ova, fake_get_info, fake_Ova, fake_set_meta, fake_config_static_ip):
        """``create_dns`` returns a dictionary upon success"""
        fake_logger = MagicMock()
        fake_deploy_from_ova.return_value.name = 'myDns'
        fake_get_info.return_value = {'worked': True}
        fake_Ova.return_value.networks = ['someLAN']
        fake_vCenter.return_value.__enter__.return_value.networks = {'someLAN' : vmware.vim.Network(moId='1')}


        output = vmware.create_dns(username='alice',
                                       machine_name='DnsBox',
                                       image='1.0.0',
                                       network='someLAN',
                                       static_ip='192.168.1.2',
                                       default_gateway='192.168.1.1',
                                       netmask='255.255.255.0',
                                       dns=['192.168.1.1'],
                                       logger=fake_logger)
        expected = {'myDns': {'worked': True}}

        self.assertEqual(output, expected)

    @patch.object(vmware.virtual_machine, 'config_static_ip')
    @patch.object(vmware.virtual_machine, 'set_meta')
    @patch.object(vmware, 'Ova')
    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware.virtual_machine, 'deploy_from_ova')
    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, 'vCenter')
    def test_create_dns_static_ip(self, fake_vCenter, fake_consume_task, fake_deploy_from_ova, fake_get_info, fake_Ova, fake_set_meta, fake_config_static_ip):
        """``create_dns`` Sets a static IP"""
        fake_logger = MagicMock()
        fake_deploy_from_ova.return_value.name = 'myDns'
        fake_get_info.return_value = {'worked': True}
        fake_Ova.return_value.networks = ['someLAN']
        fake_vCenter.return_value.__enter__.return_value.networks = {'someLAN' : vmware.vim.Network(moId='1')}


        output = vmware.create_dns(username='alice',
                                       machine_name='DnsBox',
                                       image='1.0.0',
                                       network='someLAN',
                                       static_ip='192.168.1.2',
                                       default_gateway='192.168.1.1',
                                       netmask='255.255.255.0',
                                       dns=['192.168.1.1'],
                                       logger=fake_logger)

        self.assertTrue(fake_config_static_ip.called)

    @patch.object(vmware, 'Ova')
    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware.virtual_machine, 'deploy_from_ova')
    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, 'vCenter')
    def test_create_dns_invalid_network(self, fake_vCenter, fake_consume_task, fake_deploy_from_ova, fake_get_info, fake_Ova):
        """``create_dns`` raises ValueError if supplied with a non-existing network"""
        fake_logger = MagicMock()
        fake_get_info.return_value = {'worked': True}
        fake_Ova.return_value.networks = ['someLAN']
        fake_vCenter.return_value.__enter__.return_value.networks = {'someLAN' : vmware.vim.Network(moId='1')}

        with self.assertRaises(ValueError):
            vmware.create_dns(username='alice',
                                  machine_name='DnsBox',
                                  image='1.0.0',
                                  network='someOtherLAN',
                                  static_ip='192.168.1.2',
                                  default_gateway='192.168.1.1',
                                  netmask='255.255.255.0',
                                  dns=['192.168.1.1'],
                                  logger=fake_logger)

    @patch.object(vmware.os, 'listdir')
    def test_list_images(self, fake_listdir):
        """``list_images`` - Returns a list of available Dns versions that can be deployed"""
        fake_listdir.return_value = ['Windows2019.ova', 'Bind9.ova']

        output = vmware.list_images()
        expected = ['Windows2019', 'Bind9']


        # set() avoids ordering issue in test
        self.assertEqual(set(output), set(expected))

    def test_convert_name(self):
        """``convert_name`` - defaults to converting to the OVA file name"""
        output = vmware.convert_name(name='Bind9')
        expected = 'Bind9.ova'

        self.assertEqual(output, expected)

    def test_convert_name_to_version(self):
        """``convert_name`` - can take a OVA file name, and extract the version from it"""
        output = vmware.convert_name('', to_version=True)
        expected = ''

        self.assertEqual(output, expected)


    @patch.object(vmware.virtual_machine, 'change_network')
    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, 'vCenter')
    def test_update_network(self, fake_vCenter, fake_consume_task, fake_get_info, fake_change_network):
        """``update_network`` Returns None upon success"""
        fake_logger = MagicMock()
        fake_vm = MagicMock()
        fake_vm.name = 'myMachine'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder
        fake_vCenter.return_value.__enter__.return_value.networks = {'wootTown' : 'someNetworkObject'}
        fake_get_info.return_value = {'meta': {'component' : 'Dns'}}

        result = vmware.update_network(username='pat',
                                       machine_name='myMachine',
                                       new_network='wootTown')

        self.assertTrue(result is None)

    @patch.object(vmware.virtual_machine, 'change_network')
    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, 'vCenter')
    def test_update_network_no_vm(self, fake_vCenter, fake_consume_task, fake_get_info, fake_change_network):
        """``update_network`` Raises ValueError if the supplied VM doesn't exist"""
        fake_logger = MagicMock()
        fake_vm = MagicMock()
        fake_vm.name = 'myMachine'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder
        fake_vCenter.return_value.__enter__.return_value.networks = {'wootTown' : 'someNetworkObject'}
        fake_get_info.return_value = {'meta': {'component' : 'InsightIQ'}}

        with self.assertRaises(ValueError):
            vmware.update_network(username='pat',
                                  machine_name='SomeOtherMachine',
                                  new_network='wootTown')

    @patch.object(vmware.virtual_machine, 'change_network')
    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, 'vCenter')
    def test_update_network_no_network(self, fake_vCenter, fake_consume_task, fake_get_info, fake_change_network):
        """``update_network`` Raises ValueError if the supplied new network doesn't exist"""
        fake_logger = MagicMock()
        fake_vm = MagicMock()
        fake_vm.name = 'myMachine'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder
        fake_vCenter.return_value.__enter__.return_value.networks = {'wootTown' : 'someNetworkObject'}
        fake_get_info.return_value = {'meta': {'component' : 'InsightIQ'}}

        with self.assertRaises(ValueError):
            vmware.update_network(username='pat',
                                  machine_name='myMachine',
                                  new_network='dohNet')


if __name__ == '__main__':
    unittest.main()
