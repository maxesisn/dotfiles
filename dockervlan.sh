#! /bin/bash
sudo docker network create -d macvlan --subnet=192.168.2.0/24 --gateway=192.168.2.1 --ip-range=192.168.2.64/26 -o parent=enp4s0f0 dockervlan
