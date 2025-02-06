@echo off
setlocal

:: Define variables
set APP_NAME=hw-checker-bot
set LOCAL_DB=data\database.db
set ARCHIVE_DIR=data\archived
for /f "tokens=2 delims==" %%I in ('"wmic os get localdatetime /value"') do set datetime=%%I
set TIMESTAMP=%datetime:~0,8%_%datetime:~8,6%
set BACKUP_DB=%ARCHIVE_DIR%\database_%TIMESTAMP%.db

:: Ensure archive directory exists
if not exist "%ARCHIVE_DIR%" mkdir "%ARCHIVE_DIR%"

:: Function to restore backup if interrupted
:cleanup
echo Process interrupted! Restoring the previous database...
if exist "%BACKUP_DB%" (
    move /Y "%BACKUP_DB%" "%LOCAL_DB%"
    echo Database restored.
)
echo Stopping web dyno...
heroku ps:scale web=0 --app "%APP_NAME%"
exit /b

:: Enable Ctrl+C handler
trap "call :cleanup" SIGINT

:: Start the web worker
echo Starting web dyno...
heroku ps:scale web=1 --app "%APP_NAME%"

:: Backup current database
if exist "%LOCAL_DB%" (
    echo Archiving current database...
    move /Y "%LOCAL_DB%" "%BACKUP_DB%"
)

:: Download new database from Heroku
echo Downloading database from Heroku...
heroku ps:copy /app/data/database.db --app "%APP_NAME%" --output "%LOCAL_DB%"

:: Verify success
if exist "%LOCAL_DB%" (
    echo Database successfully downloaded and replaced.
) else (
    echo Failed to download database!
    move /Y "%BACKUP_DB%" "%LOCAL_DB%"
    echo Restored previous database.
)

:: Stop the web worker
echo Stopping web dyno...
heroku ps:scale web=0 --app "%APP_NAME%"

echo Done!
exit /b
