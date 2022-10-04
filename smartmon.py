import os
import re
from datetime import datetime

from global_config import zpool_name
from sendmail import send_mail

disk_pattern = re.compile(r"^(?!wwn)(?!nvme-eui).*")
disk_list = os.listdir("/dev/disk/by-id")

indep_disk_list = [disk for disk in disk_list if disk_pattern.match(
    disk) and "part" not in disk]

smart_info = str()
new_infomsg = list()
keyword_list = ["ATTRIBUTE_NAME", "Model", "Serial", "Firmware", "result:", "Reallocated", "Spin_Retry", "Temperature_Celsius", 
                "Current_Pending_Sector", "Offline_Uncorrectable", "Extended offline", "Percentage Used", "Power On Hours", "Power_On_Hours", "Integrity Errors"]
for disk in indep_disk_list:
    infomsg = os.popen("/usr/sbin/smartctl -a /dev/disk/by-id/"+disk).read()
    infomsg = infomsg.splitlines()
    for infoline in infomsg:
        if any(word in infoline for word in keyword_list):
            new_infomsg.append(infoline)
    new_infomsg.append("\n")

new_infomsg = "\n".join(new_infomsg)

zpool_list = os.popen(f"/usr/sbin/zpool list").read()

new_infomsg += "\n\n" + zpool_list

zpool_log = os.popen(f"/usr/sbin/zpool status {zpool_name}").read()

new_infomsg += "\n\n" + zpool_log

subject = f"S.M.A.R.T每周检查报告 {datetime.now().strftime('%m/%d/%Y, %H:%M')}"

send_mail(subject, new_infomsg)
