#!/bin/bash

# brew install iproute2mac for mac

#got ipv4 ip
# ip=$(ifconfig en0 | grep inet | awk '{print $2}')


ipv4=$(ip addr show|grep -A1 'inet [^f:]'|sed -nr 's#^ +inet ([0-9.]+)/[0-9]+ brd [0-9./]+ scope global .*#\1#p')
ipv6=$(ip -6 address show | grep inet6 | awk '{print $2}' | cut -d'/' -f1);

echo "ipv4: $ipv4"
echo "ipv6: $ipv6"
time=$(date +%Y-%m-%d-%H-%M-%S)
content="time:$time \nipv4: $ipv4\nipv6: $ipv6"
sh post.sh "IP UPDATED.." "$content"