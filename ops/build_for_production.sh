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
    python3.12 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt
