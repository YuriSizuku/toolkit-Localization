@echo off
call %~dp0_env.bat

for /f "tokens=* USEBACKQ" %%f IN (`python -c "import os, docx;print(os.path.dirname(docx.__file__))"`) DO (
    set DOCX_DIR=%%f
)

nuitka --standalone --onefile --show-progress "%PYSRC_PATH%" --windows-icon-from-ico="%ICON_PATH%" --output-dir="%OUT_DIR%" -o "c%TARGET_NAME%.exe" --include-data-dir="%DOCX_DIR%\templates=docx/templates" --assume-yes-for-downloads --nofollow-import-to=numpy,PIL,numba,sklean,matplotlib,scipy