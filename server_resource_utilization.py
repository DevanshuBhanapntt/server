#!/usr/bin/env python

import subprocess
import smtplib
import email.utils
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime

company = "CLARIOS"
company_abbreviation = "CLARIOS"
server_ip = "10.75.9.167"
msg_to = "BAO_Offshore_team@nttdata.com"
#msg_to = 'venkatanagababu.battina@nttdata.com'
disk_space_threshold = 70
memory_threshold_gb = 1
account_summary = "Disk utilization status  (df -h)"
main_html = ""

def check_disk_space():
    global main_html
    try:
        disk_space = subprocess.Popen(['df', '-h'], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        output = disk_space.stdout.readlines()
    except Exception as e:
        output = []
    temp_data = []
    mem_flag = False
    table_data = """<table width='75%' border=1>
                      <tr>
                        <th colspan='5' style='background-color:#800080'><font color='#FFA500'>""" + account_summary + """</font></th>
                      </tr>"""
    if output:
        for i in output:
            i = i.decode('utf-8').replace('Mounted on', 'Mounted_on')
            list_data = i.strip().split(' ')
            if isinstance(list_data, list):
                while('' in list_data):
                    list_data.remove('')
            #print("Data is: {}".format(list_data))
            list_data[0] = list_data[5]
            list_data = list_data[:-1]
            #print("All data is: {}".format(list_data))
            disk_utilization = list_data[4].replace('%', '')
            if 'Use' not in disk_utilization:
                if int(disk_utilization) >= disk_space_threshold:
                    list_data[4] = 'RED' + disk_utilization + 'RED'
                else:
                    list_data[4] = 'GREEN' + disk_utilization + 'GREEN'

            table_data += """<tr align='center'>"""
            partition_check = [i for i in list_data if 'RED' in i]
            if partition_check:
                mem_flag = True
                temp_data.append(list_data[0])
            for data in list_data:
                if 'filesystem' in data.lower() or 'size' in data.lower() or 'used' in data.lower() or 'avail' in data.lower() or 'use%' in data.lower()or 'mounted_on' in data.lower():
                    table_data += """<th style='background-color:#800080'><font color='#FFA500'>""" + data + """</th>"""
                elif 'RED' in data:
                    table_data += """<td width="20%" style="background-color:#F98B88">""" + data.replace('RED', '') + '%' + """</td>"""
                elif 'GREEN' in data:
                    table_data += """<td width="20%" style="background-color:#C3FDB8">""" + data.replace('GREEN', '') + '%' + """</td>"""
                else:
                    table_data += """<td width="20%" style="background-color:#C3FDB8">""" + data + """</td>"""
            table_data += """</tr>"""
        table_data += """</table></br>"""
    if mem_flag:
        temp_data.sort()
        disk_space_msg = ', '.join([str(item) for item in temp_data]) + " partitions utilization is greater than " + str(disk_space_threshold) + "%. Please check"
        main_html += """<p style="color:red">""" + disk_space_msg + """</p>"""
    main_html += table_data
    send_email(main_html)
    #print("HTML data is: {}".format(table_data))

def check_memory_usage():
    global main_html
    for num in range(0,2):
        if num == 0:
            size_type = '-m'
            size_value = 'MB'
        if num == 1:
            size_type = '-g'
            size_value = 'GB'
        try:
            memory_usage_mb = subprocess.Popen(['free', size_type], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            memory_output_mb = memory_usage_mb.stdout.readlines()
        except Exception as e:
            memory_output_mb = []
        mb_data = process_mem_data(memory_output_mb, size_value)
        html_data = generate_html_tags(mb_data, size_value, size_type)
        main_html += html_data
        #print("Memory {} data is: {}".format(size_value, mb_data))
        #print("HTML data is: {}".format(html_data))


def process_mem_data(mem_output, memory_size):
    cnt = 0
    temp_list = []
    if len(mem_output) == 0:
        return temp_list
    for i in mem_output:
        temp_str = ""
        mem_data = i.decode('utf-8').strip().replace('total', 'Memory_type\ttotal')
        for data in mem_data.split():
            if cnt == 0:
                temp_str += data + "***"
            if cnt >= 1:
                if data == 'Mem:' or data == 'Swap:':
                    temp_str += data + "***"
                else:
                    temp_str += data + " " + memory_size + "***"
        temp_list.append(temp_str)
        cnt += 1
    return temp_list

def generate_html_tags(text_data, size_value, size_type):
    html_data = ""
    mem_value = ''
    for j in text_data:
        if 'Swap:' in j:
            j += 'NA***NA***NA***'
        mem_data = j.split("***")
        if 'Mem:' in mem_data:
            mem_value = int(mem_data[3].replace('MB', '').replace('GB', '').strip())
            break
    if size_value == 'MB':
        threshold = memory_threshold_gb * 1024
    if size_value == 'GB':
        threshold = memory_threshold_gb
    mem_value_check = mem_value >= threshold
    if not mem_value_check:
        html_data = """<p style="color:red">* Available """ + str(mem_value) + size_value + """ memory is lessthan threshold """ + str(threshold) + size_value + """ memory. Please check.</p>"""

    html_data += """<table width='75%' border=1>
                     <tr>
                        <th colspan='7' style='background-color:#800080'><font color='#FFA500'>""" + """Memory utilization in """ + size_value + """  (free """ + size_type +""")</font></th>
                      </tr>"""
    for i in text_data:
        if 'Swap:' in i:
            i += 'NA***NA***NA***'
        list_data = i.split("***")
        while '' in list_data:
            list_data.remove('')
        html_data += """<tr align='center'>"""
        for j in list_data:
            if 'Memory_type' in j or 'total' in j or 'used' in j or 'free' in j or 'shared' in j or 'buff/cache' in j or 'available' in j:
                html_data += """<th style='background-color:#800080'><font color='#FFA500'>""" + j + """</th>"""
            else:
                html_data += """<td width="10%" style="background-color:#9AFEFF">""" + j + """</td>"""
        html_data += """</tr>"""
    html_data += """</table> <br>"""
    return html_data

def check_uptime():
    #It supports below two uptime output formats.
    #Uptime with only hours data:
    #   12:40:16 up  9:51,  2 users,  load average: 0.09, 0.10, 0.27
    #
    #Uptime with days and minutes data
    #   10:39:51 up 221 days, 18 min,  2 users,  load average: 0.03, 0.04, 0.00
    #
    #Uptime wth number of days and hours data
    #   08:24:37 up 207 days, 11:10,  0 users,  load average: 0.00, 0.03, 0.05
    item = ''
    global main_html
    try:
        uptime_cmd = subprocess.Popen(['uptime'], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        uptime_output = uptime_cmd.stdout.readlines()
    except Exception as e:
        uptime_output = []
    for item in uptime_output:
        item = item.decode('utf-8').strip()
    uptime_data = item.split('load average:')[0]
    load_avg = item.split('load average:')[1].strip()
    current_time = uptime_data.split()[0].strip()
    uptime_days = ' '.join([str(i) for i in uptime_data.split(',')[0].split()[1:]])
    if ':' in uptime_days:
        uptime_hours = uptime_days
        uptime_days = ''
        users_logged_in = uptime_data.split(',')[1].strip()
    else:
        uptime_hours = uptime_data.split(',')[1].strip()
        users_logged_in = uptime_data.split(',')[2].strip()
    if ':' not in uptime_hours:
        hours_data = '0'
        minutes_data = uptime_hours.strip().split()[0]
    else:
        hours_data = uptime_hours.split(':')[0]
        minutes_data = uptime_hours.split(':')[1]
    if uptime_days == '':
        total_uptime = hours_data.replace('up', '').strip() + " Hours, " + minutes_data + " Minutes"
    else:
        total_uptime = uptime_days.replace('up', '').strip() + ", " + hours_data + " Hours, " + minutes_data + " Minutes"

    html_str_data = ""
    if uptime_days == '' and int(hours_data.replace('up', '').strip()) <= 24:
        #html_str_data = """<marquee width="60%" direction="up" height="50px" scrollamount="1" style="color:red"><b>SERVER RESTART DETECTED. Server restarted""" + hours_data.replace('up', '').strip() + """hours back</b></marquee>"""
        html_str_data = """<p style="color:red"><b>* SERVER RESTART DETECTED. Server restarted """ + hours_data.replace('up', '').strip() + """ hours back.</b></p>"""

    one_min_load = load_avg.split(',')[0]
    five_min_load = load_avg.split(',')[1]
    fifteen_min_load = load_avg.split(',')[2]
    html_str_data += """<table width='75%' border=1>
                     <tr>
                        <th colspan='6' style='background-color:#800080'><font color='#FFA500'>""" + """Server Uptime (uptime) </font></th>
                      </tr>
                      <tr align='center'>
                        <th style='background-color:#800080'><font color='#FFA500'>Current Time</font></th>
                        <th style='background-color:#800080'><font color='#FFA500'>Server Uptime</font></th>
                        <th style='background-color:#800080'><font color='#FFA500'>Logged in Users</font></th>
                        <th style='background-color:#800080'><font color='#FFA500'>1 min load avg</font></th>
                        <th style='background-color:#800080'><font color='#FFA500'>5 min load avg</font></th>
                        <th style='background-color:#800080'><font color='#FFA500'>15 min load avg</font></th>
                      </tr>"""
    html_str_data += """<tr align='center'>
                          <td width='10%' style='background-color:#FFE4C4'>""" + current_time + """</td>
                          <td width='10%' style='background-color:#FFE4C4'>""" + total_uptime + """</td>
                          <td width='10%' style='background-color:#FFE4C4'>""" + users_logged_in + """</td>
                          <td width='10%' style='background-color:#FFE4C4'>""" + one_min_load + """</td>
                          <td width='10%' style='background-color:#FFE4C4'>""" + five_min_load + """</td>
                          <td width='10%' style='background-color:#FFE4C4'>""" + fifteen_min_load + """</td></tr>"""
    html_str_data += """</table> <br>"""
    main_html += html_str_data

def send_email(table_data):
    port = '25'
    smtp_server = 'smtp.clarios.com'
    msg_subject = company_abbreviation + '-STACKSTORM - Server Resource utilization report - ' + str(datetime.date.today())
    msg_from = 'noreply@clarios.com'
    send_mail_sts = (False, 'NONE')
    msg_body_data = "Test line 1"
    message = MIMEMultipart(msg_body_data)
    message['To'] = email.utils.formataddr(('Recipient', msg_to))
    message['From'] = email.utils.formataddr(('Stackstorm', msg_from))
    message['Subject'] = msg_subject
    html_data = """<html>
    <head>
      <style>
        table, th, td {
        border: 1px solid black;
        border-collapse: collapse;
         }
        tr, td {
            align: center;
        }
        tr:nth-child(even) {
            background-color: #E0FFFF;
        }
      </style>
    </head>
    <body>""" + table_data  + """
    </body>
    </html>"""
    msg_type = MIMEText(html_data, "html")
    message.attach(msg_type)
    try:
        server = smtplib.SMTP(smtp_server, port)
        server.set_debuglevel(False)
        server.sendmail(msg_from, [msg_to], message.as_string())
        send_mail_sts = (True, 'MAIL_SENT_SUCCESSFULLY')
        server.quit()
        #logging.info("MAIL_SENT_SUCCESSFULLY to %s at %s\n" %(msg_to, "test"))
        print("Mail sent successfully")
    except Exception as e:
        #logging.error("ERROR_SENDING_MAIL: %s" %e)
        #logging.exception("EXCEPTION WHILE SENDING MAIL", exc_info=True)
        send_mail_sts = (False, ('ERROR_SENDING_MAIL', e))
        print("ERROR_SENDING_MAIL: %s" %e)
    return send_mail_sts

if __name__ == "__main__":
    check_uptime()
    check_memory_usage()
    check_disk_space()
