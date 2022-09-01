#!/bin/bash

if [[ $# -eq 0 ]] ; then
    echo "update-sourcecode-from-client <host name or ip address>"
    exit 1
fi

echo "scp -r pi@$1:~/SourceCode/sensornet/client/src/* ./src/"
scp -r pi@$1:~/SourceCode/sensornet/client/src/* ./src/

echo "scp -r pi@$1:~/SourceCode/sensornet/client/config/* ./config/"
scp -r pi@$1:~/SourceCode/sensornet/client/config/* ./config/

echo "scp -r pi@$1:/etc/systemd/system/sensor-client* ./systemd/"
scp -r pi@$1:/etc/systemd/system/sensor-client* ./systemd/
