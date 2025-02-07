@echo off
setlocal enabledelayedexpansion

:: Define variables
set "APP_NAME=hw-checker-bot"
set "LOCAL_DB=data\database.db"
set "ARCHIVE_DIR=data\archived"

:: Generate timestamp (YYYYMMDD_HHMMSS)
for /f "tokens=2-4 delims=/ " %%A in ('date /t') do set "DATESTAMP=%%C%%A%%B"
for /f "tokens=1-3 delims=:. " %%A in ("%TIME%") do set "TIMESTAMP=%DATESTAMP%_%%A%%B%%C"
set "BACKUP_DB=%ARCHIVE_DIR%\database_%TIMESTAMP%.db"

:: Ensure archive directory exists
if not exist "%ARCHIVE_DIR%" mkdir "%ARCHIVE_DIR%"

:: Start the web worker
echo Starting web dyno...
heroku ps:scale web=1 --app "%APP_NAME%"
if %errorlevel% neq 0 (
    echo Error: Failed to start web dyno!
    exit /b
)

:: Wait a few seconds for dyno to start
echo Waiting for web dyno to initialize...
timeout /t 5 /nobreak >nul

:: Backup current database
if exist "%LOCAL_DB%" (
    echo Archiving current database...
    move /Y "%LOCAL_DB%" "%BACKUP_DB%" >nul
)

:: Download new database from Heroku
echo Downloading database from Heroku...
heroku ps:copy /app/data/database.db --app "%APP_NAME%" --output "%LOCAL_DB%"
if %errorlevel% neq 0 (
    echo Error: Failed to download database!
    move /Y "%BACKUP_DB%" "%LOCAL_DB%" >nul
    echo Restored previous database.
    exit /b
)

:: Verify success
if exist "%LOCAL_DB%" (
    echo Database successfully downloaded and replaced.
) else (
    echo Error: Download failed!
    move /Y "%BACKUP_DB%" "%LOCAL_DB%" >nul
    echo Restored previous database.
)

:: Stop the web worker
echo Stopping web dyno...
heroku ps:scale web=0 --app "%APP_NAME%"
if %errorlevel% neq 0 (
    echo Warning: Failed to stop web dyno!
)

echo Done!
exit /b
