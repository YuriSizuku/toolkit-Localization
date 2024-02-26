@echo off
call %~dp0_env.bat

python -m pip install nuitka
nuitka --standalone --onefile --full-compat --show-progress "%PYSRC_PATH%" --windows-icon-from-ico="%ICON_PATH%" --output-dir="%OUT_DIR%" -o "c%TARGET_NAME%.exe" --assume-yes-for-downloads