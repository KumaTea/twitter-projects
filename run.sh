#!/usr/bin/env bash

set -e -x

cd /home/kuma/twi
source /home/kuma/twi/py/bin/activate

/home/kuma/twi/py/bin/python3 /home/kuma/twi/main.py > /home/kuma/twi/log.txt 2>&1 &
