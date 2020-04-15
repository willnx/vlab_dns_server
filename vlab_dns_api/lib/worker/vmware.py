# -*- coding: UTF-8 -*-
"""Business logic for backend worker tasks"""
import time
import random
import os.path
from vlab_inf_common.vmware import vCenter, Ova, vim, virtual_machine, consume_task

from vlab_dns_api.lib import const


def show_dns(username):
    """Obtain basic information about Dns

    :Returns: Dictionary

    :param username: The user requesting info about their Dns
    :type username: String
    """
    info = {}
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER, \
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        folder = vcenter.get_by_name(name=username, vimtype=vim.Folder)
        dns_vms = {}
        for vm in folder.childEntity:
            info = virtual_machine.get_info(vcenter, vm, username)
            if info['meta']['component'] == 'Dns':
                dns_vms[vm.name] = info
    return dns_vms


def delete_dns(username, machine_name, logger):
    """Unregister and destroy a user's Dns

    :Returns: None

    :param username: The user who wants to delete their jumpbox
    :type username: String

    :param machine_name: The name of the VM to delete
    :type machine_name: String

    :param logger: An object for logging messages
    :type logger: logging.LoggerAdapter
    """
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER, \
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        folder = vcenter.get_by_name(name=username, vimtype=vim.Folder)
        for entity in folder.childEntity:
            if entity.name == machine_name:
                info = virtual_machine.get_info(vcenter, entity, username)
                if info['meta']['component'] == 'Dns':
                    logger.debug('powering off VM')
                    virtual_machine.power(entity, state='off')
                    delete_task = entity.Destroy_Task()
                    logger.debug('blocking while VM is being destroyed')
                    consume_task(delete_task)
                    break
        else:
            raise ValueError('No {} named {} found'.format('dns', machine_name))


def create_dns(username, machine_name, image, network, static_ip, default_gateway, netmask, dns, logger):
    """Deploy a new instance of Dns

    :Returns: Dictionary

    :param username: The name of the user who wants to create a new Dns
    :type username: String

    :param machine_name: The name of the new instance of Dns
    :type machine_name: String

    :param image: The image/version of Dns to create
    :type image: String

    :param network: The name of the network to connect the new Dns instance up to
    :type network: String

    :param static_ip: The IPv4 address to assign to the VM
    :type static_ip: String

    :param default_gateway: The IPv4 address of the network gateway
    :type default_gateway: String

    :param netmask: The subnet mask of the network, i.e. 255.255.255.0
    :type netmask: String

    :param dns: A list of DNS servers to use.
    :type dns: List

    :param logger: An object for logging messages
    :type logger: logging.LoggerAdapter
    """
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER,
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        image_name = convert_name(image)
        logger.info(image_name)
        ova = Ova(os.path.join(const.VLAB_DNS_IMAGES_DIR, image_name))
        try:
            network_map = vim.OvfManager.NetworkMapping()
            network_map.name = ova.networks[0]
            try:
                network_map.network = vcenter.networks[network]
            except KeyError:
                raise ValueError('No such network named {}'.format(network))
            the_vm = virtual_machine.deploy_from_ova(vcenter, ova, [network_map],
                                                     username, machine_name, logger)
        finally:
            ova.close()

        meta_data = {'component' : "Dns",
                     'created' : time.time(),
                     'version' : image,
                     'configured' : False,
                     'generation' : 1}
        virtual_machine.set_meta(the_vm, meta_data)

        if image.lower().startswith('windows'):
            vm_user, vm_password, the_os = const.VLAB_DNS_WINDOWS_ADMIN, const.VLAB_DNS_WINDOWS_PW, 'windows'
        else:
            vm_user, vm_password, the_os = const.VLAB_DNS_BIND9_ADMIN, const.VLAB_DNS_BIND9_PW, 'centos8'
        virtual_machine.config_static_ip(vcenter,
                                         the_vm,
                                         static_ip,
                                         default_gateway,
                                         netmask,
                                         dns,
                                         vm_user,
                                         vm_password,
                                         logger,
                                         os=the_os)
        if the_os == 'centos8':
            _finish_bind_config(vcenter, the_vm, static_ip, logger)

        info = virtual_machine.get_info(vcenter, the_vm, username, ensure_ip=True)
        return  {the_vm.name: info}


def list_images():
    """Obtain a list of available versions of Dns that can be created

    :Returns: List
    """
    images = os.listdir(const.VLAB_DNS_IMAGES_DIR)
    images = [convert_name(x, to_version=True) for x in images]
    return images


def convert_name(name, to_version=False):
    """This function centralizes converting between the name of the OVA, and the
    version of software it contains.

    :param name: The thing to covert
    :type name: String

    :param to_version: Set to True to covert the name of an OVA to the version
    :type to_version: Boolean
    """
    if to_version:
        return os.path.splitext(name)[0]
    else:
        return '{}.ova'.format(name)


def update_network(username, machine_name, new_network):
    """Implements the VM network update

    :param username: The name of the user who owns the virtual machine
    :type username: String

    :param machine_name: The name of the virtual machine
    :type machine_name: String

    :param new_network: The name of the new network to connect the VM to
    :type new_network: String
    """
    with vCenter(host=const.INF_VCENTER_SERVER, user=const.INF_VCENTER_USER, \
                 password=const.INF_VCENTER_PASSWORD) as vcenter:
        folder = vcenter.get_by_name(name=username, vimtype=vim.Folder)
        for entity in folder.childEntity:
            if entity.name == machine_name:
                info = virtual_machine.get_info(vcenter, entity, username)
                if info['meta']['component'] == 'Dns':
                    the_vm = entity
                    break
        else:
            error = 'No VM named {} found'.format(machine_name)
            raise ValueError(error)

        try:
            network = vcenter.networks[new_network]
        except KeyError:
            error = 'No VM named {} found'.format(machine_name)
            raise ValueError(error)
        else:
            virtual_machine.change_network(the_vm, network)


def _finish_bind_config(vcenter, the_vm, static_ip, logger):
    """The records for Bind need to be adjust for the user's specific hostname and IP

    :Returns: None

    :param vcenter: The vCenter object
    :type vcenter: vlab_inf_common.vmware.vcenter.vCenter

    :param the_vm: The pyVmomi Virtual machine object
    :type the_vm: vim.VirtualMachine

    :param static_ip: The IP of the DNS server
    :type static_ip: String

    :param logger: An object for logging messages
    :type logger: logging.LoggerAdapter
    """
    sed = '/usr/bin/sed'
    args = "-i 's/{}/{}/g' {}"
    forward_zone_file = '/var/named/vlab.local.db'
    reverse_zone_file = '/var/named/vlab.local.rev'

    forward_args1 = args.format('CHANGEME', static_ip, forward_zone_file)
    forward_args2 = args.format('4\t', '5\t', forward_zone_file) # change the serial value
    reverse_args1 = args.format('CHANGEME', static_ip, reverse_zone_file)
    reverse_args2 = args.format('4\t', '5\t', reverse_zone_file) # change the serial value

    systemctl = '/usr/bin/systemctl'
    restart = 'restart named'

    logger.info("Adjusting the Forward Lookup records for BIND")
    virtual_machine.run_command(vcenter, the_vm, sed, arguments=forward_args1, user=const.VLAB_DNS_BIND9_ADMIN, password=const.VLAB_DNS_BIND9_PW)
    virtual_machine.run_command(vcenter, the_vm, sed, arguments=forward_args2, user=const.VLAB_DNS_BIND9_ADMIN, password=const.VLAB_DNS_BIND9_PW)
    logger.info("Adjusting the Reverse Lookup records for BIND")
    virtual_machine.run_command(vcenter, the_vm, sed, arguments=reverse_args1, user=const.VLAB_DNS_BIND9_ADMIN, password=const.VLAB_DNS_BIND9_PW)
    virtual_machine.run_command(vcenter, the_vm, sed, arguments=reverse_args2, user=const.VLAB_DNS_BIND9_ADMIN, password=const.VLAB_DNS_BIND9_PW)
    logger.info("Restarting named service")
    virtual_machine.run_command(vcenter, the_vm, systemctl, arguments=restart, user=const.VLAB_DNS_BIND9_ADMIN, password=const.VLAB_DNS_BIND9_PW)
