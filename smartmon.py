from dis import dis
from distutils.log import info
import os
import re
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime

from global_config import sender_pass, sender, receivers, sender_name, smtp_server
from global_config import zpool_name

disk_pattern = re.compile(r"^(?!wwn)(?!nvme-eui).*")
disk_list = os.listdir("/dev/disk/by-id")

indep_disk_list = [disk for disk in disk_list if disk_pattern.match(
    disk) and "part" not in disk]

smart_info = str()
new_infomsg = list()
keyword_list = ["Model", "Serial", "Firmware", "result:", "Reallocated", "Spin_Retry",
                "Current_Pending_Sector", "Offline_Uncorrectable", "Extended offline", "Percentage Used", "Power On Hours", "Power_On_Hours", "Integrity Errors"]
for disk in indep_disk_list:
    infomsg = os.popen("/usr/sbin/smartctl -a /dev/disk/by-id/"+disk).read()
    infomsg = infomsg.splitlines()
    for infoline in infomsg:
        if any(word in infoline for word in keyword_list):
            new_infomsg.append(infoline)
    new_infomsg.append("\n")

new_infomsg = "\n".join(new_infomsg)

zpool_log = os.popen(f"/usr/sbin/zpool status {zpool_name}").read()

new_infomsg += "\n\n" + zpool_log

message = MIMEText(new_infomsg, 'plain', 'utf-8')
message['From'] = str(Header(f"{sender_name} <{sender}>"))
message['To'] = ", ".join(receivers)

subject = f"S.M.A.R.T每周检查报告 {datetime.now().strftime('%m/%d/%Y, %H:%M')}"
message['Subject'] = Header(subject, 'utf-8')

smtpObj = smtplib.SMTP_SSL(f"{smtp_server}:465")
smtpObj.login(sender, sender_pass)
smtpObj.sendmail(sender, receivers, message.as_string())