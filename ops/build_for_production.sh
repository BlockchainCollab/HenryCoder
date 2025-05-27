#!/bin/bash

# Run this script to build the frontend for production, node and npx required
set -e

cd frontend

npm install
npm run generate

# now the content is available under <HenryCoder>/frontend/.output/public
