@echo off
call %~dp0_env.bat

pyinstaller -F "%PYSRC_PATH%" --name "%TARGET_NAME%.exe" --distpath="%OUT_DIR%" --workpath="%OUT_DIR%/obj/pyinstaller" --specpath="%OUT_DIR%/obj/pyinstaller" --icon="%ICON_PATH%" --console --clean --noupx -y --exclude-module=numpy --exclude-module=PIL --exclude-module=numba --exclude-module=sklean --exclude-module=matplotlib --exclude-module=scipy