#!/usr/bin/env python

#Stackstorm action Module
from lib.base_action import BaseAction

#API Request Module
import requests

#DateTime Module
import pytz
from datetime import datetime, timedelta

#Email Modules
import smtplib
import email.utils
from email.mime.text import MIMEText

#Json Module
import json

#sleep module
from time import sleep

class AutomoxPatchChangeCreationv1(BaseAction):
    def __init__(self, config):
        """Creates a new Action given a StackStorm config object (kwargs works too)
        :param config: StackStorm configuration object for the pack
        :returns: a new Action
        """
        super(AutomoxPatchChangeCreationv1, self).__init__(config)

    def run(self, daysinfuture, automox_apikey, automox_username, automox_password, automox_orgid, customername, companyname, change_payload_email, receiver_email):
        daysinfuture = daysinfuture # need to pass an external input named daysinfuture and assign it to daysinfuture variable here
        apikey = automox_apikey
        orgid = automox_orgid # needs to be changed as per Customer OrgID 17238 for HYG Windows | 17239 for HYG Linux
        customername = customername
        companyname = companyname
        servervalidate = []
        serverlist = []
        #automoxapi = "https://console.automox.com/api/orgs?api_key=" + apikey
        automoxapigroup = "https://console.automox.com/api/servergroups?o=" + orgid + "&api_key=" + apikey
        #automoxapiserver = "https://console.automox.com/api/servers?o=" + orgid + "&api_key=" + apikey + "&l=500" + "&p=0"
        #automoxapipolicy = "https://console.automox.com/api/policies/" + selectedpolicy + ?o=" + orgid + "&api_key=" + apikey

        #automox credentials
        user = automox_username
        pass1 = automox_password

        #get the server details and store in a variable
        for pagecount in range(0,10):
            #print("Getting the server list from page {}".format(pagecount))
            automoxapiserver = "https://console.automox.com/api/servers?o=" + orgid + "&api_key=" + apikey + "&l=500" + "&p=" + str(pagecount)
            serverlistraw = requests.get(automoxapiserver, auth=('user', 'pass1'))
            serverlistresult = (serverlistraw.json())["results"]
            servercount= len(serverlistresult)
            #print("Page Number, Length of Server List: ",str(pagecount), len(serverlistresult))
            serverlist = serverlist + serverlistresult
            if servercount < 500:
                break
        #print("Length of Server List: ", len(serverlist))
        for server in serverlist:
            if server["next_patch_time"]:
                print(server["name"], server["next_patch_time"])
        #group and policy extraction and validation
        groupdata = requests.get(automoxapigroup, auth=('user', 'pass1'))
        groupdatajson = groupdata.json()
        allgroupdata = []
        servergroupids = []
        for group in groupdatajson:
            #print(group["name"], group["server_count"], group["notes"])
            #print("="*50)
            if "###GROUPS###" in group["notes"] and group["server_count"] > 0:
                #print("=====================Notes valid=========================")
                groupdataindividual = {}
                for field in group:
                    groupdataindividual[field] = group[field]
                    #print(field, ": ", group[field])
                    if field == "wsus_config":
                        servergroupids.append(group[field]["server_group_id"])
                #print(groupdataindividual)
                allgroupdata.append(groupdataindividual)
        #print(allgroupdata)
        print(servergroupids)

        #iterating through each group and each policy inside the group
        groupcount = 0
        transferdetails = []
        servernotincmdb = []
        changescreated = []
        activepatchingpolicy = 0
        for eachgroup in allgroupdata:
            #print("Each Group Data")
            #print(eachgroup)
            grouppolicies = eachgroup["policies"]
            groupid = eachgroup["id"]
            groupname = eachgroup["name"]
            groupnotes = eachgroup["notes"]
            #servernotincmdb = []
            #changescreated = []
            print("=========== Group Name: {} and Id: {} ==============".format(groupname, groupid))
            print(grouppolicies)
            activepatchingpolicy = 0
            for selectedpolicy in grouppolicies:
                #print(selectedpolicy)
                automoxapipolicy = "https://console.automox.com/api/policies/" + str(selectedpolicy) + "?o=" + orgid + "&api_key=" + apikey
                #print(automoxapipolicy)
                policydata = requests.get(automoxapipolicy, auth=('user', 'pass1'))
                policydatajson = policydata.json()
                #print(policydatajson)
                policyid = policydatajson["id"]
                policyname = policydatajson["name"]
                print(policyid, policyname)
                #print(policydatajson["configuration"])
                try:
                    # changing auto_reboot value to False for testing, revert it to True which is the original condition
                    print(policydatajson["configuration"]["auto_patch"] == True and policydatajson["configuration"]["auto_reboot"] == True and policydatajson["policy_type_name"] == "patch" and policydatajson["server_count"] > 0)
                    print(policydatajson["configuration"]["auto_patch"], policydatajson["configuration"]["auto_reboot"], policydatajson["policy_type_name"], policydatajson["server_count"])
                    if policydatajson["configuration"]["auto_patch"] == True and policydatajson["configuration"]["auto_reboot"] == True and policydatajson["policy_type_name"] == "patch" and policydatajson["server_count"] > 0:
                        print("Active Patching Policy ID : ", policyid, "Policy Name : ", policyname)
                        activepatchingpolicy = activepatchingpolicy + 1
                        # checking next patch date and if the next patch date is 3 days ahead proceeding with change creation
                        for server in serverlist:
                            servername = server["name"]
                            servertransferdetails = {}
                            serverstoignore = ["AAMRICOH", "AFTCMAZRGTWYTST", "AFTCMIIS01", "AFTCMTELEMDIT", "AMMMFG02", "CLMPRT", "CPMAPPS6", "CPMAPPS8", "CPMFORUM", "CPMRM1", "ENMFSC03"]
                            if server in serverstoignore:
                                continue
                            #
                            #
                            #if server["name"] == "KYFTCPNTTJMP01" and groupid == server["server_group_id"]:
                            if server["next_patch_time"] and groupid == server["server_group_id"]: # need to be uncommented while testing live data
                                if server["name"] in servervalidate:
                                    print("Already worked on Server ", server["name"])
                                    servervalidationcheck = 0
                                    continue
                                else:
                                    print("Working on Server ", server["name"])
                                    #servervalidate.append(server["name"])
                                    servervalidationcheck = 1
                                print("Server Next Patch time is present: ", server["next_patch_time"], server["name"])
                                timesplit = server["next_patch_time"].split("-")
                                #snpt = "2022-08-21T23:00:00+0000" # These 3 lines should be removed/commented while testing with live data
                                #print("Server Next Patch time is present: ", snpt)
                                #timesplit = snpt.split("-")
                                time1 = timesplit[2].split("T")[1].split(":")
                                servernextpatchtime = datetime(int(timesplit[0]),int(timesplit[1]),int(timesplit[2].split("T")[0]),int(time1[0]), int(time1[1]), int(time1[2].split("+")[0]))
                                print(servernextpatchtime)
                                timediff = servernextpatchtime.astimezone(pytz.timezone('GMT')) - (datetime.now()).astimezone(pytz.timezone('GMT'))
                                print("time difference: ", timediff)
                                #print(servervalidate)
                                if timediff.days == daysinfuture and servervalidationcheck == 1:
                                    servervalidate.append(server["name"])
                                    print("Next Patch window is {} which is {} days away from today".format(servernextpatchtime.astimezone(pytz.timezone('GMT')), daysinfuture))
                                    #checking the server and server status (it should be in opertaional status) in cmdb
                                    #servername = server["name"]
                                    print("checking the ", servername," and server status - it should be in opertaional status - in cmdb")
                                    self.sn_username = self.config['servicenow']['username']
                                    self.sn_password = self.config['servicenow']['password']
                                    # change the below URL while moveing to Production
                                    cmdb_ci_check_api = "https://nttds.service-now.com/api/now/table/cmdb_ci?sysparm_query=name=" + servername + "^install_status=4"
                                    self.servicenow_headers = {'Content-type': 'application/json','Accept': 'application/json'}
                                    serverbooleanresult = 0
                                    try:
                                        cmdb_ci_result = requests.request('GET', cmdb_ci_check_api, auth=(self.sn_username, self.sn_password), headers=self.servicenow_headers)
                                        print(cmdb_ci_result.text)
                                        result = cmdb_ci_result.text
                                        print("This is length of result: ", len((cmdb_ci_result.json())["result"]))
                                        resultlength = len((cmdb_ci_result.json())["result"])
                                        if resultlength > 0:
                                            print("Server is available in CMDB and it is Operational")
                                            serverbooleanresult = 1
                                    except:
                                        print("An error occurred while connecting to CMDB")
                                    else:
                                        print("Server {} is either not available or not Operational in CMDB".format(servername))

                                    if serverbooleanresult == 1:
                                        # getting the payload ready
                                        shortdescription = "[TR - Automation] Patching " + server["name"] + ", Windows"
                                        #startdate = str(servernextpatchtime.astimezone(pytz.timezone('GMT')))
                                        startdate = str(servernextpatchtime)
                                        print(startdate)
                                        #enddate =str((servernextpatchtime + timedelta(hours=24)).astimezone(pytz.timezone('GMT')))
                                        enddate =str((servernextpatchtime + timedelta(hours=8)))
                                        print(enddate)
                                        ########## Get the details from Groupnotes ############
                                        if "PrimaryChangeNumber" in groupnotes:
                                            PrimaryChangeNumber = groupnotes.split("###CHANGE###")[1].split(":")[1].strip()
                                            print(PrimaryChangeNumber)
                                            shortdescription = "[TR - Automation] Patching " + server["name"] + ", Windows , PrimaryChangeNumber:  " + PrimaryChangeNumber
                                        else:
                                            print("PrimaryChangeNumber is not available in groupnotes")
                                        if "GROUPS" in groupnotes:
                                            ASSIGNMENTGROUP = groupnotes.split("###GROUPS###")[1].split(":")[1].split("\n")[0].strip()
                                            CHANGEMANAGEMENT = groupnotes.split("###GROUPS###")[1].split(":")[2].split("\n")[0].strip()
                                            print(ASSIGNMENTGROUP)
                                            print(CHANGEMANAGEMENT)
                                            servertransferdetails.update({"assignment_group":ASSIGNMENTGROUP, "u_change_management_group":CHANGEMANAGEMENT})
                                        else:
                                            print("GROUPS is not available in groupnotes")
                                        if "EMAIL" in groupnotes:
                                            if "APPVERIFICATION" in groupnotes and "CHANGECREATIONISSUE" in groupnotes:
                                                APPVERIFICATION = groupnotes.split("###EMAIL###")[1].split(":")[1].split("\n")[0].strip()
                                                CHANGECREATIONISSUE = groupnotes.split("###EMAIL###")[1].split(":")[2].strip()
                                                print(APPVERIFICATION)
                                                print(CHANGECREATIONISSUE)
                                            elif "CHANGECREATIONISSUE" in groupnotes:
                                                CHANGECREATIONISSUE = groupnotes.split("###EMAIL###")[1].split(":")[1].split("\n")[0].strip()
                                                print(CHANGECREATIONISSUE)
                                        else:
                                            print("EMAIL is not available in groupnotes")
                                        ############## end of Groupnotes data extraction #############
                                        servertransferdetails.update({"servername":server["name"], "start_date":startdate, "end_date":enddate, "expected_start":startdate, "shortdescription":shortdescription, "description":groupnotes})
                                        ###### adding change creation part ######

                                        endpoint = '/api/sn_chg_rest/v1/change/normal?'
                                        test_plan="""Verify system availability
Verify successful patch installation
Generate Patch compliance report
Turn over server to POC for application validation"""
                                        description = """What is this change for?
This change is the regularly scheduled compliance patching of this server

This change was approved under the parent change Nucleus Patching Automation ("""+ customername +""" - Windows) and (PROD Servers)The server will be unavailable during the restart of the server.
This change is scheduled during the approved patching window

""" + groupnotes
                                        backout_plan="""In the event that a system or application becomes unavailable, the offending patch will be uninstalled.
If uninstalling the patch does not restore services, the server will be restored from backup following documented DR plans."""
                                        work_notes='This is a change created with automation'
                                        change_plan=description
                                        payload = {
                                                'start_date': startdate,
                                                'state': 1,
                                                'assigned_to': 'Automation Service',
                                                #'assignment_group':'ARC-CM Approvers',
                                                'assignment_group': ASSIGNMENTGROUP,
                                                'backout_plan': backout_plan,
                                                'category': 'Perform',
                                                'change_plan': change_plan,
                                                'cmdb_ci': server["name"],
                                                'company': companyname,
                                                'contact_type': 'email',
                                                'end_date': enddate,
                                                'expected_start': startdate,
                                                'implementation_plan': 'Test',
                                                'justification': 'justification',
                                                'risk': 4,
                                                'test_plan': test_plan,
                                                'type': 'Normal',
                                                'u_change_management_group': CHANGEMANAGEMENT,
                                                'work_notes': work_notes,
                                                'short_description': shortdescription,
                                                'description': description,
                                                'approval': 'approved',
                                                'u_req_by_email': change_payload_email,
                                                'impact': 3,
                                                'u_change_environment': 'Production',
                                                'u_subcategory': 'Restart Scheduled Maintenance',
                                                'u_is_incident_suppression_requ': 'true',
                                                'u_change_reason': 'Maintenance',
                                                'u_suppression_start': startdate,
                                                'u_suppression_end': enddate,
                                                'u_validation_time': '01:00:00',
                                                'u_backout_time': '01:00:00',
                                                "u_implementation_time": "06:00:00",
                                                "u_total_change_time": "08:00:00"
                                                 }
                                        print("Change creation payload: ", payload)
                                        change = self.sn_api_call('POST', endpoint, payload=payload)
                                        #print(change["number"]["value"])
                                        createdchangenumber = change["number"]["value"]
                                        print(createdchangenumber)
                                        sleep(2)
                                        # First step of change approval Request
                                        endpoint1 = '/api/dems/ebonding_change_automation/changeAutomation'
                                        payload1 = {"company":companyname,"number":createdchangenumber,"request_approval":"Yes"}
                                        #payload1 = {"company":companyname,"number":'CHG0571171',"request_approval":"Yes"}
                                        change1 = self.sn_api_call('POST', endpoint1, payload=payload1)
                                        print(change1)
                                        sleep(3)
                                        # Second Step of change approval
                                        endpoint2 = '/api/dems/ebonding_change_automation/changeAutomation'
                                        payload2 = {"company":companyname,"number":createdchangenumber,"approval":"Approve"}
                                        #payload2 = {"company":companyname,"number":'CHG0571171',"approval":"Approve"}
                                        change2 = self.sn_api_call('POST', endpoint2, payload=payload2)
                                        print(change2)
                                        sleep(5)

                                        # Next step of change approval Request
                                        endpoint3 = '/api/dems/ebonding_change_automation/changeAutomation'
                                        payload3 = {"company":companyname,"number":createdchangenumber,"request_approval":"Yes"}
                                        #payload3 = {"company":companyname,"number":'CHG0571176',"request_approval":"Yes"}
                                        change3 = self.sn_api_call('POST', endpoint3, payload=payload3)
                                        print(change3)

                                        sleep(5)

                                        # Next Step of change approval
                                        endpoint4 = '/api/dems/ebonding_change_automation/changeAutomation'
                                        payload4 = {"company":companyname,"number":createdchangenumber,"approval":"Approve"}
                                        #payload4 = {"company":companyname,"number":'CHG0571176',"approval":"Approve"}
                                        change4 = self.sn_api_call('POST', endpoint4, payload=payload4)
                                        print(change4)

                                        changenumberandserver = change["number"]["value"] + " : " + servername
                                        print(changenumberandserver)
                                        changescreated.append(changenumberandserver)
                                        print(changescreated)
                                        ######## end of change creation ##########
                                        print(servertransferdetails)
                                    else:
                                        servernotincmdbformat = '('+ servername +') not in operational status for ('+companyname+')'
                                        servernotincmdb.append(servernotincmdbformat)
                            if servertransferdetails:
                                transferdetails.append(servertransferdetails)
                except KeyError as KE:
                    print("Keyerror in policy : ",policyid, policyname)
                    print(KE)
                else:
                    print("one of the condition is not satisfied: " , policydatajson["configuration"]["auto_patch"], policydatajson["configuration"]["auto_reboot"], policydatajson["policy_type_name"],  policydatajson["server_count"])

            #Send Email after each group with the changes created and not created

            port = 25
            smtp_server = "155.16.123.161"
            sender_email = "noreply@nttdata.com"
            receiver_email = receiver_email
            password = ''
            if len(changescreated) > 0 and len(servernotincmdb) == 0:
                #Send Email with the changes created and not created due to issues

                messagebody = """
Nucleus Patching Automation Change Creation: All changes created for ("""+ companyname +""" - Windows) group ("""+ groupname +""")

Changes created: """+ str(len(changescreated)) +"""

"""+ '\n'.join(changescreated) +"""

This automated message was sent to you at: """ + str((datetime.now()).astimezone(pytz.timezone('GMT'))) + """."""
                message = MIMEText(messagebody)
                message['TO'] = email.utils.formataddr(('Recipient', receiver_email))
                message['From'] = email.utils.formataddr(('Nucleus Patching Automation', sender_email))
                message['Subject'] = 'Nucleus Patching Automation Change Creation: All changes created for ('+ companyname +' - Windows) group ('+ groupname +')'

            elif len(changescreated) > 0 and len(servernotincmdb) > 0:
                #Send Email with the changes created and not created due to issues

                messagebody = """
Nucleus Patching Automation Change Creation: Issues with (""" + companyname + """- Windows) group ("""+ groupname +""")

Changes created: """+ str(len(changescreated)) +"""

Issues with servers detailed below:
Server Name: """+ '\n'.join(servernotincmdb) +"""

Changes created:
"""+ '\n'.join(changescreated) +"""

This automated message was sent to you at: """ + str((datetime.now()).astimezone(pytz.timezone('GMT'))) + """."""
                message = MIMEText(messagebody)
                message['TO'] = email.utils.formataddr(('Recipient', receiver_email))
                message['From'] = email.utils.formataddr(('Nucleus Patching Automation', sender_email))
                message['Subject'] = 'Nucleus Patching Automation Change Creation: Issues with ('+ companyname +' - Windows) group ('+ groupname +')'
            else:
                #Send Email with the changes created and not created due to issues

                messagebody = """
Nucleus Patching Automation Change Creation: No Changes Created for (""" + companyname + """- Windows) group ("""+ groupname +""")

This automated message was sent to you at: """ + str((datetime.now()).astimezone(pytz.timezone('GMT'))) + """."""
                message = MIMEText(messagebody)
                message['TO'] = email.utils.formataddr(('Recipient', receiver_email))
                message['From'] = email.utils.formataddr(('Nucleus Patching Automation', sender_email))
                message['Subject'] = 'Nucleus Patching Automation Change Creation: No Changes Created for ('+ companyname + '- Windows) group ('+ groupname +')'

            server = smtplib.SMTP(smtp_server, port)
            server.set_debuglevel(True)
            if len(changescreated) > 0:
                try:
                    server.sendmail(sender_email, [receiver_email], message.as_string())
                finally:
                    server.quit()
            else:
                print("No changes created in this group: ", groupname)

            if activepatchingpolicy > 0:
                groupcount = groupcount + 1
                #"There are activepatchingpolicy active patching policies applied to this group"
                print("Patching group id : ", groupid, "Notes-", groupid, " : ", policydatajson["notes"], "Name-", groupid, " : ", groupname)
            print("Changes created: ", changescreated , "server not in cmdb: ", servernotincmdb , "groupcount: ", groupcount, "policycount: ", activepatchingpolicy)
            servernotincmdb = []
            changescreated = []
        print(servervalidate)
        #return groupdata.status_code, transferdetails
        #finaltransferdetails = [transferdetails]
        results = {"servers_data":transferdetails}
        return results