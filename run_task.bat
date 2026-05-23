@echo off
setlocal enabledelayedexpansion

REM Change directory to the location of this batch script
cd /d "%~dp0"

REM Load environment variables from .env file, ignoring empty lines and comments
if exist .env (
    for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do (
        if not "%%B"=="" (
            set "%%A=%%B"
        )
    )
)

REM Create logs directory if it doesn't exist
if not exist logs (
    mkdir logs
)

REM Run the python script and redirect all output to a log file
(
    echo.
    echo ========================================================
    echo Starting IT Job Market Brief Pipeline at %date% %time%
    call myvenv\Scripts\python.exe run.py
    echo Script finished with ERRORLEVEL !ERRORLEVEL! at %date% %time%
    echo ========================================================
) >> logs\pipeline.log 2>&1

exit /b !ERRORLEVEL!
