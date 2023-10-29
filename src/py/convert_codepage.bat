@echo off
set OUTDIR=%1\convert
set codepage=%~dp0codepage.py
mkdir %OUTDIR%
for /f "delims=" %%i in ('dir /b /a:-d %1') do (
    echo %%i
    python %codepage% "%1\%%i" -o "%OUTDIR%\%%i" %2 %3 %4 %5 %6 %7 %8 %9
)