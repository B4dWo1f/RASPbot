#!/bin/bash
BASEDIR=$(dirname "$0")

cd $BASEDIR

while ! ping -c 1 -W 1 8.8.8.8; do
    sleep 1
done

$BASEDIR/rasp.py
