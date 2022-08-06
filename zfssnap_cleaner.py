import os
import re
from datetime import datetime

from global_config import remote_folder

remote_snap_list = os.listdir(remote_folder)

counter = 0

for remote_snap in remote_snap_list:
    snap_time = re.search(r"(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})", remote_snap).group(1)
    snap_time = datetime.strptime(snap_time, "%Y-%m-%d_%H-%M-%S")
    if (datetime.now() - snap_time).days > 7:
        os.remove(os.path.join(remote_folder, remote_snap))
        counter += 1
if counter > 0:
    print(f"Removed {counter} snapshots")
        