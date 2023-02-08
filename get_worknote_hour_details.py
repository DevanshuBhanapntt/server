#!/usr/bin/env python
# Copyright 2019 NTT Technologies
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from st2common.runners.base_action import Action
from time import strftime
import time
import datetime
import json
import subprocess
import paramiko
import os
import re
from datetime import date

class getWorkNoteDetails(Action):
    def __init__(self, config):
        """Creates a new Action given a StackStorm config object (kwargs works too)
        :param config: StackStorm configuration object for the pack
        :returns: a new Action
        """
        super(getWorkNoteDetails, self).__init__(config)

    def run(self, worknotes,state):
            
        try:          
            if(state=="-5"):
              last_update_time=work_notes_list.split('Last Update:')[1].strip()
              counter= work_notes_list.split("Attempts:")[1].split(".")[0].strip()
              current_time = time.time()                  
              datetime1 = datetime.datetime.fromtimestamp(current_time)
              datetime2= datetime.datetime.fromtimestamp(last_update_time)
              diff = datetime1 -datetime2
              diff_hour=diff.seconds//3600
              return {'last_update_time': last_update_time,'counter': counter,'diff_hour':diff_hour}                                  
        except Exception as e:
            print("An exception occurred: "+str(e))
            


