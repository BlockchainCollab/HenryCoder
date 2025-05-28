#!/bin/bash

cd backend

source .venv/bin/activate
source .env
uvicorn main:app --host $HOST --port $PORT --workers 2
