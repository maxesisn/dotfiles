#!/usr/bin/env bash

#Change these variables!
NIC_NAME="enp4s0f0"
DOCKER_ROUTING_INTERFACE_NAME="dockerrouteif"
DOCKERNETWORK_IP_ADDRESS="192.168.2.236/32"
DOCKERNETWORK_IP_RANGE="192.168.2.64/26"

sleep 15 #Do not rush things if executing during boot. This line is not mandatory and can be removed.


ip link add ${DOCKER_ROUTING_INTERFACE_NAME} link ${NIC_NAME} type macvlan mode bridge ; ip addr add ${DOCKERNETWORK_IP_ADDRESS} dev ${DOCKER_ROUTING_INTERFACE_NAME} ; ip link set ${DOCKER_ROUTING_INTERFACE_NAME} up
ip route add ${DOCKERNETWORK_IP_RANGE} dev ${DOCKER_ROUTING_INTERFACE_NAME}
