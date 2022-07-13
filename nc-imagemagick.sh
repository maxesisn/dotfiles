#! /bin/bash
sudo docker exec -u 0 nextcloud_app_1 apt-get update
sudo docker exec -u 0 nextcloud_app_1 apt-get install -y imagemagick
