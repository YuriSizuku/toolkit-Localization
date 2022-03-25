@echo off
set OUTDIR=%1\convert
for /f "delims=" %%i in ('dir /b %1') do (
    echo %%i
    python ftextcvt.py "%1\%%i" -o "%1\%%~ni%2" %3 %4 %5 %6 %7 %8 %9
)