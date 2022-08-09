#!/bin/env python3
from collections import namedtuple
from pydoc import describe
import sys
from tkinter import E
from webbrowser import get
import requests
import json
import urllib3
import ssl

'''
Script: Create Service Now Incidents
Creator: amp473
Description:
    This script will create Service Now incidents with information given. 
    It take in the following parameters:
    server_list = list(sys.argv[1].split(','))
    short_desc = sys.argv[2]
    bus_service = sys.argv[3]
    long_desc = sys.argv[4]
    Given the list of servers, it will determine the appropriate parameters to send
    to Service now such as environment, ownership, priority, etc.
'''

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context


snow_url = "https://dev-servicenow.sherwin.com"

# Create VM object to make things easier for myself.
class config_item:

    # Set a dictionary for one of the vm's to do general logic.
    def setChecker(self,server_stuff):
        self._one = next(iter(server_stuff.values()))
        
    def getChecker(self):
        return self._one
    
    # Creates our list of servers with correct class information
    def setList(self,server_stuff):
        self._list = server_stuff
        return self._list

    def getList (self):
        return self._list

    # Calculates the priority based on the environment for that configuration item.
    def calcPriority(self):
        # For linux, High and Crit priority alerts will send everbridge events.
        env = self.getChecker()['environment']
        inc_things = {}
        if env == "Development":
            inc_things['impact'] = 3
            inc_things['urgency'] = 2
        elif env == "QA":
            inc_things['impact'] = 2
            inc_things['urgency'] = 2
        elif env == "Production":
            inc_things['impact'] = 1
            inc_things['urgency'] = 1
        self._priority = inc_things
        return self._priority

    def getPriority(self):
        return self._priority

# Asks for a dictionary but will create an object from a dictionary for easy use.
def objTup(my_dict):
    return namedtuple("ObjectName", my_dict.keys())(*my_dict.values())

# Grabs the configuration item for what was passed in and returns the correct class information.
def getServCI(serv):
    url = snow_url+"/api/now/table/cmdb_ci?name="+serv

    headers = {
        'Authorization': 'Basic c25fd3NfZ29zY19saW51eDpLMVYmQmJBR2oyVHE',
        'Content-Type':'application/json',
        "Accept":"application/json"
    }
    
    response = requests.get(url,headers=headers)
    j_response = json.loads(response.text)
    serv_dict = j_response['result'][0]

    url = snow_url+"/api/now/table/"+serv_dict['sys_class_name']+"?name="+serv

    headers = {
        'Authorization': 'Basic c25fd3NfZ29zY19saW51eDpLMVYmQmJBR2oyVHE',
        'Content-Type':'application/json',
        "Accept":"application/json"
    }
    
    response2 = requests.get(url,headers=headers)
    j_response2 = json.loads(response2.text)
    serv_dict2 = j_response2['result'][0]

    return serv_dict2

''' Creates an incident with various parameters. If there is more than 1 server that was passed in, 
    update that ticket and add the rest of the servers to the affected CI's area of the incident.
'''
def createInc(vm,short_desc,long_desc,bus_service):
    dictTup = objTup(vm.getChecker())
    url = snow_url+"/api/now/table/incident"

    headers = {
        'Authorization': 'Basic c25fd3NfZ29zY19saW51eDpLMVYmQmJBR2oyVHE',
        'Content-Type':'application/json',
        "Accept":"application/json"
    }
    vm_priority = vm.getPriority()

    payload = {
        'short_description': short_desc,
        'description': long_desc,
        'business_service': bus_service,
        'assignment_group': dictTup.support_group['value'],
        'urgency': vm_priority['urgency'],
        'impact': vm_priority['impact'],
        'location': dictTup.location['value'],
        'cmdb_ci':dictTup.name,
        'contact_type': 'direct input',
        'category':'site'
    }
    
    
    response = requests.post(url,headers=headers,json=payload)

    j_response = json.loads(response.text)

    vm_list = vm.getList()

    if len(vm_list) > 1:
        url = snow_url+"/api/now/table/task_ci"
        for key in vm_list:
            
            payload = {
                'task':  j_response['result']['sys_id'],
                'ci_item': key
            }

            put_response = requests.post(url,headers=headers,json=payload)

    return j_response['result']['number']

# Main
def main():
    print("starttttttt")

    #server_list = list(sys.argv[1].split(','))
    #short_desc = sys.argv[2]
    #bus_service = sys.argv[3]
    #long_desc = sys.argv[4]

    server_list = list("cgccrptadmin01d".split(','))
    short_desc = "patching failed"
    bus_service = "Linux OS Patching"
    long_desc = ""
    server_stuff = {}

    
    for serv in server_list:
        gimmethis = getServCI(serv)
        server_stuff[serv] = gimmethis
    vm = config_item()
    vm.setList(server_stuff)
    vm.setChecker(server_stuff)

    vm.calcPriority()
    createInc(vm,short_desc,long_desc,bus_service)
 
    print("END")



if __name__ == "__main__":
    main()
