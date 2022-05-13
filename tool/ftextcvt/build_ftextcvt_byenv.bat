::@echo off
if not exist "%~dp0\..\..\env" (
    mkdir "%~dp0\..\..\env"
)
pushd "%~dp0\..\..\env"
python -m venv python_docx
cd .\python_docx\Scripts
python -m pip install pyinstaller
python -m pip install python-docx
call %1
popd 