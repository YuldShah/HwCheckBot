#!/bin/bash

# Define paths
APP_NAME="hw-checker-bot"
LOCAL_DB="data/database.db"
ARCHIVE_DIR="data/archived"

# Ensure archive directory exists
mkdir -p "$ARCHIVE_DIR"

# Backup current database with timestamp
echo "Current database being archived..."
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PATH_NEW="$ARCHIVE_DIR/database_$TIMESTAMP.db"
if [ -f "$LOCAL_DB" ]; then
    mv "$LOCAL_DB" "$PATH_NEW"
fi

# Download new database from Heroku
echo "Downloading database from Heroku..."
heroku ps:copy /app/data/database.db --app "$APP_NAME" --output "$LOCAL_DB"

# Verify success
if [ -f "$LOCAL_DB" ]; then
    echo "Database successfully downloaded and replaced."
else
    echo "Failed to download database!"
    mv "$PATH_NEW" "$LOCAL_DB"
    echo "Restored current datase."
fi

