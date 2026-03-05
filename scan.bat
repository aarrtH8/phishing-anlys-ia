@echo off
SETLOCAL

IF "%~1"=="" (
    ECHO Usage: scan.bat [URL]
    EXIT /B 1
)

:: Forward to PowerShell script
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scan.ps1" "%~1" %2 %3 %4 %5 %6 %7 %8 %9

ENDLOCAL
