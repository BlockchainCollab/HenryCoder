#!/bin/bash

# Run this script to build the frontend for production, node and npx required
set -e

cd frontend

npm install
npm run generate

# now the content is available under <HenryCoder>/frontend/.output/public

echo "Building the backend..."

# build the backend
cd ../backend

# if the .venv directory does not exist, create it
if [ ! -d ".venv" ]; then
    # Prefer python3.13 if available, otherwise fall back to python3.12
    if command -v python3.13 >/dev/null 2>&1; then
        python3.13 -m venv .venv
    elif command -v python3.12 >/dev/null 2>&1; then
        python3.12 -m venv .venv
    else
        echo "Error: neither python3.13 nor python3.12 is available." >&2
        exit 1
    fi
fi
source .venv/bin/activate
pip install -r requirements.txt
