#!/bin/bash
uname -a
uptime -p
pingstring=$(ping -c 4 -i 0.2 github.com)
echo -e "--- g${pingstring##*'--- g'}"
