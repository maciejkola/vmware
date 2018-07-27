#!/usr/bin/python

# author: mkola

import requests
from requests.auth import HTTPBasicAuth
import sys
import syslog
import argparse
from xml.etree import ElementTree
import time


###############################################################################
# REQUIREMENTS:
# "Virtual CPU hot add" and "Memory hot add" must be checked out in vcloud VM
# properties
###############################################################################

############################ EDIT THOSE LINES ###############################
# vcloud url:
url = ''

# VM ID in vCloud notation:
vApp = ''

# credentials
username_and_org = ''
password = ''

# limit of loop execution to prevent infinite loop
limit=15

# for how long I should wait before starting VM (in restart option)
wait_before_start=15
#############################################################################





def get_token():
        header = {'Accept':'application/*+xml;version=1.5' }
        try:
                response = requests.post(url + '/api/sessions', headers=header, auth=HTTPBasicAuth(username_and_org, password))
        except requests.exceptions.RequestException as e:
                syslog.syslog("Error: %s while getting token" % str(e))
                print("Error: %s while getting token" % str(e))
                sys.exit(1)
        if response.status_code == 200:
                auth_token = response.headers['x-vcloud-authorization']
                return auth_token
        else:
                syslog.syslog("Error: %s, stats code: %s while getting token" % str(response.text), str(response.status_code))
                print("Error: Received %s status code while getting token" % str(response.status_code))
                sys.exit(1)


def get_number_of_CPUs_from_vcloud(token):
        header = {'Accept':'application/*+xml;version=1.5', 'x-vcloud-authorization':token }
        try:
                response = requests.get(url + '/api/vApp/' + vApp + '/virtualHardwareSection/cpu', headers=header)
        except requests.exceptions.RequestException as e:
                syslog.syslog("Error: %s" % str(e))
                print("Error: %s" % str(e))
                sys.exit(1)
        if response.status_code == 200:
                root = ElementTree.fromstring(response.content)
                return root.find('{http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData}VirtualQuantity').text
        else:
                syslog.syslog(str(response.text))
                print("Error: Received %s status code" % str(response.status_code))
                sys.exit(1)



def get_RAM_from_vcloud(token):
        header = {'Accept':'application/*+xml;version=1.5', 'x-vcloud-authorization':token }
        try:
                response = requests.get(url + '/api/vApp/' + vApp + '/virtualHardwareSection/memory', headers=header)
        except requests.exceptions.RequestException as e:
                syslog.syslog("Error: %s" % str(e))
                print("Error: %s" % str(e))
                sys.exit(1)
        if response.status_code == 200:
                root = ElementTree.fromstring(response.content)
                return root.find('{http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData}VirtualQuantity').text
        else:
                syslog.syslog(str(response.text))
                print("Error: Received %s status code" % str(response.status_code))
                sys.exit(1)


def set_number_of_CPUs_in_vcloud(token, number):
        header = {'Accept':'application/*+xml;version=27.0', 'x-vcloud-authorization':token, 'Content-type':'application/vnd.vmware.vcloud.rasdItem+xml' }
        xml = """<?xml version='1.0' encoding='UTF-8'?>
        <Item xmlns='http://www.vmware.com/vcloud/v1.5' xmlns:rasd='http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData' xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xmlns:vcloud='http://www.vmware.com/vcloud/v1.5' vcloud:type='application/vnd.vmware.vcloud.rasdItem+xml' vcloud:href='{1}/api/vApp/{2}/virtualHardwareSection/cpu' xsi:schemaLocation='http://www.vmware.com/vcloud/v1.5 http://{1}/api/v1.5/schema/master.xsd http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2.22.0/CIM_ResourceAllocationSettingData.xsd'>
        <rasd:AllocationUnits>hertz * 10^6</rasd:AllocationUnits>
        <rasd:Description>Number of Virtual CPUs</rasd:Description>
        <rasd:ElementName>1 virtual CPU(s)</rasd:ElementName>
        <rasd:InstanceID>4</rasd:InstanceID>
        <rasd:Reservation>0</rasd:Reservation>
        <rasd:ResourceType>3</rasd:ResourceType>
        <rasd:VirtualQuantity>{0}</rasd:VirtualQuantity>
        <rasd:Weight>0</rasd:Weight>
        <Link rel='edit' href='https://{1}/api/vApp/{2}/virtualHardwareSection/cpu' type='application/vnd.vmware.vcloud.rasdItem+xml'/>
        </Item>"""


        try:
                response = requests.put(url + '/api/vApp/' + vApp + '/virtualHardwareSection/cpu', data=xml.format(number, url, vApp), headers=header)
                #print response.text
        except requests.exceptions.RequestException as e:
                syslog.syslog("Error: %s" % str(e))
                print("Error: %s" % str(e))
                sys.exit(1)
        if response.status_code == 202:
                print("CPU was successfully set to %s") % (number)
                syslog.syslog("CPU was successfully set to %s" % (number))
        else:
                syslog.syslog(str(response.text))
                print("Error: Received %s status code, CPU modification failed." % str(response.status_code))
                sys.exit(1)



def set_RAM_in_vcloud(token, gigabyte_number):
        header = {'Accept':'application/*+xml;version=27.0', 'x-vcloud-authorization':token, 'Content-type':'application/vnd.vmware.vcloud.rasdItem+xml' }
        xml = """<?xml version='1.0' encoding='UTF-8'?>
        <Item xmlns='http://www.vmware.com/vcloud/v1.5' xmlns:rasd='http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData' xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xmlns:vcloud='http://www.vmware.com/vcloud/v1.5' vcloud:type='application/vnd.vmware.vcloud.rasdItem+xml' vcloud:href='{1}/api/vApp/{2}/virtualHardwareSection/cpu' xsi:schemaLocation='http://www.vmware.com/vcloud/v1.5 http://{1}/api/v1.5/schema/master.xsd http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2/CIM_ResourceAllocationSettingData http://schemas.dmtf.org/wbem/wscim/1/cim-schema/2.22.0/CIM_ResourceAllocationSettingData.xsd'>
        <rasd:AllocationUnits>byte * 2^20</rasd:AllocationUnits>
        <rasd:Description>Memory Size</rasd:Description>
        <rasd:ElementName>{0} MB of memory</rasd:ElementName>
        <rasd:InstanceID>5</rasd:InstanceID>
        <rasd:Reservation>0</rasd:Reservation>
        <rasd:ResourceType>4</rasd:ResourceType>
        <rasd:VirtualQuantity>{0}</rasd:VirtualQuantity>
        <rasd:Weight>0</rasd:Weight>
        <Link rel='edit' href='https://{1}/api/vApp/{2}/virtualHardwareSection/memory' type='application/vnd.vmware.vcloud.rasdItem+xml'/>
        </Item>"""


        try:
                response = requests.put(url + '/api/vApp/' + vApp + '/virtualHardwareSection/memory', data=xml.format(gigabyte_number, url, vApp), headers=header)
                #print response.text
        except requests.exceptions.RequestException as e:
                syslog.syslog("Error: %s" % str(e))
                print("Error: %s" % str(e))
                sys.exit(1)
        if response.status_code == 202:
                print("RAM was successfully set to %s MB (%s GB)") % (gigabyte_number, str(conv_MB_to_GB(gigabyte_number)))
                syslog.syslog("RAM was successfully set to %s MB (%s GB)" % (gigabyte_number, str(conv_MB_to_GB(gigabyte_number))))
        else:
                syslog.syslog(str(response.text))
                print("Error: Received %s status code, RAM modification failed." % str(response.status_code))
                sys.exit(1)






def shutdown_vApp(token):
        header = {'Accept':'application/*+xml;version=1.5', 'x-vcloud-authorization':token }
        try:
                response = requests.post(url + '/api/vApp/' + vApp + '/power/action/shutdown', headers=header)
                #print response.text
        except requests.exceptions.RequestException as e:
                syslog.syslog("Error: %s while shutting down VM." % str(e))
                print("Error: %s while shutting down VM." % str(e))
                sys.exit(1)
        if response.status_code == 202:
                print("Shutdown was successful.")
                syslog.syslog("Shutdown was successful.")
        else:
                syslog.syslog(str(response.text))
                print("Error: Received %s status code, shutdown failed." % str(response.status_code))
                sys.exit(1)



def start_vApp(token):
        header = {'Accept':'application/*+xml;version=1.5', 'x-vcloud-authorization':token }
        try:
                response = requests.post(url + '/api/vApp/' + vApp + '/power/action/powerOn', headers=header)
                #print response.text
        except requests.exceptions.RequestException as e:
                syslog.syslog("Error: %s while starting VM." % str(e))
                print("Error: %s while starting VM." % str(e))
                sys.exit(1)
        if response.status_code == 202:
                print("Start of VM: %s was successful" % vApp)
                syslog.syslog("Start of VM: %s was successful" % vApp)
        else:
                syslog.syslog(str(response.text))
                print("Error: Received %s status code, start failed." % str(response.status_code))
                sys.exit(1)


def get_power_state_from_vcloud(token):
        # options: 4 (powered on); 8 (off); 3 (suspended)
        header = {'Accept':'application/*+xml;version=1.5', 'x-vcloud-authorization':token }
        try:
                response = requests.get(url + '/api/vApp/' + vApp, headers=header)
        except requests.exceptions.RequestException as e:
                syslog.syslog("Error: %s while getting power state" % str(e))
                print("Error: %s while getting power state" % str(e))
                sys.exit(1)
        if response.status_code == 200:
                root = ElementTree.fromstring(response.content)
                status = root.attrib.get("status")
                syslog.syslog("Successfuly returned power state: %s" % (str(status)))
                return status
        else:
                syslog.syslog("Error: Received %s with %s status code while checking power state" % (str(response.text), str(response.code)))
                print("Error: Received %s status code while checking power state" % str(response.status_code))
                sys.exit(1)



def conv_MB_to_GB(input_megabyte):
        gigabyte = 1.0/1024
        convert_gb = gigabyte * input_megabyte
        return int(convert_gb)

def conv_GB_to_MB(input_gigabyte):
        megabyte = 1024/1.0
        convert_mb = megabyte * input_gigabyte
        return int(convert_mb)

def get_cpu():
        token = get_token()
        vcloud = get_number_of_CPUs_from_vcloud(token)
        print("Currently VM has:        %s CPU(s)") % (vcloud)

def set_cpu(number):
        token = get_token()
        syslog.syslog('Changing to %s CPU(s), VM: %s.' %(str(number), vApp))
        set_number_of_CPUs_in_vcloud(token, number)


def get_ram():
        token = get_token()
        vcloud = get_RAM_from_vcloud(token)
        giga = conv_MB_to_GB(int(vcloud))
        print("Currently RAM has:        %s MB (%s GB)") % (vcloud, str(giga))

def get_power_status():
        token = get_token()
        status = get_power_state_from_vcloud(token)
        # options: 4 (powered on); 8 (off); 3 (suspended)
        if status == "4":
                print "VM is powered ON"
        if status == "8":
                print "VM is powered OFF"
        if status == "3":
                print "VM is suspended"

def set_ram(number):
        token = get_token()
        syslog.syslog('Changing to %s GB RAM, VM: %s.' %(str(number), vApp))
        gigabyte_number = conv_GB_to_MB(number)
        set_RAM_in_vcloud(token, gigabyte_number)

def set_cpu_restart(number):
        syslog.syslog('VM: %s set_cpu_restart function was called to change number of CPU(s) to %s' %(vApp, str(number)))
        token = get_token()
        existing_number = get_number_of_CPUs_from_vcloud(token)
        syslog.syslog('VM: %s Current number of CPU: %s' %(vApp, existing_number))
        if int(number) < int(existing_number):
                syslog.syslog('VM: %s new value of CPU (%s) is lower then current one (%s)' %(vApp, number, existing_number))
                power_state = get_power_state_from_vcloud(token)
                if power_state != "8":
                        syslog.syslog('VM: %s is not powered off. Executing shutdown...' %(vApp))
                        shutdown_vApp(token)
                        count = 0
                        while True:
                                new_power_state = get_power_state_from_vcloud(token)
                                time.sleep(5)
                                if new_power_state == "8":
                                        syslog.syslog('VM: %s is now powered off.' %(vApp))
                                        syslog.syslog('Changing to %s CPU(s), VM: %s.' %(str(number), vApp))
                                        set_number_of_CPUs_in_vcloud(token, number)
                                        break
                                else:
                                        if count == limit:
                                                syslog.syslog('Error: Timeout was reached while waiting for VM shutdown: %s.' %(vApp))
                                                syslog.syslog('Error: could not change number of CPU(s) on VM: %s to %s' %(vApp, number))
                                                break
                                        syslog.syslog('Attempt: %s / %s' %(count, limit))
                                        syslog.syslog('VM: %s is still running, waiting another 5 sec...' %(vApp))
                                        count = count + 1
                        syslog.syslog('Starting VM: %s .' %(vApp))
                        time.sleep(wait_before_start)
                        start_vApp(token)
                else:
                        syslog.syslog('VM: %s is already powered off.' %(vApp))
                        syslog.syslog('Changing to %s CPU(s), VM: %s.' %(str(number), vApp))
                        set_number_of_CPUs_in_vcloud(token, number)
                        syslog.syslog('Starting VM: %s.' %(vApp))
                        start_vApp(token)
        if int(number) == int(existing_number):
                syslog.syslog('VM: %s : new number of CPU (%s) is the same as existing CPU number (%s). Doing nothing.' %(vApp, number, existing_number))
                print('VM: %s : new number of CPU (%s) is the same as existing CPU number (%s). Doing nothing.' %(vApp, number, existing_number))
                sys.exit(0)
        if int(number) > int(existing_number):
                syslog.syslog('VM: %s new value of CPU (%s) is greater then current one (%s). VM will not be restarted.' %(vApp, number, existing_number))
                set_number_of_CPUs_in_vcloud(token, number)


def set_ram_restart(number):
        syslog.syslog('VM: %s set_ram_restart function was called to change value of RAM to %s GB' %(vApp, number))
        gigabyte_number = conv_GB_to_MB(number)
        token = get_token()
        vcloud = get_RAM_from_vcloud(token)
        existing_number = conv_MB_to_GB(int(vcloud))
        syslog.syslog('VM: %s Current value of RAM: %s GB' %(vApp, existing_number))
        if int(number) < int(existing_number):
                syslog.syslog('VM: %s new value of RAM (%s GB) is lower then current one (%s GB)' %(vApp, number, existing_number))
                power_state = get_power_state_from_vcloud(token)
                if power_state != "8":
                        syslog.syslog('VM: %s is not powered off. Executing shutdown...' %(vApp))
                        shutdown_vApp(token)
                        count = 0
                        while True:
                                new_power_state = get_power_state_from_vcloud(token)
                                time.sleep(5)
                                if new_power_state == "8":
                                        syslog.syslog('VM: %s is now powered off.' %(vApp))
                                        syslog.syslog('Changing to %s GB of RAM, VM: %s.' %(str(number), vApp))
                                        set_RAM_in_vcloud(token, gigabyte_number)
                                        break
                                else:
                                        if count == limit:
                                                syslog.syslog('Error: Timeout was reached while waiting for VM shutdown: %s.' %(vApp))
                                                syslog.syslog('Error: could not change value of RAM on VM: %s to %s' %(vApp, number))
                                                break
                                        syslog.syslog('Attempt: %s / %s' %(count, limit))
                                        syslog.syslog('VM: %s is still running, waiting another 5 sec...' %(vApp))
                                        count = count + 1
                        syslog.syslog('Starting VM: %s .' %(vApp))
                        time.sleep(wait_before_start)
                        start_vApp(token)
                else:
                        syslog.syslog('VM: %s is already powered off.' %(vApp))
                        syslog.syslog('Changing to %s GB RAM, VM: %s.' %(str(number), vApp))
                        set_RAM_in_vcloud(token, gigabyte_number)
                        syslog.syslog('Starting VM: %s.' %(vApp))
                        start_vApp(token)
        if int(number) == int(existing_number):
                syslog.syslog('VM: %s : new value of RAM (%s GB) is the same as existing RAM number (%s GB). Doing nothing.' %(vApp, number, existing_number))
                print('VM: %s : new value of RAM (%s) is the same as existing RAM number (%s). Doing nothing.' %(vApp, number, existing_number))
                sys.exit(0)
        if int(number) > int(existing_number):
                syslog.syslog('VM: %s new value of RAM (%s) is greater then current one (%s). VM will not be restarted.' %(vApp, number, existing_number))
                set_RAM_in_vcloud(token, gigabyte_number)


parser=argparse.ArgumentParser(
    description='''Get/Set number of CPU(s) and RAM. ''',
    epilog="""WARNING: Option '--setCPU/setRAM' requires restart only if number of CPU/RAM was decreased. If you want to change CPU/RAM with automatic restart, use '--setCPUrestart/setRAMrestart' options. With this option script will check if restart is necessary. BE CAREFUL because script won't prompt you for permission before restart.""")
parser.add_argument('--getCPU', action='store_true', help='Get number of CPU(s)')
parser.add_argument('--getRAM', action='store_true', help='Get number of RAM')
parser.add_argument('--setCPU', type=int, choices=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24], help='Set number of CPU(s); for example --setCPU 2')
parser.add_argument('--setRAM', type=int, choices=[1,2,4,8,16,32,64], help='Set number of RAM in GB; for example --setRAM 2')
parser.add_argument('--setCPUrestart', type=int, choices=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24], help='Set number of CPU(s); for example --setCPU 2')
parser.add_argument('--setRAMrestart', type=int, choices=[1,2,4,8,16,32,64], help='Set number of RAM in GB; for example --setRAM 2')
parser.add_argument('--shutdown', action='store_true', help='Shutdown VM')
parser.add_argument('--start', action='store_true', help='Start VM')
parser.add_argument('--status', action='store_true', help='Get VM power status')
args=parser.parse_args()

if not len(sys.argv) > 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

if args.getCPU:
        get_cpu()

if args.getRAM:
        get_ram()

if args.setCPU:
        set_cpu(args.setCPU)

if args.setRAM:
        set_ram(args.setRAM)

if args.shutdown:
        token = get_token()
        syslog.syslog('Shutting down VM: %s.' %(vApp))
        shutdown_vApp(token)

if args.start:
        token = get_token()
        syslog.syslog('Starting VM: %s.' %(vApp))
        start_vApp(token)

if args.setCPUrestart:
        set_cpu_restart(args.setCPUrestart)

if args.setRAMrestart:
        set_ram_restart(args.setRAMrestart)

if args.status:
        get_power_status()
