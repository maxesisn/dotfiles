import os
from datetime import datetime

from global_config import sender_pass, sender, receivers, sender_name, smtp_server
from global_config import zpool_name 
from sendmail import send_mail

zpool_log = os.popen(f"/usr/sbin/zpool status {zpool_name}").read()
if "state: ONLINE" in zpool_log and "errors: No known data errors" in zpool_log:
    exit()

subject = f"{zpool_name} 存储池状态告警 {datetime.now().strftime('%m/%d/%Y, %H:%M')}"
send_mail(subject, zpool_log)