import subprocess
import smtplib
import email.utils
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
from email.mime.application import MIMEApplication
from os.path import basename

company = "Moodys"
company_abbreviation = "Moodys"
server_ip = "10.124.128.161"
msg_to = 'BAO_Offshore_team@nttdata.com'

def health_check():
    services_list = ['st2actionrunner','st2api', 'st2stream', 'st2auth', 'st2notifier', 'st2rulesengine', 'st2sensorcontainer']
    account_summary = company + " - Health Check - " + str(datetime.date.today()) + "\n"
    #print(account_summary)
    email_array=[]

    email_array.append(account_summary)
    #Server Timestamp Details
    #print("--------------------Server Timestamp--------------------")
    email_array.append("--------------------Server Timestamp--------------------\n")
    try:
        server_timestamp = subprocess.Popen(['timedatectl'], stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
        server_timestamp_output = server_timestamp.stdout.readlines()
    except Exception as e:
        server_timestamp_output = "Command Execution Failed: "+str(e)
    
    email_array.append("".join(server_timestamp_output))

    try:
        #Check Mongo DB Status
        #print("--------------------Mongo DB Status--------------------")
        email_array.append("\n--------------------Mongo DB Status--------------------\n")
        mongod_status = subprocess.Popen(['systemctl', 'status', 'mongod'], stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
        mongod_status_output = mongod_status.stdout.readlines()

    except Exception as e:
        mongod_status_output = "Command Execution Failed: "+str(e)
        
    email_array.append("".join(mongod_status_output))
    
    try:
        #Check ST2 Status
        #print("--------------------ST2 Status--------------------")
        email_array.append("\n--------------------ST2 Status--------------------\n")
        st2_status = subprocess.Popen(['st2ctl', 'status'], stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
        st2_status_output = st2_status.stdout.readlines()

    except Exception as e:
        st2_status_output = "Command Execution Failed: "+str(e)
        
    email_array.append("".join(st2_status_output)) 


    #Check Disk Status
    #print("--------------------Disk Status--------------------")
    email_array.append("\n--------------------Disk Status--------------------\n")
    try:
        disk_status = subprocess.Popen(['df', '-h'], stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
        disk_status_output = disk_status.stdout.readlines()
    except Exception as e:
        disk_status_output = "Command Execution Failed: "+str(e)
        
    email_array.append("".join(disk_status_output))


    # Check St2 Sensor Log Status
    #print("--------------------Check Sensor Log--------------------")
    email_array.append("\n--------------------Check Sensor Log--------------------\n")
    try:
        sensor_status = subprocess.Popen(['tail', '-50' , '/var/log/st2/st2sensorcontainer.log'], stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
        sensor_status_output = sensor_status.stdout.readlines()
    except Exception as e:
        sensor_status_output = "Command Execution Failed: "+str(e)  
        
    email_array.append("".join(sensor_status_output))


    #Check services status
    services_flag = []
    for i in services_list:
        #print("--------------------Check"+" Service "+ i +"--------------------")
        email_array.append("\n--------------------Check"+" Service "+ i +"--------------------\n")
        try:
            service_status = subprocess.Popen(['systemctl', 'status' , i], stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
            service_status_output = service_status.stdout.readlines()
        except Exception as e:
            sensor_status_output = "Command Execution Failed: "+str(e)    
            
        email_array.append("".join(service_status_output))


    #Check execution status
    #print("--------------------Check Stackstorm Execution Status--------------------")
    email_array.append("\n--------------------Check Stackstorm Execution Status--------------------\n")
    try:
        execution_status = subprocess.Popen(['st2', 'execution' , 'list', '-n' , '5'], stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
        execution_status_output = execution_status.stdout.readlines()
    except Exception as e:
        sensor_status_output = "Command Execution Failed: "+str(e) 
        
    email_array.append("".join(execution_status_output))


    file_path= '/opt/scripts/'+'healthcheck_report.txt'
    file = open(file_path,"w")
    file.write(''.join(email_array))
    file.close()

    send_email(file_path)

def send_email(file_path):
    port = '25'
    smtp_server = '155.16.123.161'
    msg_subject = company_abbreviation + '-STACKSTORM - Health Check Report - ' + str(datetime.date.today())
    msg_from = 'noreply@nttdata.com'
    send_mail_sts = (False, 'NONE')
    msg_body_data = "HealthCheck Report"
    message = MIMEMultipart(msg_body_data)
    msg_to = 'BAO_Offshore_team@nttdata.com'
    #msg_to = msg_to.split(';')
    message['To'] = email.utils.formataddr(('Recipient',msg_to))
    message['From'] = email.utils.formataddr(('Stackstorm', msg_from))
    message['Subject'] = msg_subject
    msg_body = "Please find attached Health Check Report"
    part2 = MIMEText(msg_body, "plain")
    message.attach(part2)

    with open(file_path, "rb") as fil:
        part = MIMEApplication(
            fil.read(),
            Name=basename(file_path)
        )

    part['Content-Disposition'] = 'attachment; filename="%s"' % basename(file_path)
    message.attach(part)

    server = smtplib.SMTP(smtp_server, port)
    server.set_debuglevel(False)
    try:
        server.sendmail(msg_from, msg_to , message.as_string())
        send_mail_sts = (True, 'MAIL_SENT_SUCCESSFULLY')
    except Exception as e:
        send_mail_sts = (False, ('ERROR_SENDING_MAIL', e))
    finally:
        server.quit()
    print(send_mail_sts)

if __name__ == "__main__":
    health_check()
