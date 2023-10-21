@echo off
set OUTDIR=%1\convert
mkdir %OUTDIR%
for /f "delims=" %%i in ('dir /b /a:-d %1') do (
    echo %%i
    python cpcvt.py "%1\%%i" -o "%OUTDIR%\%%i" %2 %3 %4 %5 %6 %7 %8 %9
)