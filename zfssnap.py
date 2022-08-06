import os
from datetime import datetime

from global_config import datasets_to_backup, remote_folder, zpool_name

start_time = datetime.now()
for dataset in datasets_to_backup:
    time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    snapshot_str = f"{dataset}@{time_str}"
    remote_snap_path = os.path.join(remote_folder, snapshot_str)
    os.system(f"/usr/bin/sudo zfs snapshot {zpool_name}/{dataset}@{time_str}")
    os.system(f"/usr/bin/sudo zfs send -R {zpool_name}/{dataset}@{time_str} > {remote_snap_path}")
    os.system(f"/usr/bin/sudo zfs destroy {zpool_name}/{dataset}@{time_str}")

end_time = datetime.now()
print(f"Backup completed in {end_time - start_time} seconds")