#!/bin/sh

python CreateConfigFile.py

echo "Starting $*..."


exec "$@"