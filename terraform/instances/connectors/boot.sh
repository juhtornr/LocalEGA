#!/bin/bash

set -e

git clone -b terraform https://github.com/NBISweden/LocalEGA.git ~/repo
sudo pip3.6 install ~/repo/src

echo "Waiting for Message Broker"
until nc -4 --send-only ega-mq 5672 </dev/null &>/dev/null; do sleep 1; done
echo "Waiting for database"
until nc -4 --send-only ega-db 5432 </dev/null &>/dev/null; do sleep 1; done

systemctl start ega-connectors
systemctl enable ega-connectors

echo "LEGA ready"
