@echo off
call %~dp0_env.bat

nuitka --standalone --onefile --show-progress "%PYSRC_PATH%" --windows-icon-from-ico="%ICON_PATH%" --output-dir="%OUT_DIR%" -o "c%TARGET_NAME%.exe" --assume-yes-for-downloads --nofollow-import-to=numpy,PIL,numba,sklean,matplotlib,scipy