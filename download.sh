#!/bin/bash
echo "Downloading inventory..."
python tolinoclient.py --config .tolinoclientrc inventory > inventory.txt
cat inventory.txt | grep 'id ' | cut -d: -f2 | xargs | tr ' ' ',' > allids.txt
echo "Downloading books..."
python tolinoclient.py --config .tolinoclientrc download "$(cat allids.txt)" > download.log
cat download.log

