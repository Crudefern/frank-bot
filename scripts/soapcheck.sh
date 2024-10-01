#!/bin/bash
for i in ./cleaninty/Donors/*.json; do
    string=$(cleaninty ctr LastTransfer -C "$i") 
    echo -e "----\n${i##*\/}"
    if grep -qi "Ready for transfer!" <<< "$string"; then
        echo "Ready for transfer!"
    else
        grep -i "Ready for transfer in" <<< "$string"
    fi
    done
echo "----"
