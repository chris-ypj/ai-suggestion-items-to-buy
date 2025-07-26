#!/bin/bash

# set -e: if error, exit immediately
set -e

# show commands
set -x

# make sure script is run from the directory it is located in
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Python version check
PYTHON_VERSION=$(python3 --version)
echo "current Python version: $PYTHON_VERSION"

# check python version is 3.8 or higher
if ! python3 -c 'import sys; exit(0) if sys.version_info >= (3, 8) else exit(1)'; then
    echo "error: we need Python 3.8 or latest"
    exit 1
fi

# create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "create virtul environment..."
    python3 -m venv venv
fi

# activate virtual environment
source venv/bin/activate

# upgrade pip
pip3 install --upgrade pip

# install dependencies
pip3 install pymongo fastapi uvicorn pymongo scikit-learn pandas numpy gunicorn uvloop inflect pytest pytest-asyncio requests

# start FastAPI server in a server
#gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker -D -b 0.0.0.0:9999

# # start FastAPI server locally
uvicorn main:app --reload --host 0.0.0.0 --port 9999

# close virtual environment
deactivate
