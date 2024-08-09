#!/usr/bin/env bash

set -e -x

cd /home/kuma/twi
source /home/kuma/twi/py/bin/activate

MAX_TRIES=5
attempt=0

while [ $attempt -lt $MAX_TRIES ]; do
  /home/kuma/twi/py/bin/python3 /home/kuma/twi/src/query.py && break || {
    echo "Command failed, attempt $((++attempt)). Retrying in 1 minute..."
    sleep 60
  }
done

if [ $attempt -eq $MAX_TRIES ]; then
  /usr/bin/notify "twi info error!"
fi

