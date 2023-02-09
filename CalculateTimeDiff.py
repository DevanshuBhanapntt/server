#!/usr/bin/env python
from lib.base_action import BaseAction
from datetime import datetime
import pytz 
class CalculateTimeDiff(BaseAction):
    def __init__(self, config):
        """Creates a new Action given a StackStorm config object (kwargs works too)
        :param config: StackStorm configuration object for the pack
        :returns: a new Action
        """
        super(CalculateTimeDiff, self).__init__(config)     def run(self, task_start_date):
        #print("task_start_date: ", task_start_date)
        # 2022-10-04 22:05:23
        timesplit = task_start_date.split("-")
        time1 = timesplit[2].split(" ")[1].split(":")
        taskstarttime = datetime(int(timesplit[0]),int(timesplit[1]),int(timesplit[2].split(" ")[0]),int(time1[0]), int(time1[1]), int(time1[2]))
        #print(taskstarttime)
        #converting to GMT and substracting from current time
        #timediffGMT = (datetime.now()).astimezone(pytz.timezone('GMT')) - taskstarttime.astimezone(pytz.timezone('GMT'))
        #without converting to GMT
        gmtcurrenttime = datetime.now(pytz.timezone('GMT'))
        current_time_without_timezone = gmtcurrenttime.replace(tzinfo=None)
        timediff = current_time_without_timezone - taskstarttime
        #print("time difference in GMT: ", timediffGMT, "time difference: ", timediff)
        timediff = round((timediff.total_seconds()/3600))
        if timediff =< 24:
           return True
        else:
           return False