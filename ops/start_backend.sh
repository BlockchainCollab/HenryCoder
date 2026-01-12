#!/bin/bash

cd backend

source .venv/bin/activate
source .env

# Use single worker for streaming endpoints to prevent connection issues
# For scaling, use external load balancer with sticky sessions instead
uvicorn main:app --host $HOST --port $PORT --timeout-keep-alive 120
