#!/bin/bash

# Define variables
APP_NAME="hw-checker-bot"
LOCAL_DB="data/database.db"
ARCHIVE_DIR="data/archived"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DB="$ARCHIVE_DIR/database_$TIMESTAMP.db"

# Ensure archive directory exists
mkdir -p "$ARCHIVE_DIR"

# Function to restore backup if interrupted
cleanup() {
    echo "Process interrupted! Restoring the previous database..."
    if [ -f "$BACKUP_DB" ]; then
        mv "$BACKUP_DB" "$LOCAL_DB"
        echo "Database restored."
    fi
    echo "Stopping web dyno..."
    heroku ps:scale web=0 --app "$APP_NAME"
    exit 1
}

# Trap Ctrl+C (SIGINT) to run cleanup function
trap cleanup SIGINT

# Start the web worker
echo "Starting web dyno..."
heroku ps:scale web=1 --app "$APP_NAME"

# Backup current database
if [ -f "$LOCAL_DB" ]; then
    echo "Archiving current database..."
    mv "$LOCAL_DB" "$BACKUP_DB"
fi

# Download new database from Heroku
echo "Downloading database from Heroku..."
heroku ps:copy /app/data/database.db --app "$APP_NAME" --output "$LOCAL_DB"

# Verify success
if [ -f "$LOCAL_DB" ]; then
    echo "Database successfully downloaded and replaced."
else
    echo "Failed to download database!"
    mv "$BACKUP_DB" "$LOCAL_DB"
    echo "Restored previous database."
fi

# Stop the web worker
echo "Stopping web dyno..."
heroku ps:scale web=0 --app "$APP_NAME"

echo "Done!"
