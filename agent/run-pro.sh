#!/bin/bash
export PYTHONPATH="/home/ruser/containerguard-pro:$PYTHONPATH"
cd /home/ruser/containerguard-pro
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi
source venv/bin/activate
exec python agent/runner.py
