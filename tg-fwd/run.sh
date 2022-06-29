#!/usr/bin/env bash

while true
do
  date "+%D %T"
  /home/kuma/.conda/envs/bot/bin/python3 main.py > run.log 2>&1
  sleep 600
done
