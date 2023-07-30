#!/usr/bin/env python3

import libvirt
import json
import re

def get_vm_ips(vm):
    ips = []
    if vm.isActive():
        domain = vm.name()
        try:
            ifaces = vm.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_AGENT, 0)
            for (name, val) in ifaces.items():
                if val['addrs']:
                    for addr in val['addrs']:
                        ips.append(addr['addr'])
        except libvirt.libvirtError as e:
            print(f"Error getting IP for domain {domain}: {e}")
    return ips

def get_libvirt_vms():
    try:
        # Connect to the remote libvirt daemon using its URI
        uri = 'qemu+ssh://root@10.0.0.73/system'
        conn = libvirt.open(uri)
        if conn is None:
            raise Exception("Failed to connect to the remote libvirt hypervisor.")
        
        # Get the list of all defined domains (VMs)
        vm_list = conn.listAllDomains()
        return vm_list
    except Exception as e:
        print(f"Error fetching libvirt VMs: {e}")
        return []

def main():
    vms = get_libvirt_vms()
    inventory = {
        '_meta': {
            'hostvars': {}
        },
        'all': {
            'hosts': [],
            'vars': {}
        }
    }
    for vm in vms:
        vm_name = vm.name()
        vm_status = vm.isActive()
        # You can customize the group mapping based on your VM naming conventions or other criteria.
        groups = ['libvirt_vms']
        if vm_status:
            groups.append('running')
        else:
            groups.append('stopped')
        
        # Add the VM to the 'all' group as well
        groups.append('all')

        # Add the VM to the specific group(s)
        for group in groups:
            if group not in inventory:
                inventory[group] = {'hosts': []}
            inventory[group]['hosts'].append(vm_name)

        # Get IP addresses of the VM and add them as host variables
        vm_ips = get_vm_ips(vm)
        inventory['_meta']['hostvars'][vm_name] = {
            'ansible_host': vm_ips,
            # Add other host variables as needed
        }
    
    print(json.dumps(inventory, indent=1))

if __name__ == "__main__":
    main()
