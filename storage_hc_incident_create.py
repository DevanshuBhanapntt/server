from lib.base_action import BaseAction

class StorageHcSomCreate(BaseAction):

    def __init__(self, config):
        """Creates a new Action given a StackStorm config object (kwargs works too)
        :param config: StackStorm configuration object for the pack
        :returns: a new Action
        """
        super(StorageHcSomCreate, self).__init__(config)


    def run(self,host_names_inc,company,requested_by,short_description,category,subcategory,assignment_group,impact,description):

        # REST API URL
        # endpoint = '/api/now/table/incident?sysparm_fields=number'
        # scripted/Customized API for NTT Data

        endpoint = '/api/ntt11/incident_automation_stackstorm/CreateIncident'

        # the below input fields only for Rest API
        incident=[]
        for item in host_names_inc:
            host=item.split(':',2)[0]
            ip_address=item.split(':',2)[1]
            worknotes=item.split(':',2)[2]
            payload = {
                    'company': company,
                    'requested_by': requested_by,
                    'short_description': short_description+' '+company,
                    'description': description+' '+ip_address+'. See Work Logs for details.',
                    'cmdb_ci': host,
                    'category' : category,
                    'subcategory' : subcategory,
                    'assignment_group': assignment_group,
                    'impact': impact
                }
            response = self.sn_api_call('POST', endpoint, payload=payload)
            inc_number = response['Number']
            inc_sys_id = response['SysID']
            print(inc_number)
            incident.append(response)
            w_notes="Found Error on IP"+" "+ip_address+'\n'+worknotes
            endpointurl = '/api/now/table/incident/' + inc_sys_id
            payload1 = {
                     #'assigned_to': 'Automation Service',
                     'assignment_group': assignment_group,
                     'work_notes': w_notes
             }
            inc = self.sn_api_call('PATCH', endpointurl, payload=payload1)
        return incident