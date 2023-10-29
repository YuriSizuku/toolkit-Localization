:: build by pyinstaller
call %~dp0_env.bat
python -m pip install pyinstaller
pyinstaller -F "%PYSRC_PATH%" --name "%TARGET_NAME%.exe" --distpath="%OUT_DIR%" --workpath="%OUT_DIR%/obj/pyinstaller" --specpath="%OUT_DIR%/obj/pyinstaller" --icon="%ICON_PATH%" --exclude-module=numpy --exclude-module=PIL --console --clean --noupx -y