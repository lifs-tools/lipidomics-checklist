#!/bin/bash

# Check if db/checklist.sqlite exists
if [ ! -f db/checklist.sqlite ]; then
    # If it doesn't exist, create the database
    cp db/checklist.sqlite.template db/checklist.sqlite
fi

# Check if db/ChecklistConfig.py exists
if [ ! -f db/ChecklistConfig.py ]; then
    # If it doesn't exist, create the configuration file
    cp db/ChecklistConfig.py.template db/ChecklistConfig.py
    # replace encryption_key = "..." with a random string
    sed -i '' "s/encryption_key = \"...\"/encryption_key = \"$(openssl rand -base64 32)\"/g" db/ChecklistConfig.py
fi
# Install dependencies, create a virtual environment
python3 -m venv .venv
# Install the virtual environment
source .venv/bin/activate
# Install the dependencies
pip install -r requirements.txt
echo "Starting the application..."
# Run the application with docker compose
docker compose up --build --no-recreate --watch
