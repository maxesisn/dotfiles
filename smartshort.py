import os
import re
from time import sleep

disk_pattern = re.compile(r"^(?!wwn)(?!nvme-eui).*")
disk_list = os.listdir("/dev/disk/by-id")

indep_disk_list = [disk for disk in disk_list if disk_pattern.match(
    disk) and "part" not in disk]

for disk in indep_disk_list:
    os.system("/usr/sbin/smartctl -t short /dev/disk/by-id/"+disk)
    sleep(120)
    
