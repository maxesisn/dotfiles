#! /bin/bash
sudo docker exec -u 0 filerun_web_1 apt-get update
sudo docker exec -u 0 filerun_web_1 apt-get install -y imagemagick
