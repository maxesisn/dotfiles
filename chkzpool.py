import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime

from global_config import mail_pass, mail_user, sender, receivers, sender_name, smtp_server
from global_config import zpool_name 

zpool_log = os.popen(f"/usr/sbin/zpool status {zpool_name}").read()
if "state: ONLINE" in zpool_log and "errors: No known data errors" in zpool_log:
    exit()

message = MIMEText(zpool_log, 'plain', 'utf-8')
message['From'] = str(Header(f"{sender_name} <{sender}>"))
message['To'] = ", ".join(receivers)

subject = f"{zpool_name} 存储池状态告警 {datetime.now().strftime('%m/%d/%Y, %H:%M')}"
message['Subject'] = Header(subject, 'utf-8')

smtpObj = smtplib.SMTP_SSL(f"{smtp_server}:465")
smtpObj.login(mail_user, mail_pass)
smtpObj.sendmail(sender, receivers, message.as_string())